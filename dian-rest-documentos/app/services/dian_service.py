"""
Servicio para interactuar con el portal de la DIAN
"""

import os
import asyncio
from datetime import datetime

from playwright.async_api import async_playwright
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import logger
from app.models.db_models import Lote
from app.services.task_service import TaskService
from app.services.lote_service import LoteService


class DianService:
    """Servicio para automatizar la descarga de documentos de DIAN"""

    # Configuración de reintentos
    MAX_REINTENTOS = 5
    DELAY_INICIAL = 2  # segundos
    FACTOR_EXPONENCIAL = 1.5  # Aumentar delay cada vez

    @staticmethod
    async def _retry_action(
        action_func,
        db,
        task_id: str,
        action_name: str = "acción",
        max_retries: int = None,
    ):
        """
        Ejecuta una acción con reintentos automáticos

        Args:
            action_func: Función async que ejecutar
            db: Sesión de BD para actualizar estado
            task_id: ID de la tarea para logging
            action_name: Nombre descriptivo de la acción
            max_retries: Número máximo de reintentos (usa MAX_REINTENTOS si no se especifica)

        Returns:
            Resultado de action_func si tiene éxito
        
        Raises:
            Exception: Si falla después de todos los reintentos
        """
        if max_retries is None:
            max_retries = DianService.MAX_REINTENTOS

        delay = DianService.DELAY_INICIAL
        ultimo_error = None

        for intento in range(max_retries + 1):
            try:
                logger.info(
                    f"Tarea {task_id}: {action_name} (intento {intento + 1}/{max_retries + 1})"
                )

                resultado = await action_func()
                
                if intento > 0:
                    logger.info(f"Tarea {task_id}: {action_name} exitoso después de {intento} reintentos")
                
                return resultado

            except Exception as e:
                ultimo_error = e
                
                if intento < max_retries:
                    # Calcular delay con backoff exponencial
                    espera = delay * (DianService.FACTOR_EXPONENCIAL ** intento)
                    
                    logger.warning(
                        f"Tarea {task_id}: Error en {action_name}: {str(e)[:100]}. "
                        f"Reintentando en {espera:.1f}s... (intento {intento + 1}/{max_retries})"
                    )
                    
                    # Actualizar estado con mensaje de reintento
                    await TaskService.update_task(
                        db,
                        task_id,
                        {
                            "mensaje": f"{action_name} - reintentando en {espera:.0f}s (intento {intento + 1}/{max_retries})...",
                        },
                    )
                    
                    await asyncio.sleep(espera)
                else:
                    # Último intento falló
                    logger.error(f"Tarea {task_id}: {action_name} falló después de {max_retries} reintentos")

        # Si llegamos aquí, se agotaron los reintentos
        raise ultimo_error

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

                    # Con reintentos para clicks de navegación
                    async def click_document_index():
                        await page.locator("a#DocumentIndex").click(timeout=15000)

                    async def click_document_received():
                        await page.locator("li#DocumentReceived a").click(timeout=15000)

                    await DianService._retry_action(
                        click_document_index,
                        db,
                        task_id,
                        action_name="Clic en índice de documentos",
                        max_retries=2,
                    )
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK)

                    await DianService._retry_action(
                        click_document_received,
                        db,
                        task_id,
                        action_name="Clic en documentos recibidos",
                        max_retries=2,
                    )
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

                    # Usar reintentos para el click del botón de búsqueda (paso crítico)
                    async def click_buscar():
                        await page.locator("button.btn-radian-success").click(timeout=15000)

                    await DianService._retry_action(
                        click_buscar,
                        db,
                        task_id,
                        action_name="Clic en botón de búsqueda",
                        max_retries=3,
                    )

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

    @staticmethod
    async def descargar_por_cufes(lote_id: str):
        """
        Procesa un lote de CUFE: navega al portal DIAN, busca cada CUFE
        y descarga el ZIP correspondiente.

        Soporta reanudacion: solo procesa CUFE con status 'pending' o 'failed'.
        """
        logger.info(f"Lote {lote_id}: Iniciando proceso de descarga por CUFE")

        async with AsyncSessionLocal() as db:
            try:
                token_url = await LoteService.get_lote_token_url(db, lote_id)
                if not token_url:
                    raise Exception("No se encontro token_url en el lote")

                await LoteService.update_lote(
                    db, lote_id, {"status": "running", "mensaje": "Iniciando navegador..."}
                )

                download_folder = os.path.join(
                    settings.DOWNLOAD_BASE_FOLDER,
                    f"lote_{lote_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )
                os.makedirs(download_folder, exist_ok=True)
                await LoteService.update_lote(db, lote_id, {"download_folder": download_folder})

                logger.info(f"Lote {lote_id}: Carpeta de descarga: {download_folder}")

                async with async_playwright() as p:
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

                    # Paso 1: Login
                    await LoteService.update_lote(
                        db, lote_id, {"mensaje": "Conectando a portal DIAN...", "progress": 2}
                    )
                    await page.goto(
                        token_url, wait_until="networkidle", timeout=settings.BROWSER_TIMEOUT
                    )
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_LOGIN)
                    logger.info(f"Lote {lote_id}: Conectado a portal DIAN")

                    # Paso 2: Navegar a Documentos Recibidos
                    await LoteService.update_lote(
                        db, lote_id, {"mensaje": "Navegando a Documentos Recibidos...", "progress": 5}
                    )

                    async def click_document_index():
                        await page.locator("a#DocumentIndex").click(timeout=15000)

                    async def click_document_received():
                        await page.locator("li#DocumentReceived a").click(timeout=15000)

                    await DianService._retry_action(
                        click_document_index, db, lote_id,
                        action_name="Clic en indice de documentos", max_retries=2,
                    )
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK)

                    await DianService._retry_action(
                        click_document_received, db, lote_id,
                        action_name="Clic en documentos recibidos", max_retries=2,
                    )
                    await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK + 1000)

                    await page.wait_for_selector("#dashboard-report-range", timeout=20000)

                    # Paso 3: Configurar fechas (rango amplio si no hay fechas especificas)
                    lote_result = await db.execute(select(Lote).where(Lote.id == lote_id))
                    lote_obj = lote_result.scalar_one_or_none()
                    fecha_inicio = lote_obj.fecha_inicio if lote_obj and lote_obj.fecha_inicio else "01-01-2020"
                    fecha_fin = lote_obj.fecha_fin if lote_obj and lote_obj.fecha_fin else datetime.now().strftime("%d-%m-%Y")

                    rango_fecha = f"{fecha_inicio} - {fecha_fin}"
                    campo_fecha = page.locator("#dashboard-report-range")

                    await LoteService.update_lote(
                        db, lote_id,
                        {"mensaje": f"Configurando fechas {fecha_inicio} - {fecha_fin}...", "progress": 8}
                    )
                    await campo_fecha.click(timeout=10000)
                    await page.wait_for_timeout(500)
                    await campo_fecha.fill(rango_fecha)
                    await page.wait_for_timeout(500)
                    await campo_fecha.dispatch_event("change")
                    await page.wait_for_timeout(500)

                    # Paso 4: Buscar
                    await LoteService.update_lote(
                        db, lote_id, {"mensaje": "Buscando documentos...", "progress": 10}
                    )

                    async def click_buscar():
                        await page.locator("button.btn-radian-success").click(timeout=15000)

                    await DianService._retry_action(
                        click_buscar, db, lote_id,
                        action_name="Clic en boton de busqueda", max_retries=3,
                    )

                    await page.wait_for_selector("button.download-document", timeout=30000)

                    # Paso 5: Procesar cada CUFE pendiente/fallido
                    cufes_pendientes = await LoteService.get_pending_cufes(db, lote_id)
                    total_pendientes = len(cufes_pendientes)

                    if total_pendientes == 0:
                        await LoteService.update_lote(
                            db, lote_id,
                            {"status": "completed", "mensaje": "No hay CUFE pendientes para procesar", "progress": 100}
                        )
                        await browser.close()
                        return

                    logger.info(f"Lote {lote_id}: Procesando {total_pendientes} CUFE pendientes/fallidos")

                    # Localizar el campo de busqueda del DataTable
                    search_input = page.locator(".dataTables_filter input[type='search'], input[type='search']").first

                    for idx, detalle in enumerate(cufes_pendientes):
                        cufe = detalle.cufe
                        try:
                            await LoteService.update_lote(
                                db, lote_id,
                                {
                                    "mensaje": f"Buscando CUFE {idx + 1}/{total_pendientes}: {cufe[:30]}...",
                                },
                            )

                            await LoteService.update_detalle(
                                db, detalle.id,
                                {
                                    "status": "downloading",
                                    "intentos": detalle.intentos + 1,
                                    "ultimo_intento": datetime.now(),
                                },
                            )

                            # Limpiar y buscar por CUFE
                            if await search_input.is_visible():
                                await search_input.click(timeout=5000)
                                await search_input.fill("")
                                await page.wait_for_timeout(500)
                                await search_input.fill(cufe)
                                await page.wait_for_timeout(settings.DIAN_WAIT_AFTER_CLICK)
                            else:
                                # Si no hay search input, recargar pagina y re-navegar
                                logger.warning(f"Lote {lote_id}: No se encontro campo de busqueda, recargando...")
                                await page.reload(wait_until="networkidle")
                                await page.wait_for_timeout(5000)
                                search_input = page.locator(".dataTables_filter input[type='search'], input[type='search']").first

                            # Verificar si aparecen botones de descarga
                            botones = page.locator("button.download-document")
                            cantidad = await botones.count()

                            if cantidad == 0:
                                # CUFE no encontrado
                                await LoteService.update_detalle(
                                    db, detalle.id,
                                    {"status": "not_found", "mensaje": "CUFE no encontrado en el portal DIAN"},
                                )
                                await LoteService.recalculate_lote_counts(db, lote_id)
                                logger.info(f"Lote {lote_id}: CUFE {cufe[:30]}... no encontrado")
                                continue

                            # Buscar el boton con el data-id que coincida
                            encontrado = False
                            for i in range(cantidad):
                                boton = botones.nth(i)
                                doc_id = await boton.get_attribute("data-id")
                                if doc_id and (doc_id == cufe or cufe in doc_id or doc_id in cufe):
                                    encontrado = True
                                    id_corto = doc_id[:12] if doc_id else f"cufe_{idx}"

                                    async with page.expect_download(timeout=settings.DOWNLOAD_TIMEOUT) as dl_info:
                                        await boton.click(timeout=15000)

                                    download = await dl_info.value
                                    filename = f"CUFE_{id_corto}_{datetime.now().strftime('%H%M%S')}.zip"
                                    save_path = os.path.join(download_folder, filename)
                                    await download.save_as(save_path)

                                    await LoteService.update_detalle(
                                        db, detalle.id,
                                        {
                                            "status": "downloaded",
                                            "download_path": save_path,
                                            "mensaje": f"Descargado: {filename}",
                                        },
                                    )
                                    await LoteService.recalculate_lote_counts(db, lote_id)
                                    logger.info(f"Lote {lote_id}: CUFE {cufe[:30]}... descargado exitosamente")
                                    await page.wait_for_timeout(settings.DIAN_WAIT_BETWEEN_DOWNLOADS)
                                    break

                            if not encontrado:
                                # El CUFE no estaba entre los resultados visibles
                                await LoteService.update_detalle(
                                    db, detalle.id,
                                    {"status": "not_found", "mensaje": "CUFE no encontrado en los resultados visibles"},
                                )
                                await LoteService.recalculate_lote_counts(db, lote_id)
                                logger.info(f"Lote {lote_id}: CUFE {cufe[:30]}... no encontrado en resultados")

                            # Actualizar progreso general
                            progreso = 10 + ((idx + 1) / total_pendientes) * 85
                            await LoteService.update_lote(
                                db, lote_id, {"progress": min(progreso, 95)}
                            )

                        except Exception as e:
                            error_msg = str(e)[:200]
                            logger.error(f"Lote {lote_id}: Error en CUFE {cufe[:30]}...: {error_msg}")

                            await LoteService.update_detalle(
                                db, detalle.id,
                                {"status": "failed", "mensaje": error_msg},
                            )
                            await LoteService.recalculate_lote_counts(db, lote_id)

                            # Continuar con el siguiente CUFE
                            await page.wait_for_timeout(2000)

                    await browser.close()

                    # Actualizar estado final del lote
                    await LoteService.recalculate_lote_counts(db, lote_id)

                    lote_final_result = await db.execute(select(Lote).where(Lote.id == lote_id))
                    lote_final_obj = lote_final_result.scalar_one_or_none()

                    if lote_final_obj and lote_final_obj.status == "running":
                        await LoteService.update_lote(
                            db, lote_id,
                            {
                                "status": "completed",
                                "progress": 100,
                                "mensaje": f"Proceso completado. {lote_final_obj.descargados}/{lote_final_obj.total_cufes} descargados.",
                            },
                        )

                    logger.info(
                        f"Lote {lote_id}: Completado. "
                        f"Descargados={lote_final_obj.descargados if lote_final_obj else '?'}, "
                        f"Fallidos={lote_final_obj.fallidos if lote_final_obj else '?'}, "
                        f"No encontrados={lote_final_obj.no_encontrados if lote_final_obj else '?'}"
                    )

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logger.error(f"Lote {lote_id}: {error_msg}", exc_info=True)
                await LoteService.update_lote(
                    db, lote_id, {"status": "failed", "mensaje": error_msg}
                )
