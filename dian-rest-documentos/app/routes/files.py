"""
Rutas para gestión de archivos descargados
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.core.security import verify_api_key
from app.models.db_models import APIKey
from app.models.schemas import FileInfo, FileListResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/api", tags=["Archivos"])


@router.get("/listar-archivos/{task_id}")
async def listar_archivos(
    task_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todos los archivos descargados para una tarea específica.

    **Requiere**: API Key válida en header X-API-Key

    - **task_id**: ID de la tarea

    Retorna lista de archivos con sus nombres y rutas.
    """
    # Verificar que existe la tarea
    await TaskService.get_task(db, task_id)  # Lanza HTTPException si no existe

    download_folder = await TaskService.get_task_folder(db, task_id)

    if not download_folder or not os.path.exists(download_folder):
        return {"task_id": task_id, "archivos": [], "total": 0}

    archivos = []
    for archivo in os.listdir(download_folder):
        filepath = os.path.join(download_folder, archivo)
        if os.path.isfile(filepath):
            archivos.append(
                FileInfo(
                    nombre=archivo,
                    tamaño_kb=round(os.path.getsize(filepath) / 1024, 2),
                    tipo=archivo.split(".")[-1].upper(),
                )
            )

    return {"task_id": task_id, "archivos": archivos, "total": len(archivos)}


@router.get("/descargar-archivo/{task_id}/{nombre_archivo}")
async def descargar_archivo(
    task_id: str,
    nombre_archivo: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Descarga un archivo específico de una tarea.

    **Requiere**: API Key válida en header X-API-Key

    - **task_id**: ID de la tarea
    - **nombre_archivo**: Nombre del archivo a descargar

    Retorna el archivo solicitado (ZIP, PDF, XML, etc.).
    """
    # Verificar que existe la tarea
    await TaskService.get_task(db, task_id)

    download_folder = await TaskService.get_task_folder(db, task_id)

    if not download_folder:
        raise HTTPException(
            status_code=400, detail="La tarea aún no tiene archivos descargados"
        )

    filepath = os.path.join(download_folder, nombre_archivo)

    if not os.path.exists(filepath):
        logger.warning(f"Archivo no encontrado: {filepath}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Determinar tipo de archivo
    if nombre_archivo.endswith(".zip"):
        media_type = "application/zip"
    elif nombre_archivo.endswith(".pdf"):
        media_type = "application/pdf"
    elif nombre_archivo.endswith(".xml"):
        media_type = "application/xml"
    else:
        media_type = "application/octet-stream"

    return FileResponse(filepath, media_type=media_type, filename=nombre_archivo)


@router.get("/descargar-todos/{task_id}", response_model=FileListResponse)
async def descargar_todos(
    task_id: str,
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: zip, pdf, xml"),
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista archivos de una tarea con opción de filtrar por tipo.

    **Requiere**: API Key válida en header X-API-Key.

    - **task_id**: ID de la tarea
    - **tipo**: (Opcional) Filtrar por tipo de archivo (zip, pdf, xml)
    """
    # Verificar que existe la tarea
    await TaskService.get_task(db, task_id)

    download_folder = await TaskService.get_task_folder(db, task_id)

    if not download_folder or not os.path.exists(download_folder):
        return FileListResponse(task_id=task_id, filtro_tipo=tipo, archivos=[], total=0)

    archivos = []
    for archivo in os.listdir(download_folder):
        filepath = os.path.join(download_folder, archivo)
        if os.path.isfile(filepath):
            extension = archivo.split(".")[-1].lower()

            # Filtrar por tipo si se especificó
            if tipo and extension != tipo.lower():
                continue

            archivos.append(
                FileInfo(
                    nombre=archivo,
                    tamaño_kb=round(os.path.getsize(filepath) / 1024, 2),
                    tipo=extension.upper(),
                )
            )

    return FileListResponse(
        task_id=task_id, filtro_tipo=tipo, archivos=archivos, total=len(archivos)
    )
