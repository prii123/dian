"""
Punto de entrada de la aplicación
"""

import asyncio
import sys

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    # Fix para Windows: Playwright requiere ProactorEventLoop (soporta subprocess_exec)
    # en versiones Python 3.8+ con Playwright 1.41+
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
