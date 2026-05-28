"""
Middleware y funciones de seguridad para autenticación
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.models.db_models import APIKey
from app.services.apikey_service import ApiKeyService


async def get_api_key_from_header(
    x_api_key: Optional[str] = Header(None, alias=settings.API_KEY_HEADER_NAME),
) -> str:
    """
    Extrae la API Key del header

    Args:
        x_api_key: API Key desde el header

    Returns:
        API Key

    Raises:
        HTTPException: Si no se proporciona API Key
    """
    if not x_api_key:
        logger.warning("❌ Intento de acceso sin API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerida. Incluye el header 'X-API-Key' en tu request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


async def verify_api_key(
    api_key: str = Depends(get_api_key_from_header), db: AsyncSession = Depends(get_db)
) -> APIKey:
    """
    Dependency para verificar API Key en endpoints protegidos

    Uso en endpoints:
        @app.get("/protected")
        async def protected_endpoint(
            api_key_info: APIKey = Depends(verify_api_key)
        ):
            # Endpoint protegido
            ...

    Args:
        api_key: API Key desde el header
        db: Sesión de base de datos

    Returns:
        APIKey validada

    Raises:
        HTTPException: Si la API Key es inválida
    """
    if not settings.API_KEY_ENABLED:
        # Si la autenticación está deshabilitada, retornar None
        # (útil para desarrollo/testing)
        logger.warning("⚠️ Autenticación deshabilitada - modo desarrollo")
        return None

    # Validar API Key
    db_key = await ApiKeyService.validate_api_key(db, api_key)

    if not db_key:
        logger.warning(f"❌ API Key inválida o expirada: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida, expirada o revocada",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info(f"✅ Acceso autorizado - API Key: {db_key.id} ({db_key.name})")
    return db_key


async def verify_master_key(api_key: str = Depends(get_api_key_from_header)) -> bool:
    """
    Dependency para verificar Master API Key (solo para endpoints de administración)

    Uso en endpoints admin:
        @app.post("/admin/api-keys")
        async def create_key(
            _: bool = Depends(verify_master_key),
            ...
        ):
            # Solo accesible con Master Key
            ...

    Args:
        api_key: API Key desde el header

    Returns:
        True si es válida

    Raises:
        HTTPException: Si no es la Master Key
    """
    if api_key != settings.MASTER_API_KEY:
        logger.warning("❌ Intento de acceso admin con clave inválida")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere Master API Key para esta operación.",
        )

    logger.info("✅ Acceso admin autorizado con Master Key")
    return True


# Dependency opcional: permitir acceso sin API key (para endpoints públicos)
async def optional_api_key(
    x_api_key: Optional[str] = Header(None, alias=settings.API_KEY_HEADER_NAME),
    db: AsyncSession = Depends(get_db),
) -> Optional[APIKey]:
    """
    Dependency opcional que permite acceso con o sin API Key
    Útil para endpoints que quieres trackear pero no forzar autenticación

    Args:
        x_api_key: API Key opcional desde el header
        db: Sesión de base de datos

    Returns:
        APIKey si es válida, None si no se proporciona
    """
    if not x_api_key:
        return None

    return await ApiKeyService.validate_api_key(db, x_api_key)
