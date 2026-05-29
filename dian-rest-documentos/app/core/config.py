"""
Configuración centralizada del servicio DIAN REST API
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Información de la aplicación
    APP_NAME: str = "DIAN Document Service"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Servicio REST para automatizar la descarga de documentos de la DIAN"
    )

    # Configuración del servidor
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False

    # Configuración de descarga
    DOWNLOAD_BASE_FOLDER: str = "./descargas"

    # Configuración de Playwright
    BROWSER_HEADLESS: bool = True
    BROWSER_SLOW_MO: int = 0  # ms - 0=sin slowmo, usar 500-1000 para debug visual
    BROWSER_TIMEOUT: int = 90000  # ms
    DOWNLOAD_TIMEOUT: int = 45000  # ms

    # Configuración de la DIAN
    DIAN_WAIT_AFTER_LOGIN: int = 8000  # ms
    DIAN_WAIT_AFTER_CLICK: int = 2000  # ms
    DIAN_WAIT_BETWEEN_DOWNLOADS: int = 2000  # ms
    DIAN_PAGINATION_WAIT: int = 8000  # ms

    # Límites y restricciones
    MAX_CONCURRENT_TASKS: int = 10

    # Configuración de logs
    LOG_LEVEL: str = "INFO"
    ENABLE_DEBUG_SCREENSHOTS: bool = False

    # Configuración de limpieza automática
    AUTO_CLEANUP_ENABLED: bool = False
    AUTO_CLEANUP_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list = ["*"]

    # Configuración de Base de Datos PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "dian_user"
    DB_PASSWORD: str = "dian_password"
    DB_NAME: str = "dian_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False  # SQL query logging

    # Configuración de Seguridad y API Keys
    API_KEY_ENABLED: bool = True
    MASTER_API_KEY: str = "master_key_change_this_in_production"
    API_KEY_HEADER_NAME: str = "X-API-Key"
    API_KEY_LENGTH: int = 32  # Longitud de las API keys generadas

    @property
    def DATABASE_URL(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()

# Crear carpeta de descargas
os.makedirs(settings.DOWNLOAD_BASE_FOLDER, exist_ok=True)
