"""
Servicio para interactuar con el portal de la DIAN
"""

import os
from datetime import datetime

from playwright.async_api import async_playwright

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import logger
from app.services.task_service import TaskService


class DianService:
    """Servicio para automatizar la descarga de documentos de DIAN"""

    @staticmethod
    async def descargar_documentos(
        task_id: str, token_url: str, fecha_inicio: str, fecha_fin: str
    ):
        """
        Ejecuta el proceso de descarga de documentos de DIAN

        Args:
            task_id: ID de la tarea
            token_url: URL con token de autenticación
            fecha_inicio: Fecha inicio (DD-MM-YYYY)
            fecha_fin: Fecha fin (DD-MM-YYYY)
        """
        logger.info(f"Tarea {task_id}: Iniciando proceso de descarga")

        # Crear sesión de base de datos para el background task
        async with AsyncSessionLocal() as db:
            try:
                # Actualizar estado a 'running'
                await TaskService.update_task(
                    db,
                    task_id,
                    {"status": "running", "mensaje": "Iniciando navegador..."},
                )

                # Crear carpeta específica para esta tarea
                download_folder = os.path.join(
                    settings.DOWNLOAD_BASE_FOLDER,
                    f"tarea_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )
                os.makedirs(download_folder, exist_ok=True)
                await TaskService.update_task(
                    db, task_id, {"download_folder": download_folder}
                )

                logger.info(f"Tarea {task_id}: Carpeta de descarga: {download_folder}")

                async with async_playwright() as p:
                    # Iniciar navegador
                    browser = await p.chromium.launch(
                        headless=settings.BROWSER_HEADLESS,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                        ],
                    )
                    context = await browser.new_context(accept_downloads=True)
                    page = await context.new_page()

                    # Paso 1: Abrir portal DIAN
                    await TaskService.update_task(
                        db,
                        task_id,
                        {"mensaje": "Conectando a portal DIAN...", "progress": 5},
                    )

                    await page.goto(
                        token_url,
                        wait_until="networkidle",
                        timeout=settings.BROWSER_TIMEOUT,
                    )
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_LOGIN)
                    logger.info(f"Tarea {task_id}: Conectado a portal DIAN")

                    # Paso 2: Navegar a Documentos Recibidos
                    await TaskService.update_task(
                        db,
                        task_id,
                        {
                            "mensaje": "Navegando a Documentos Recibidos...",
                            "progress": 10,
                        },
                    )

                    await page.locator("a#DocumentIndex").click(timeout=15000)
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK)

                    await page.locator("li#DocumentReceived a").click(timeout=15000)
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK + 1000)

                    await page.wait_for_selector(
                        "#dashboard-report-range", timeout=20000
                    )

                    # Paso 3: Configurar fechas
                    await TaskService.update_task(
                        db,
                        task_id,
                        {
                            "mensaje": f"Configurando fechas {fecha_inicio} - {fecha_fin}...",
                            "progress": 15,
                        },
                    )

                    rango_fecha = f"{fecha_inicio} - {fecha_fin}"
                    campo_fecha = page.locator("#dashboard-report-range")
                    await campo_fecha.click(timeout=10000)
                    await page.wait_for_timeout(500)
                    await campo_fecha.fill(rango_fecha)
                    await page.wait_for_timeout(500)
                    await campo_fecha.dispatch_event("change")
                    await page.wait_for_timeout(500)

                    # Paso 4: Buscar documentos
                    await TaskService.update_task(
                        db,
                        task_id,
                        {"mensaje": "Buscando documentos...", "progress": 20},
                    )

                    await page.locator("button.btn-radian-success").click(timeout=15000)
                    await page.wait_for_selector(
                        "button.download-document", timeout=30000
                    )

                    # Paso 5: Obtener total de documentos
                    total_estimado = await DianService._obtener_total_documentos(
                        page, db, task_id
                    )

                    # Paso 6: Descargar todos los documentos
                    total_descargados = await DianService._descargar_todas_paginas(
                        page, db, task_id, download_folder, total_estimado
                    )

                    await browser.close()

                    # Completar tarea
                    await TaskService.update_task(
                        db,
                        task_id,
                        {
                            "status": "completed",
                            "progress": 100,
                            "descargados": total_descargados,
                            "mensaje": f"Proceso completado. {total_descargados} documentos descargados.",
                        },
                    )

                    logger.info(
                        f"Tarea {task_id}: Completada exitosamente. {total_descargados} documentos descargados"
                    )

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logger.error(f"Tarea {task_id}: {error_msg}", exc_info=True)

                await TaskService.update_task(
                    db, task_id, {"status": "failed", "mensaje": error_msg}
                )

    @staticmethod
    async def _obtener_total_documentos(page, db, task_id: str) -> int:
        """Obtiene el total de documentos a descargar"""
        try:
            info_tabla = await page.locator(
                ".dataTables_info, [class*='info']"
            ).first.inner_text()
            if "de" in info_tabla:
                total_estimado = int(info_tabla.split("de")[-1].strip().split()[0])
                await TaskService.update_task(
                    db, task_id, {"total_documentos": total_estimado}
                )
                logger.info(
                    f"Tarea {task_id}: Total estimado de documentos: {total_estimado}"
                )
                return total_estimado
        except Exception as e:
            logger.warning(
                f"Tarea {task_id}: No se pudo determinar total de documentos: {e}"
            )

        # Fallback: contar botones visibles
        total_botones = await page.locator("button.download-document").count()
        await TaskService.update_task(db, task_id, {"total_documentos": total_botones})
        return total_botones

    @staticmethod
    async def _descargar_todas_paginas(
        page, db, task_id: str, download_folder: str, total_estimado: int
    ) -> int:
        """Descarga documentos de todas las páginas"""
        total_descargados = 0
        pagina_actual = 1

        while True:
            await TaskService.update_task(
                db,
                task_id,
                {
                    "mensaje": f"Procesando página {pagina_actual}...",
                    "pagina_actual": pagina_actual,
                },
            )

            # Esperar botones de descarga
            try:
                await page.locator("button.download-document").first.wait_for(
                    timeout=20000
                )
            except Exception:
                logger.info(
                    f"Tarea {task_id}: No hay más botones. Finalizando en página {pagina_actual}"
                )
                break

            # Descargar archivos de la página actual
            botones = page.locator("button.download-document")
            cantidad = await botones.count()

            logger.info(
                f"Tarea {task_id}: Página {pagina_actual} - {cantidad} documentos"
            )

            for i in range(cantidad):
                try:
                    boton = botones.nth(i)
                    doc_id = await boton.get_attribute("data-id")
                    id_corto = doc_id[:12] if doc_id else f"doc_{i}"

                    # Descargar archivo
                    async with page.expect_download(
                        timeout=settings.DOWNLOAD_TIMEOUT
                    ) as dl_info:
                        await boton.click(timeout=15000)

                    download = await dl_info.value
                    filename = f"Recibido_P{pagina_actual}_{i + 1:03d}_{id_corto}_{datetime.now().strftime('%H%M%S')}.zip"
                    save_path = os.path.join(download_folder, filename)
                    await download.save_as(save_path)

                    total_descargados += 1

                    # Actualizar progreso
                    progress = 20 + (total_descargados / max(total_estimado, 1)) * 75

                    await TaskService.update_task(
                        db,
                        task_id,
                        {
                            "descargados": total_descargados,
                            "progress": min(progress, 95),
                            "mensaje": f"Descargado {total_descargados}/{total_estimado} - {filename}",
                        },
                    )

                    logger.debug(
                        f"Tarea {task_id}: Descargado {total_descargados}/{total_estimado} - {filename}"
                    )

                    await page.wait_for_timeout(settings.DIAN_WAIT_BETWEEN_DOWNLOADS)

                except Exception as e:
                    logger.error(
                        f"Tarea {task_id}: Error en botón {i + 1} página {pagina_actual}: {str(e)[:100]}"
                    )
                    continue

            # Verificar si hay siguiente página
            siguiente = page.locator("button.dt-paging-button.next")
            disabled = await siguiente.get_attribute("aria-disabled")

            if disabled == "true":
                logger.info(
                    f"Tarea {task_id}: Última página alcanzada (página {pagina_actual})"
                )
                break

            # Ir a siguiente página
            await siguiente.click(timeout=10000)
            await page.wait_for_timeout(settings.DIAN_PAGINATION_WAIT)
            pagina_actual += 1
            logger.info(f"Tarea {task_id}: Navegando a página {pagina_actual}")

        return total_descargados
