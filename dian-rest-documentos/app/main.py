"""
Aplicación principal FastAPI
"""

import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.core.database import init_database, close_database
from app.routes import files, health, tasks, admin

# Fix para Windows: Playwright requiere WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def create_app() -> FastAPI:
    """Factory para crear la aplicación FastAPI"""

    # Descripción extendida para Swagger
    description = """
    ## 📄 Servicio REST para descarga automatizada de documentos DIAN
    
    Este servicio permite automatizar la descarga de documentos desde el portal de la DIAN 
    utilizando tokens de autenticación y rangos de fechas.
    
    ### Características principales:
    
    * **Descarga automatizada**: Descarga documentos por rango de fechas
    * **Gestión de tareas**: Sistema de tareas asíncronas con seguimiento en tiempo real
    * **Gestión de archivos**: Lista, descarga individual o descarga masiva en ZIP
    * **Navegador automatizado**: Utiliza Playwright para la automatización
    
    ### Flujo de uso:
    
    1. **Iniciar descarga**: POST `/api/iniciar-descarga` con token_url y fechas
    2. **Consultar estado**: GET `/api/estado-tarea/{task_id}` para ver el progreso
    3. **Listar archivos**: GET `/api/listar-archivos/{task_id}` cuando se complete
    4. **Descargar**: GET `/api/descargar-archivo/{task_id}/{nombre}` o `/api/descargar-todos/{task_id}`
    """

    # Metadatos de tags para organizar los endpoints
    tags_metadata = [
        {
            "name": "Health",
            "description": "Endpoints de verificación de estado del servicio y información general.",
        },
        {
            "name": "Tareas",
            "description": "Gestión de tareas de descarga: iniciar, consultar estado, listar tareas por usuario. **Requiere API Key**.",
        },
        {
            "name": "Descargas y Archivos",
            "description": "Gestión de archivos descargados: listar, descargar individual, descargar múltiples en ZIP. **Requiere API Key**.",
        },
        {
            "name": "Admin - API Keys",
            "description": "Administración de API Keys. **Requiere Master API Key**.",
        },
    ]

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=tags_metadata,
        contact={
            "name": "DIAN Document Service",
            "url": "https://github.com/tu-usuario/dian-rest-documentos",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(admin.router)  # Rutas de administración
    # Registrar routers
    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(files.router)

    # Event handlers
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Sistema operativo: {sys.platform}")
        if sys.platform == "win32":
            logger.info(
                "Event Loop Policy: WindowsSelectorEventLoopPolicy (requerido para Playwright)"
            )
        logger.info(f"Carpeta de descargas: {settings.DOWNLOAD_BASE_FOLDER}")
        logger.info(f"Modo headless: {settings.BROWSER_HEADLESS}")
        
        # Inicializar base de datos
        logger.info("🗄️ Inicializando base de datos PostgreSQL...")
        try:
            await init_database()
            logger.info(f"✅ Base de datos conectada: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Error al conectar a base de datos: {e}")
            logger.warning("⚠️ El servicio continuará pero sin autenticación de API Keys")
        
        # Información de seguridad
        if settings.API_KEY_ENABLED:
            logger.info("🔐 Autenticación de API Keys: HABILITADA")
            logger.info(f"📋 Header de API Key: {settings.API_KEY_HEADER_NAME}")
        else:
            logger.warning("⚠️ Autenticación de API Keys: DESHABILITADA (solo para desarrollo)")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"Deteniendo {settings.APP_NAME}")
        await close_database()
        logger.info(f"Deteniendo {settings.APP_NAME}")

    return app


# Crear instancia de la aplicación
app = create_app()
