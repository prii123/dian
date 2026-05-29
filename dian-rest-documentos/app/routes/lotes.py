"""
Rutas para gestion de lotes de CUFE
"""

import os
import io
import zipfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.core.security import verify_api_key
from app.models.db_models import APIKey
from app.models.schemas import (
    LoteDetalleListResponse,
    LoteListResponse,
    LoteReanudarTokenRequest,
    LoteStatus,
    LoteUploadResponse,
)
from app.services.dian_service import DianService
from app.services.lote_service import LoteService

router = APIRouter(prefix="/api/lotes", tags=["Lotes CUFE"])


@router.post("/upload", response_model=LoteUploadResponse)
async def upload_lote(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo Excel (.xlsx) con columna de CUFE"),
    token_url: str = Form(..., description="URL completa con el token de autenticacion de DIAN"),
    fecha_inicio: Optional[str] = Form(None, description="Fecha inicio en formato DD-MM-YYYY"),
    fecha_fin: Optional[str] = Form(None, description="Fecha fin en formato DD-MM-YYYY"),
    columna: Optional[str] = Form(None, description="Nombre de la columna que contiene los CUFE (autodetecta si no se especifica)"),
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube un archivo Excel con CUFE y crea un lote de procesamiento.

    Requiere API Key valida en header X-API-Key.

    - **file**: Archivo Excel (.xlsx) que contiene una columna con los CUFE
    - **token_url**: URL completa con el token de autenticacion de DIAN
    - **fecha_inicio**: Fecha inicio opcional para acotar la busqueda (DD-MM-YYYY)
    - **fecha_fin**: Fecha fin opcional para acotar la busqueda (DD-MM-YYYY)
    - **columna**: Nombre de la columna de CUFE (se autodetecta si no se especifica)

    Retorna el ID del lote para hacer seguimiento.
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx o .xls)")

    response = await LoteService.create_lote(
        db, file, token_url, fecha_inicio, fecha_fin, str(api_key.id), columna
    )

    background_tasks.add_task(DianService.descargar_por_cufes, response.lote_id)

    return response


@router.get("", response_model=LoteListResponse)
async def listar_lotes(
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todos los lotes asociados al API Key del usuario.

    Requiere API Key valida en header X-API-Key.

    Retorna lista de lotes ordenados por fecha de creacion (mas recientes primero).
    """
    return await LoteService.get_lotes_by_api_key(db, str(api_key.id))


@router.get("/{lote_id}", response_model=LoteStatus)
async def estado_lote(
    lote_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Consulta el estado y progreso de un lote de CUFE.

    Requiere API Key valida en header X-API-Key.

    - **lote_id**: ID del lote retornado al subir el archivo
    """
    return await LoteService.get_lote(db, lote_id)


@router.get("/{lote_id}/detalles", response_model=LoteDetalleListResponse)
async def detalles_lote(
    lote_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene el detalle CUFE por CUFE de un lote, con su estado individual.

    Requiere API Key valida en header X-API-Key.

    - **lote_id**: ID del lote
    """
    return await LoteService.get_lote_detalles(db, lote_id)


@router.post("/{lote_id}/reanudar", response_model=LoteStatus)
async def reanudar_lote(
    lote_id: str,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Reanuda un lote que fallo o fue interrumpido.
    Solo procesa los CUFE que estan en estado 'pending' o 'failed'.
    Los CUFE ya descargados ('downloaded') se omiten.

    Requiere API Key valida en header X-API-Key.

    - **lote_id**: ID del lote a reanudar
    """
    lote = await LoteService.get_lote(db, lote_id)
    if lote.status in ["running"]:
        raise HTTPException(status_code=400, detail="El lote ya esta en ejecucion")

    if lote.status == "completed":
        raise HTTPException(status_code=400, detail="El lote ya fue completado exitosamente")

    pending = await LoteService.get_pending_cufes(db, lote_id)
    if not pending:
        raise HTTPException(status_code=400, detail="No hay CUFE pendientes o fallidos para reanudar")

    await LoteService.update_lote(
        db, lote_id,
        {
            "status": "pending",
            "mensaje": f"Reanudando lote con {len(pending)} CUFE pendientes/fallidos",
            "completed_at": None,
        },
    )

    background_tasks.add_task(DianService.descargar_por_cufes, lote_id)

    return await LoteService.get_lote(db, lote_id)


@router.post("/{lote_id}/reanudar-con-token", response_model=LoteStatus)
async def reanudar_lote_con_token(
    lote_id: str,
    body: LoteReanudarTokenRequest,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza el token_url del lote y reanuda el procesamiento.
    Util cuando el token anterior expiro y la busqueda fallo.
    Solo procesa CUFE pendientes o fallidos, no los ya descargados.

    Requiere API Key valida en header X-API-Key.

    - **lote_id**: ID del lote a reanudar
    - **token_url**: Nuevo token de autenticacion DIAN
    """
    await LoteService.update_lote_token(db, lote_id, body.token_url)

    pending = await LoteService.get_pending_cufes(db, lote_id)
    if not pending:
        raise HTTPException(status_code=400, detail="No hay CUFE pendientes o fallidos para reanudar")

    await LoteService.update_lote(
        db, lote_id,
        {
            "status": "pending",
            "mensaje": f"Reanudando lote con nuevo token - {len(pending)} CUFE pendientes/fallidos",
            "completed_at": None,
        },
    )

    background_tasks.add_task(DianService.descargar_por_cufes, lote_id)

    return await LoteService.get_lote(db, lote_id)


@router.get("/{lote_id}/descargar-comprimido")
async def descargar_lote_comprimido(
    lote_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Descarga todos los archivos ZIP del lote en un unico archivo comprimido.

    Requiere API Key valida en header X-API-Key.

    - **lote_id**: ID del lote
    """
    await LoteService.get_lote(db, lote_id)

    download_folder = await LoteService.get_lote_folder(db, lote_id)

    if not download_folder:
        raise HTTPException(status_code=400, detail="El lote aun no tiene archivos descargados")

    if not os.path.exists(download_folder):
        raise HTTPException(status_code=404, detail="La carpeta de descargas no existe")

    archivos_a_comprimir = []
    for archivo in os.listdir(download_folder):
        filepath = os.path.join(download_folder, archivo)
        if os.path.isfile(filepath):
            archivos_a_comprimir.append((archivo, filepath))

    if not archivos_a_comprimir:
        raise HTTPException(status_code=404, detail="No hay archivos descargados en este lote")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for nombre_archivo, filepath in archivos_a_comprimir:
            zip_file.write(filepath, arcname=nombre_archivo)

    zip_buffer.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lote_{lote_id[:8]}_{timestamp}.zip"

    logger.info(f"Archivo comprimido creado: {filename} con {len(archivos_a_comprimir)} archivos")

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
