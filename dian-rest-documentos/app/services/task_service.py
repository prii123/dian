"""
Servicio para gestión de tareas
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.db_models import Task
from app.models.schemas import TaskRequest, TaskStatus, TaskListResponse


class TaskService:
    """Servicio para gestionar tareas de descarga"""

    @staticmethod
    async def create_task(
        db: AsyncSession, request: TaskRequest, api_key_id: Optional[str] = None
    ) -> str:
        """
        Crear una nueva tarea de descarga

        Args:
            db: Sesión de base de datos
            request: Datos de la petición
            api_key_id: ID de la API Key que crea la tarea (opcional)

        Returns:
            ID de la tarea creada

        Raises:
            HTTPException: Si se alcanza el límite de tareas concurrentes
        """
        # Verificar límite de tareas concurrentes
        if settings.MAX_CONCURRENT_TASKS > 0:
            running_tasks = await TaskService.count_running_tasks(db)
            if running_tasks >= settings.MAX_CONCURRENT_TASKS:
                logger.warning(
                    f"Límite de tareas concurrentes alcanzado: {running_tasks}/{settings.MAX_CONCURRENT_TASKS}"
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite de tareas concurrentes alcanzado ({settings.MAX_CONCURRENT_TASKS}). Espera a que termine alguna tarea.",
                )

        # Generar ID único
        task_id = str(uuid.uuid4())

        # Crear registro de tarea
        task = Task(
            id=task_id,
            status="pending",
            progress=0.0,
            total_documentos=0,
            descargados=0,
            pagina_actual=0,
            mensaje="Tarea creada, esperando inicio...",
            token_url=request.token_url,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            api_key_id=api_key_id,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(
            f"Tarea creada: {task_id} - Fechas: {request.fecha_inicio} a {request.fecha_fin}"
        )

        return task_id

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> TaskStatus:
        """
        Obtener el estado de una tarea

        Args:
            db: Sesión de base de datos
            task_id: ID de la tarea

        Returns:
            Estado de la tarea

        Raises:
            HTTPException: Si la tarea no existe
        """
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(f"Tarea no encontrada: {task_id}")
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        return TaskStatus(
            task_id=task.id,
            status=task.status,
            progress=task.progress,
            total_documentos=task.total_documentos,
            descargados=task.descargados,
            pagina_actual=task.pagina_actual,
            mensaje=task.mensaje,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            download_folder=task.download_folder,
            fecha_inicio=task.fecha_inicio,
            fecha_fin=task.fecha_fin,
        )

    @staticmethod
    async def update_task(db: AsyncSession, task_id: str, updates: dict) -> None:
        """
        Actualizar el estado de una tarea

        Args:
            db: Sesión de base de datos
            task_id: ID de la tarea
            updates: Datos a actualizar
        """
        # Verificar que la tarea existe
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            logger.error(f"Intento de actualizar tarea inexistente: {task_id}")
            return

        # Actualizar campos
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # Marcar completed_at si la tarea se completa o falla
        if (
            updates.get("status") in ["completed", "failed"]
            and task.completed_at is None
        ):
            task.completed_at = datetime.now()

        await db.commit()

        # Log de actualizaciones importantes
        if "status" in updates:
            logger.info(f"Tarea {task_id}: Estado actualizado a '{updates['status']}'")
        if "progress" in updates and updates.get("status") == "running":
            logger.debug(f"Tarea {task_id}: Progreso {updates['progress']:.1f}%")

    @staticmethod
    async def get_task_folder(db: AsyncSession, task_id: str) -> Optional[str]:
        """
        Obtener la carpeta de descargas de una tarea

        Args:
            db: Sesión de base de datos
            task_id: ID de la tarea

        Returns:
            Ruta de la carpeta o None
        """
        result = await db.execute(
            select(Task.download_folder).where(Task.id == task_id)
        )
        folder = result.scalar_one_or_none()
        return folder

    @staticmethod
    async def count_running_tasks(db: AsyncSession) -> int:
        """Contar tareas en ejecución"""
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.status == "running")
        )
        count = result.scalar()
        return count or 0

    @staticmethod
    async def get_tasks_by_api_key(db: AsyncSession, api_key_id: str) -> TaskListResponse:
        """
        Obtener todas las tareas asociadas a un API Key

        Args:
            db: Sesión de base de datos
            api_key_id: ID del API Key

        Returns:
            Lista de tareas del API Key ordenadas por fecha de creación (más recientes primero)
        """
        # Consultar tareas ordenadas por fecha de creación descendente
        result = await db.execute(
            select(Task)
            .where(Task.api_key_id == api_key_id)
            .order_by(Task.created_at.desc())
        )
        tasks = result.scalars().all()

        # Convertir a TaskStatus
        task_statuses = [
            TaskStatus(
                task_id=task.id,
                status=task.status,
                progress=task.progress,
                total_documentos=task.total_documentos,
                descargados=task.descargados,
                pagina_actual=task.pagina_actual,
                mensaje=task.mensaje,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                download_folder=task.download_folder,
                fecha_inicio=task.fecha_inicio,
                fecha_fin=task.fecha_fin,
            )
            for task in tasks
        ]

        logger.info(f"Obtenidas {len(task_statuses)} tareas para API Key {api_key_id}")

        return TaskListResponse(total=len(task_statuses), tareas=task_statuses)
