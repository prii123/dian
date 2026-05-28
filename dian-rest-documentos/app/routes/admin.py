"""
Rutas de administración de API Keys
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_master_key
from app.models.schemas import (
    ApiKeyCreate,
    ApiKeyInfo,
    ApiKeyListResponse,
    ApiKeyResponse,
    ApiKeyUpdate,
)
from app.services.apikey_service import ApiKeyService

router = APIRouter(
    prefix="/admin/api-keys",
    tags=["Admin - API Keys"],
    dependencies=[
        Depends(verify_master_key)
    ],  # Todos los endpoints requieren Master Key
)


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(request: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    """
    Crear una nueva API Key

    **⚠️ IMPORTANTE**: La API Key se muestra solo una vez al crearla.
    Guárdala en un lugar seguro.

    **Requiere**: Master API Key en header X-API-Key

    - **name**: Nombre descriptivo del cliente
    - **description**: Descripción opcional
    - **expires_at**: Fecha de expiración (ISO format) - opcional

    Retorna la API Key generada (solo visible al crear).
    """
    api_key = await ApiKeyService.create_api_key(db, request)
    return api_key


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    """
    Listar todas las API Keys

    **Requiere**: Master API Key en header X-API-Key

    Retorna lista de todas las API Keys (sin mostrar las keys).
    Incluye información de uso y estado.
    """
    keys = await ApiKeyService.get_all_keys(db)
    return ApiKeyListResponse(total=len(keys), keys=keys)


@router.get("/{key_id}", response_model=ApiKeyInfo)
async def get_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """
    Obtener detalles de una API Key específica

    **Requiere**: Master API Key en header X-API-Key

    - **key_id**: ID de la API Key

    Retorna información detallada (sin mostrar la key).
    """
    key_info = await ApiKeyService.get_key_by_id(db, key_id)

    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key con ID {key_id} no encontrada",
        )

    return key_info


@router.patch("/{key_id}", response_model=ApiKeyInfo)
async def update_api_key(
    key_id: str, request: ApiKeyUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Actualizar una API Key

    **Requiere**: Master API Key en header X-API-Key

    - **key_id**: ID de la API Key
    - **name**: Nuevo nombre (opcional)
    - **description**: Nueva descripción (opcional)
    - **is_active**: Activar/desactivar (opcional)

    Permite actualizar nombre, descripción y estado (activa/inactiva).
    """
    updated_key = await ApiKeyService.update_key(
        db,
        key_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active,
    )

    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key con ID {key_id} no encontrada",
        )

    return updated_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """
    Revocar (desactivar) una API Key

    **Requiere**: Master API Key en header X-API-Key

    - **key_id**: ID de la API Key a revocar

    La API Key se desactiva permanentemente y no podrá usarse más.
    Esta operación no puede deshacerse (aunque puedes reactivarla con PATCH).
    """
    success = await ApiKeyService.revoke_key(db, key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key con ID {key_id} no encontrada",
        )

    return None  # 204 No Content
