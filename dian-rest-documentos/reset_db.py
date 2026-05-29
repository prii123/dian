#!/usr/bin/env python3
"""
Script para limpiar y reinicializar la base de datos
"""

import asyncio
import sys
from pathlib import Path

# Agregar la carpeta del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import close_database, engine
from app.core.logger import logger
from app.models.db_models import Base
from sqlalchemy import text


async def main():
    """Función principal"""
    try:
        logger.info("=" * 60)
        logger.info("🗑️  LIMPIANDO BASE DE DATOS")
        logger.info("=" * 60)
        logger.info(f"Base de datos: {settings.DB_HOST}:{settings.DB_PORT}")
        logger.info(f"Nombre: {settings.DB_NAME}")
        logger.info("=" * 60)

        # Eliminar todas las tablas (con CASCADE para dependencias)
        async with engine.begin() as conn:
            # Usar raw SQL con CASCADE para manejar dependencias
            await conn.execute(text("DROP TABLE IF EXISTS deepseek_processing_results CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS tasks CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS api_keys CASCADE"))
        logger.info("✅ Tablas eliminadas")

        logger.info("=" * 60)
        logger.info("🔄 REINICIALIZANDO BASE DE DATOS")
        logger.info("=" * 60)

        # Crear todas las tablas nuevamente
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("=" * 60)
        logger.info("✅ Base de datos reinicializada exitosamente")
        logger.info("=" * 60)
        logger.info("\nTablas creadas:")
        logger.info("  • api_keys - Para autenticación con API Keys")
        logger.info("  • tasks - Para gestionar tareas de descarga")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Error al reinicializar base de datos: {e}")
        logger.error("=" * 60)
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
