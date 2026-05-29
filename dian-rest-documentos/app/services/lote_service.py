"""
Servicio para gestion de lotes de CUFE
"""

import uuid
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.db_models import Lote, LoteDetalle
from app.models.schemas import (
    LoteDetalleInfo,
    LoteDetalleListResponse,
    LoteListResponse,
    LoteStatus,
    LoteUploadResponse,
)


class LoteService:

    COLUMNAS_CUFE = ["cufe", "CUFE", "Cufe", "documento_id", "DocumentoID", "num_documento"]

    @staticmethod
    async def count_running_lotes(db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).select_from(Lote).where(Lote.status == "running")
        )
        count = result.scalar()
        return count or 0

    @staticmethod
    async def parse_excel_cufes(file: UploadFile, columna: Optional[str] = None) -> List[str]:
        import openpyxl

        contents = await file.read()
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise HTTPException(status_code=400, detail="El archivo Excel esta vacio")

        header = [str(c).strip() if c else "" for c in rows[0]]
        col_idx = None

        if columna:
            for i, h in enumerate(header):
                if h.strip().lower() == columna.strip().lower():
                    col_idx = i
                    break
            if col_idx is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columna '{columna}' no encontrada en el Excel. Columnas detectadas: {header}",
                )
        else:
            for i, h in enumerate(header):
                if h.strip() in LoteService.COLUMNAS_CUFE:
                    col_idx = i
                    break
            if col_idx is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se detecto columna de CUFE. Columnas disponibles: {header}. Use el parametro 'columna' para especificar el nombre.",
                )

        cufes = []
        for row in rows[1:]:
            if not row or len(row) <= col_idx:
                continue
            val = row[col_idx]
            if val is not None:
                val_str = str(val).strip()
                if val_str:
                    cufes.append(val_str)

        if not cufes:
            raise HTTPException(status_code=400, detail="No se encontraron CUFE en la columna especificada")

        return cufes

    @staticmethod
    async def create_lote(
        db: AsyncSession,
        file: UploadFile,
        token_url: str,
        fecha_inicio: Optional[str],
        fecha_fin: Optional[str],
        api_key_id: Optional[str],
        columna: Optional[str] = None,
    ) -> LoteUploadResponse:
        if settings.MAX_CONCURRENT_TASKS > 0:
            running = await LoteService.count_running_lotes(db)
            if running >= settings.MAX_CONCURRENT_TASKS:
                raise HTTPException(
                    status_code=429,
                    detail=f"Limite de tareas concurrentes alcanzado ({settings.MAX_CONCURRENT_TASKS})",
                )

        cufes = await LoteService.parse_excel_cufes(file, columna)
        cufes = list(dict.fromkeys(cufes))

        lote_id = str(uuid.uuid4())
        lote = Lote(
            id=lote_id,
            status="pending",
            filename=file.filename or "sin_nombre.xlsx",
            token_url=token_url,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_cufes=len(cufes),
            progress=0.0,
            mensaje=f"Lote creado con {len(cufes)} CUFE pendientes",
            api_key_id=api_key_id,
        )
        db.add(lote)

        for cufe in cufes:
            detalle = LoteDetalle(
                id=str(uuid.uuid4()),
                lote_id=lote_id,
                cufe=cufe,
                status="pending",
            )
            db.add(detalle)

        await db.commit()
        await db.refresh(lote)

        logger.info(f"Lote creado: {lote_id} - {len(cufes)} CUFE - Archivo: {file.filename}")

        return LoteUploadResponse(
            lote_id=lote_id,
            filename=file.filename or "sin_nombre.xlsx",
            total_cufes=len(cufes),
            mensaje=f"Lote creado con {len(cufes)} CUFE pendientes",
            status="pending",
        )

    @staticmethod
    async def get_lote(db: AsyncSession, lote_id: str) -> LoteStatus:
        result = await db.execute(select(Lote).where(Lote.id == lote_id))
        lote = result.scalar_one_or_none()
        if not lote:
            raise HTTPException(status_code=404, detail="Lote no encontrado")

        return LoteStatus(
            lote_id=lote.id,
            filename=lote.filename,
            status=lote.status,
            total_cufes=lote.total_cufes,
            descargados=lote.descargados,
            fallidos=lote.fallidos,
            no_encontrados=lote.no_encontrados,
            progress=lote.progress,
            mensaje=lote.mensaje,
            download_folder=lote.download_folder,
            created_at=lote.created_at.isoformat(),
            updated_at=lote.updated_at.isoformat(),
            completed_at=lote.completed_at.isoformat() if lote.completed_at else None,
        )

    @staticmethod
    async def get_lotes_by_api_key(db: AsyncSession, api_key_id: str) -> LoteListResponse:
        result = await db.execute(
            select(Lote)
            .where(Lote.api_key_id == api_key_id)
            .order_by(Lote.created_at.desc())
        )
        lotes = result.scalars().all()

        lote_statuses = [
            LoteStatus(
                lote_id=lote.id,
                filename=lote.filename,
                status=lote.status,
                total_cufes=lote.total_cufes,
                descargados=lote.descargados,
                fallidos=lote.fallidos,
                no_encontrados=lote.no_encontrados,
                progress=lote.progress,
                mensaje=lote.mensaje,
                download_folder=lote.download_folder,
                created_at=lote.created_at.isoformat(),
                updated_at=lote.updated_at.isoformat(),
                completed_at=lote.completed_at.isoformat() if lote.completed_at else None,
            )
            for lote in lotes
        ]

        return LoteListResponse(total=len(lote_statuses), lotes=lote_statuses)

    @staticmethod
    async def update_lote(db: AsyncSession, lote_id: str, updates: dict) -> None:
        result = await db.execute(select(Lote).where(Lote.id == lote_id))
        lote = result.scalar_one_or_none()
        if not lote:
            logger.error(f"Intento de actualizar lote inexistente: {lote_id}")
            return

        for key, value in updates.items():
            if hasattr(lote, key):
                setattr(lote, key, value)

        if updates.get("status") in ["completed", "failed", "partial"] and lote.completed_at is None:
            lote.completed_at = datetime.now()

        await db.commit()

    @staticmethod
    async def get_lote_detalles(db: AsyncSession, lote_id: str) -> LoteDetalleListResponse:
        lote_result = await db.execute(select(Lote).where(Lote.id == lote_id))
        lote = lote_result.scalar_one_or_none()
        if not lote:
            raise HTTPException(status_code=404, detail="Lote no encontrado")

        detalle_result = await db.execute(
            select(LoteDetalle).where(LoteDetalle.lote_id == lote_id).order_by(LoteDetalle.created_at)
        )
        detalles = detalle_result.scalars().all()

        pendientes = sum(1 for d in detalles if d.status == "pending")
        descargados_count = sum(1 for d in detalles if d.status == "downloaded")
        fallidos_count = sum(1 for d in detalles if d.status == "failed")
        no_encontrados_count = sum(1 for d in detalles if d.status == "not_found")

        detalles_info = [
            LoteDetalleInfo(
                id=d.id,
                cufe=d.cufe,
                status=d.status,
                download_path=d.download_path,
                mensaje=d.mensaje,
                intentos=d.intentos,
                ultimo_intento=d.ultimo_intento.isoformat() if d.ultimo_intento else None,
            )
            for d in detalles
        ]

        return LoteDetalleListResponse(
            lote_id=lote_id,
            detalles=detalles_info,
            total=len(detalles_info),
            pendientes=pendientes,
            descargados=descargados_count,
            fallidos=fallidos_count,
            no_encontrados=no_encontrados_count,
        )

    @staticmethod
    async def get_pending_cufes(db: AsyncSession, lote_id: str) -> List[LoteDetalle]:
        result = await db.execute(
            select(LoteDetalle).where(
                LoteDetalle.lote_id == lote_id,
                LoteDetalle.status.in_(["pending", "failed"]),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_detalle(db: AsyncSession, detalle_id: str, updates: dict) -> None:
        result = await db.execute(select(LoteDetalle).where(LoteDetalle.id == detalle_id))
        detalle = result.scalar_one_or_none()
        if not detalle:
            return

        for key, value in updates.items():
            if hasattr(detalle, key):
                setattr(detalle, key, value)

        await db.commit()

    @staticmethod
    async def recalculate_lote_counts(db: AsyncSession, lote_id: str) -> None:
        result = await db.execute(select(Lote).where(Lote.id == lote_id))
        lote = result.scalar_one_or_none()
        if not lote:
            return

        detalles_result = await db.execute(
            select(LoteDetalle).where(LoteDetalle.lote_id == lote_id)
        )
        detalles = detalles_result.scalars().all()

        total = len(detalles)
        if total == 0:
            return

        descargados = sum(1 for d in detalles if d.status == "downloaded")
        fallidos = sum(1 for d in detalles if d.status == "failed")
        no_encontrados = sum(1 for d in detalles if d.status == "not_found")
        progress = ((descargados + fallidos + no_encontrados) / total) * 100.0

        lote.descargados = descargados
        lote.fallidos = fallidos
        lote.no_encontrados = no_encontrados
        lote.progress = min(progress, 100.0)

        procesados = descargados + fallidos + no_encontrados
        if procesados >= total:
            if fallidos > 0 or no_encontrados > 0:
                lote.status = "partial"
                lote.mensaje = f"Lote completado parcialmente: {descargados} descargados, {fallidos} fallidos, {no_encontrados} no encontrados"
            else:
                lote.status = "completed"
                lote.mensaje = f"Lote completado: {descargados} CUFE descargados exitosamente"
            if lote.completed_at is None:
                lote.completed_at = datetime.now()

        await db.commit()

    @staticmethod
    async def get_lote_token_url(db: AsyncSession, lote_id: str) -> Optional[str]:
        result = await db.execute(
            select(Lote.token_url).where(Lote.id == lote_id)
        )
        token = result.scalar_one_or_none()
        return token

    @staticmethod
    async def update_lote_token(db: AsyncSession, lote_id: str, new_token_url: str) -> None:
        result = await db.execute(select(Lote).where(Lote.id == lote_id))
        lote = result.scalar_one_or_none()
        if not lote:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        if lote.status in ["running"]:
            raise HTTPException(status_code=400, detail="El lote esta en ejecucion, espera a que termine")
        lote.token_url = new_token_url
        await db.commit()

    @staticmethod
    async def get_lote_folder(db: AsyncSession, lote_id: str) -> Optional[str]:
        result = await db.execute(
            select(Lote.download_folder).where(Lote.id == lote_id)
        )
        folder = result.scalar_one_or_none()
        return folder
