"""
Rutas para gestión de tareas de descarga
"""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.db_models import APIKey
from app.models.schemas import TaskCreateResponse, TaskRequest, TaskStatus
from app.services.dian_service import DianService
from app.services.task_service import TaskService

router = APIRouter(prefix="/api", tags=["Tareas"])


@router.post("/iniciar-descarga", response_model=TaskCreateResponse)
async def iniciar_descarga(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia una tarea de descarga de documentos de la DIAN.

    **Requiere**: API Key válida en header X-API-Key

    - **token_url**: URL completa con el token de autenticación
    - **fecha_inicio**: Fecha inicio en formato DD-MM-YYYY
    - **fecha_fin**: Fecha fin en formato DD-MM-YYYY

    Retorna el ID de la tarea para hacer seguimiento.
    """
    # Crear tarea
    task_id = await TaskService.create_task(db, request, api_key_id=str(api_key.id))

    # Programar descarga en background
    background_tasks.add_task(
        DianService.descargar_documentos,
        task_id,
        request.token_url,
        request.fecha_inicio,
        request.fecha_fin,
    )

    return TaskCreateResponse(
        task_id=task_id, mensaje="Tarea iniciada exitosamente", status="pending"
    )


@router.get("/estado-tarea/{task_id}", response_model=TaskStatus)
async def estado_tarea(
    task_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Consulta el estado y progreso de una tarea de descarga.

    **Requiere**: API Key válida en header X-API-Key

    - **task_id**: ID de la tarea retornado al iniciar la descarga

    Retorna información detallada del estado, progreso y archivos descargados.
    """
    return await TaskService.get_task(db, task_id)
