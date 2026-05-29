"""
Rutas para gestión de archivos descargados
"""

import os
import io
import zipfile
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.core.security import verify_api_key
from app.models.db_models import APIKey
from app.models.schemas import FileInfo, FileListResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/api", tags=["Descargas y Archivos"])


@router.get("/listar-archivos/{task_id}")
async def listar_archivos(
    task_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    📋 Lista todos los archivos descargados de una tarea.

    Esta ruta permite obtener un listado completo de todos los archivos que fueron 
    descargados para una tarea específica, incluyendo su nombre, tamaño y tipo.

    **Autenticación**: Requiere API Key válida en header X-API-Key

    **Parámetros de path:**
    - `task_id`: ID único de la tarea

    **Respuesta exitosa (200):**
    ```json
    {
      "task_id": "uuid-de-la-tarea",
      "archivos": [
        {
          "nombre": "documento_001.pdf",
          "tamaño_kb": 245.6,
          "tipo": "PDF"
        },
        {
          "nombre": "documento_002.xml",
          "tamaño_kb": 12.3,
          "tipo": "XML"
        }
      ],
      "total": 2
    }
    ```

    **Errores posibles:**
    - 401: No autorizado (API Key inválida)
    - 404: Tarea no encontrada
    - 404: Carpeta de descarga no existe
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
    ⬇️ Descarga un archivo específico de una tarea.

    Permite descargar un archivo individual previamente descargado de la DIAN. 
    El servidor detecta automáticamente el tipo de archivo (PDF, XML, ZIP, etc.) 
    y establece el Content-Type correcto.

    **Autenticación**: Requiere API Key válida en header X-API-Key

    **Parámetros de path:**
    - `task_id`: ID único de la tarea
    - `nombre_archivo`: Nombre exacto del archivo a descargar

    **Respuesta exitosa (200):**
    - Retorna el archivo binario con el Content-Type y filename correctos

    **Ejemplo de uso:**
    ```bash
    curl -H "X-API-Key: tu-api-key" \
      -O http://localhost:8000/api/descargar-archivo/task-uuid/documento_001.pdf
    ```

    **Errores posibles:**
    - 400: La tarea no tiene archivos descargados aún
    - 401: No autorizado (API Key inválida)
    - 404: Tarea no encontrada
    - 404: Archivo no encontrado en la tarea
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
    📂 Lista archivos de una tarea con opción de filtrar por tipo.

    Obtiene un listado de archivos de una tarea con la capacidad de filtrar 
    por tipo específico (ZIP, PDF, XML, etc.). Útil para obtener información 
    antes de hacer descargas masivas.

    **Autenticación**: Requiere API Key válida en header X-API-Key

    **Parámetros de path:**
    - `task_id`: ID único de la tarea

    **Parámetros de query:**
    - `tipo` (opcional): Filtrar por tipo de archivo (zip, pdf, xml)
      - Ejemplos: `tipo=pdf`, `tipo=xml`, `tipo=zip`

    **Respuesta exitosa (200):**
    ```json
    {
      "task_id": "uuid-de-la-tarea",
      "filtro_tipo": "pdf",
      "archivos": [
        {
          "nombre": "documento_001.pdf",
          "tamaño_kb": 245.6,
          "tipo": "PDF"
        }
      ],
      "total": 1
    }
    ```

    **Ejemplo de uso:**
    ```bash
    # Obtener todos los archivos PDF
    curl -H "X-API-Key: tu-api-key" \
      http://localhost:8000/api/descargar-todos/task-uuid?tipo=pdf
    ```

    **Errores posibles:**
    - 401: No autorizado (API Key inválida)
    - 404: Tarea no encontrada
    - 404: Carpeta de descarga no existe
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


@router.get("/descargar-todos-comprimido/{task_id}")
async def descargar_todos_comprimido(
    task_id: str,
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: zip, pdf, xml"),
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    🗜️ Descarga todos los archivos de una tarea en un único archivo ZIP.

    Comprime todos los archivos de una tarea en un archivo ZIP en memoria 
    y lo retorna como descarga. Soporta filtrado por tipo de archivo para 
    descargar solo ciertos tipos (PDFs, XMLs, etc.).

    **Autenticación**: Requiere API Key válida en header X-API-Key

    **Parámetros de path:**
    - `task_id`: ID único de la tarea

    **Parámetros de query:**
    - `tipo` (opcional): Filtrar por tipo de archivo (zip, pdf, xml)
      - Ejemplos: `tipo=pdf` (solo PDFs), `tipo=xml` (solo XMLs)
      - Sin parámetro: incluye todos los archivos

    **Respuesta exitosa (200):**
    - Retorna archivo ZIP con todos los archivos comprimidos
    - El nombre del archivo es: `tarea_XXXXXXXX_YYYYMMDD_HHMMSS.zip`
    - Content-Type: `application/zip`

    **Ejemplo de uso:**
    ```bash
    # Descargar todos los archivos en ZIP
    curl -H "X-API-Key: tu-api-key" \
      -O http://localhost:8000/api/descargar-todos-comprimido/task-uuid

    # Descargar solo PDFs en ZIP
    curl -H "X-API-Key: tu-api-key" \
      -O "http://localhost:8000/api/descargar-todos-comprimido/task-uuid?tipo=pdf"
    ```

    **Errores posibles:**
    - 400: La tarea no tiene archivos descargados o carpeta no existe
    - 401: No autorizado (API Key inválida)
    - 404: Tarea no encontrada
    - 404: No hay archivos del tipo solicitado en la tarea
    - 500: Error al comprimir archivos
    """
    # Verificar que existe la tarea
    try:
        task = await TaskService.get_task(db, task_id)
    except HTTPException as e:
        logger.error(f"Tarea no encontrada: {task_id}")
        raise

    download_folder = await TaskService.get_task_folder(db, task_id)

    if not download_folder:
        logger.warning(f"Tarea {task_id} no tiene carpeta de descarga asignada")
        raise HTTPException(
            status_code=400, detail="La tarea aún no tiene archivos descargados"
        )

    if not os.path.exists(download_folder):
        logger.warning(f"Carpeta no existe: {download_folder}")
        raise HTTPException(
            status_code=404, detail="La carpeta de descargas no existe"
        )

    # Obtener lista de archivos
    archivos_a_comprimir = []
    try:
        archivos_en_carpeta = os.listdir(download_folder)
        logger.info(f"Archivos en carpeta {download_folder}: {archivos_en_carpeta}")
        
        for archivo in archivos_en_carpeta:
            filepath = os.path.join(download_folder, archivo)
            if os.path.isfile(filepath):
                extension = archivo.split(".")[-1].lower()

                # Filtrar por tipo si se especificó
                if tipo and extension != tipo.lower():
                    logger.debug(f"Saltando archivo (tipo no coincide): {archivo} ({extension} != {tipo})")
                    continue

                archivos_a_comprimir.append((archivo, filepath))
                logger.debug(f"Agregando archivo a comprimir: {archivo}")
    except Exception as e:
        logger.error(f"Error al listar archivos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al leer carpeta: {str(e)}")

    if not archivos_a_comprimir:
        logger.warning(f"No hay archivos{f' de tipo {tipo}' if tipo else ''} en tarea {task_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No hay archivos{f' de tipo {tipo}' if tipo else ''} en esta tarea",
        )

    logger.info(
        f"Comprimiendo {len(archivos_a_comprimir)} archivos para tarea {task_id}"
    )

    # Crear archivo ZIP en memoria
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for nombre_archivo, filepath in archivos_a_comprimir:
            try:
                # Agregar archivo al ZIP
                zip_file.write(filepath, arcname=nombre_archivo)
                logger.debug(f"Archivo agregado al ZIP: {nombre_archivo}")
            except Exception as e:
                logger.error(f"Error al agregar archivo al ZIP: {nombre_archivo} - {e}")
                raise HTTPException(status_code=500, detail=f"Error al comprimir archivo: {str(e)}")

    zip_buffer.seek(0)

    # Generar nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tarea_{task_id[:8]}_{timestamp}.zip"

    logger.info(f"Archivo comprimido creado: {filename} con {len(archivos_a_comprimir)} archivos")

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
