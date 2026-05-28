# 📁 Estructura del Proyecto

## 🏗️ Arquitectura Modular

El proyecto sigue una arquitectura modular limpia y escalable, separando responsabilidades:

```
dian-rest-documentos/
│
├── app/                          # Aplicación principal
│   ├── __init__.py
│   ├── main.py                   # Punto de entrada FastAPI
│   │
│   ├── core/                     # Configuración y utilidades centrales
│   │   ├── __init__.py
│   │   ├── config.py             # Configuración centralizada (settings)
│   │   ├── database.py           # Almacenamiento de tareas
│   │   └── logger.py             # Configuración de logging
│   │
│   ├── models/                   # Modelos y schemas de datos
│   │   ├── __init__.py
│   │   └── schemas.py            # Schemas de Pydantic
│   │
│   ├── routes/                   # Endpoints de la API
│   │   ├── __init__.py
│   │   ├── tasks.py              # Rutas de tareas (/api/iniciar-descarga, /api/estado-tarea)
│   │   ├── files.py              # Rutas de archivos (/api/listar-archivos, /api/descargar-archivo)
│   │   └── health.py             # Health check (/, /health)
│   │
│   └── services/                 # Lógica de negocio
│       ├── __init__.py
│       ├── dian_service.py       # Servicio para automatización de DIAN
│       └── task_service.py       # Servicio de gestión de tareas
│
├── descargas/                    # Carpeta de archivos descargados (auto-generada)
│
├── run.py                        # Script de inicio de la aplicación
├── requirements.txt              # Dependencias
├── .env.example                  # Ejemplo de variables de entorno
├── .gitignore                    # Archivos ignorados por git
│
├── README.md                     # Documentación principal
├── README_PROYECTO.md            # Este archivo - Estructura del proyecto
├── INICIO_RAPIDO.md              # Guía de inicio rápido
│
├── config.py                     # (Legacy - será removido)
├── main.py                       # (Legacy - será removido)
├── test.py                       # Script original
├── ejemplo_uso.py                # Ejemplo de uso de la API
├── ejemplos_curl.md              # Ejemplos con curl
└── iniciar_servidor.bat          # Script para Windows
```

## 📦 Descripción de Módulos

### 🔧 `app/core/` - Núcleo de la Aplicación

**config.py**: Configuración centralizada usando Pydantic Settings
- Carga variables de entorno desde `.env`
- Define configuración del servidor, timeouts, límites, etc.
- Instancia global `settings` accesible desde toda la app

**database.py**: Almacenamiento en memoria
- Clase `InMemoryTaskStore` para gestionar tareas
- En producción, reemplazar por PostgreSQL, MongoDB, etc.
- Métodos CRUD para tareas

**logger.py**: Sistema de logging
- Configuración centralizada de logs
- Formato consistente en toda la aplicación
- Niveles configurables (DEBUG, INFO, WARNING, ERROR)

### 📊 `app/models/` - Modelos de Datos

**schemas.py**: Schemas de validación con Pydantic
- `TaskRequest`: Validación de peticiones de descarga
- `TaskStatus`: Estado de una tarea
- `TaskCreateResponse`: Respuesta al crear tarea
- `FileInfo`: Información de archivo
- `FileListResponse`: Listado de archivos
- `HealthResponse`: Respuesta del health check

### 🛣️ `app/routes/` - Rutas de la API

**tasks.py**: Endpoints de tareas
- `POST /api/iniciar-descarga` - Iniciar descarga
- `GET /api/estado-tarea/{task_id}` - Consultar estado

**files.py**: Endpoints de archivos
- `GET /api/listar-archivos/{task_id}` - Listar archivos
- `GET /api/descargar-archivo/{task_id}/{nombre}` - Descargar archivo
- `GET /api/descargar-todos/{task_id}` - Listar con filtros

**health.py**: Endpoints de salud
- `GET /` - Información del servicio
- `GET /health` - Health check

### ⚙️ `app/services/` - Lógica de Negocio

**task_service.py**: Gestión de tareas
- `create_task()` - Crear nueva tarea
- `get_task()` - Obtener estado de tarea
- `update_task()` - Actualizar tarea
- `count_running_tasks()` - Contar tareas activas
- Validación de límites de concurrencia

**dian_service.py**: Automatización de DIAN
- `descargar_documentos()` - Proceso principal de descarga
- `_obtener_total_documentos()` - Extraer total de documentos
- `_descargar_todas_paginas()` - Descargar de todas las páginas
- Interacción con Playwright

## 🚀 Cómo Ejecutar

### Opción 1: Archivo principal nuevo
```bash
python run.py
```

### Opción 2: Usando uvicorn directamente
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


## 🔄 Flujo de Ejecución

```
1. Cliente hace POST /api/iniciar-descarga
   ↓
2. routes/tasks.py recibe la petición
   ↓
3. services/task_service.py crea la tarea
   ↓
4. services/dian_service.py ejecuta descarga en background
   ↓
5. Actualiza estado en core/database.py
   ↓
6. Cliente consulta GET /api/estado-tarea/{task_id}
   ↓
7. routes/tasks.py → services/task_service.py → core/database.py
   ↓
8. Cliente descarga archivos con GET /api/descargar-archivo/...
```


## 🔧 Configuración Personalizada

Copia `.env.example` a `.env` y modifica según necesites:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:
```env
SERVER_PORT=8000
MAX_CONCURRENT_TASKS=5
BROWSER_HEADLESS=True
LOG_LEVEL=DEBUG
```

## 📝 Próximos Pasos de Mejora

- [ ] Implementar base de datos real (PostgreSQL/MongoDB)
- [ ] Agregar autenticación y autorización (OAuth2, JWT)
- [ ] Implementar cola de tareas (Celery + Redis)
- [ ] Agregar tests unitarios y de integración
- [ ] Implementar limpieza automática de archivos antiguos
- [ ] Agregar métricas y monitoreo (Prometheus)
- [ ] Dockerizar la aplicación
- [ ] Agregar CI/CD
- [ ] Implementar WebSockets para notificaciones en tiempo real

## 🧪 Testing

Para agregar tests (próximamente):

```
tests/
├── __init__.py
├── test_tasks.py
├── test_files.py
├── test_services.py
└── conftest.py
```

## 📚 Recursos

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
