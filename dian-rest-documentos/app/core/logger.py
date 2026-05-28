"""
Configuración de logging
"""
import logging
import sys
from app.core.config import settings


def setup_logger():
    """Configura el logger de la aplicación"""
    
    # Crear logger
    logger = logging.getLogger("dian_service")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Crear handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Crear formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Agregar handler al logger
    logger.addHandler(console_handler)
    
    return logger


# Logger global
logger = setup_logger()
