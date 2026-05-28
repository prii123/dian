"""
Servicio para gestión de API Keys
"""

import uuid
from datetime import datetime
from typing import List, Optional

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.db_models import APIKey
from app.models.schemas import ApiKeyCreate, ApiKeyInfo, ApiKeyResponse


class ApiKeyService:
    """Servicio para gestionar API Keys de autenticación"""

    @staticmethod
    def generate_api_key() -> str:
        """
        Genera una API Key aleatoria segura

        Returns:
            API Key en formato UUID sin guiones (32 caracteres hexadecimales)
        """
        # Generar UUID aleatorio y quitar guiones
        return uuid.uuid4().hex

    @staticmethod
    def hash_key(api_key: str) -> str:
        """
        Hashea una API Key usando bcrypt

        Args:
            api_key: API Key en texto plano

        Returns:
            Hash de la API Key
        """
        return bcrypt.hash(api_key)

    @staticmethod
    def verify_key(plain_key: str, hashed_key: str) -> bool:
        """
        Verifica si una API Key coincide con su hash

        Args:
            plain_key: API Key en texto plano
            hashed_key: Hash almacenado

        Returns:
            True si coincide, False en caso contrario
        """
        try:
            return bcrypt.verify(plain_key, hashed_key)
        except Exception as e:
            logger.error(f"Error al verificar API key: {e}")
            return False

    @staticmethod
    async def create_api_key(db: AsyncSession, request: ApiKeyCreate) -> ApiKeyResponse:
        """
        Crea una nueva API Key

        Args:
            db: Sesión de base de datos
            request: Datos de creación

        Returns:
            ApiKeyResponse con la key generada
        """
        # Generar API key única
        api_key_plain = ApiKeyService.generate_api_key()
        api_key_hash = ApiKeyService.hash_key(api_key_plain)

        # Parsear fecha de expiración si existe
        expires_at = None
        if request.expires_at:
            try:
                expires_at = datetime.fromisoformat(request.expires_at)
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {request.expires_at}")

        # Crear registro en base de datos
        db_key = APIKey(
            id=str(uuid.uuid4()),
            key_hash=api_key_hash,
            name=request.name,
            description=request.description,
            is_active=True,
            expires_at=expires_at,
            request_count=0,
        )

        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)

        logger.info(f"✅ API Key creada: {db_key.id} - {request.name}")

        # Retornar con la key en texto plano (solo esta vez)
        return ApiKeyResponse(
            id=db_key.id,
            key=api_key_plain,  # ⚠️ Solo se muestra al crear
            name=db_key.name,
            description=db_key.description,
            is_active=db_key.is_active,
            created_at=db_key.created_at.isoformat(),
            expires_at=db_key.expires_at.isoformat() if db_key.expires_at else None,
        )

    @staticmethod
    async def validate_api_key(db: AsyncSession, api_key: str) -> Optional[APIKey]:
        """
        Valida una API Key y retorna el registro si es válida

        Args:
            db: Sesión de base de datos
            api_key: API Key en texto plano

        Returns:
            APIKey si es válida, None si no
        """
        # Obtener todas las API keys activas
        result = await db.execute(select(APIKey).where(APIKey.is_active))
        api_keys = result.scalars().all()

        # Verificar contra cada hash
        for db_key in api_keys:
            if ApiKeyService.verify_key(api_key, db_key.key_hash):
                # Verificar expiración
                if db_key.expires_at and datetime.now() > db_key.expires_at:
                    logger.warning(f"⚠️ API Key expirada: {db_key.id}")
                    return None

                # Actualizar última uso y contador
                db_key.last_used_at = datetime.now()
                db_key.request_count += 1
                await db.commit()

                return db_key

        return None

    @staticmethod
    async def get_all_keys(db: AsyncSession) -> List[ApiKeyInfo]:
        """
        Obtiene todas las API Keys (sin mostrar las keys)

        Args:
            db: Sesión de base de datos

        Returns:
            Lista de ApiKeyInfo
        """
        result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        db_keys = result.scalars().all()

        return [
            ApiKeyInfo(
                id=key.id,
                name=key.name,
                description=key.description,
                is_active=key.is_active,
                created_at=key.created_at.isoformat(),
                updated_at=key.updated_at.isoformat(),
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                request_count=key.request_count,
            )
            for key in db_keys
        ]

    @staticmethod
    async def get_key_by_id(db: AsyncSession, key_id: str) -> Optional[ApiKeyInfo]:
        """
        Obtiene una API Key por su ID

        Args:
            db: Sesión de base de datos
            key_id: ID de la API Key

        Returns:
            ApiKeyInfo si existe, None si no
        """
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        db_key = result.scalar_one_or_none()

        if not db_key:
            return None

        return ApiKeyInfo(
            id=db_key.id,
            name=db_key.name,
            description=db_key.description,
            is_active=db_key.is_active,
            created_at=db_key.created_at.isoformat(),
            updated_at=db_key.updated_at.isoformat(),
            expires_at=db_key.expires_at.isoformat() if db_key.expires_at else None,
            last_used_at=db_key.last_used_at.isoformat()
            if db_key.last_used_at
            else None,
            request_count=db_key.request_count,
        )

    @staticmethod
    async def revoke_key(db: AsyncSession, key_id: str) -> bool:
        """
        Revoca (desactiva) una API Key

        Args:
            db: Sesión de base de datos
            key_id: ID de la API Key a revocar

        Returns:
            True si se revocó, False si no existe
        """
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        db_key = result.scalar_one_or_none()

        if not db_key:
            return False

        db_key.is_active = False
        await db.commit()

        logger.info(f"🔒 API Key revocada: {key_id} - {db_key.name}")
        return True

    @staticmethod
    async def update_key(
        db: AsyncSession,
        key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ApiKeyInfo]:
        """
        Actualiza una API Key

        Args:
            db: Sesión de base de datos
            key_id: ID de la API Key
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            is_active: Nuevo estado (opcional)

        Returns:
            ApiKeyInfo actualizada o None si no existe
        """
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        db_key = result.scalar_one_or_none()

        if not db_key:
            return None

        # Actualizar campos
        if name is not None:
            db_key.name = name
        if description is not None:
            db_key.description = description
        if is_active is not None:
            db_key.is_active = is_active

        await db.commit()
        await db.refresh(db_key)

        logger.info(f"✏️ API Key actualizada: {key_id}")

        return ApiKeyInfo(
            id=db_key.id,
            name=db_key.name,
            description=db_key.description,
            is_active=db_key.is_active,
            created_at=db_key.created_at.isoformat(),
            updated_at=db_key.updated_at.isoformat(),
            expires_at=db_key.expires_at.isoformat() if db_key.expires_at else None,
            last_used_at=db_key.last_used_at.isoformat()
            if db_key.last_used_at
            else None,
            request_count=db_key.request_count,
        )
