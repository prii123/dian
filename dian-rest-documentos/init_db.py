#!/usr/bin/env python3
"""
Script para inicializar la base de datos y crear todas las tablas
"""

import asyncio
import sys
from pathlib import Path

# Agregar la carpeta del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import close_database, init_database
from app.core.logger import logger


async def main():
    """Función principal"""
    try:
        logger.info("=" * 60)
        logger.info("🗄️  INICIALIZANDO BASE DE DATOS")
        logger.info("=" * 60)
        logger.info(f"Base de datos: {settings.DB_HOST}:{settings.DB_PORT}")
        logger.info(f"Nombre: {settings.DB_NAME}")
        logger.info(f"Usuario: {settings.DB_USER}")
        logger.info("=" * 60)

        # Inicializar base de datos
        await init_database()

        logger.info("=" * 60)
        logger.info("✅ Base de datos inicializada exitosamente")
        logger.info("=" * 60)
        logger.info("\nTablas creadas:")
        logger.info("  • api_keys - Para autenticación con API Keys")
        logger.info("  • tasks - Para gestionar tareas de descarga")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Error al inicializar base de datos: {e}")
        logger.error("=" * 60)
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
