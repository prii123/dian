"""
Rutas de health check y estado del servicio
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import HealthResponse
from app.services.task_service import TaskService
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "servicio": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "descripcion": settings.APP_DESCRIPTION,
        "endpoints": {
            "iniciar_descarga": "POST /api/iniciar-descarga",
            "estado_tarea": "GET /api/estado-tarea/{task_id}",
            "listar_archivos": "GET /api/listar-archivos/{task_id}",
            "descargar_archivo": "GET /api/descargar-archivo/{task_id}/{nombre_archivo}",
            "descargar_todos": "GET /api/descargar-todos/{task_id}?tipo=zip",
            "documentacion": "GET /docs",
            "health": "GET /health"
        }
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        tareas_activas=await TaskService.count_running_tasks(db),
        version=settings.APP_VERSION
    )
