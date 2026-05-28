# DIAN REST API - Servicio de Descarga de Documentos

Servicio REST profesional y modular para automatizar la descarga de documentos recibidos desde el portal de la DIAN.

## 🐳 Inicio Rápido con Docker (Recomendado)

La forma más rápida de ejecutar el servicio es usando Docker:

### Windows
```bash
start-docker.bat
```

### Linux/Mac
```bash
chmod +x start-docker.sh
./start-docker.sh
```

### Usando Docker Compose directamente
```bash
docker-compose up -d
```

**URLs disponibles:**
- 📍 API: http://localhost:8000
- 📚 Swagger UI: http://localhost:8000/docs
- 📖 ReDoc: http://localhost:8000/redoc
- 🏥 Health: http://localhost:8000/health

Ver [README_DOCKER.md](README_DOCKER.md) para documentación completa de Docker.

## 🏗️ Arquitectura del Proyecto

El proyecto sigue una arquitectura modular limpia con separación de responsabilidades:

```
dian-rest-documentos/
├── app/                      # Aplicación principal
│   ├── core/                 # Configuración y utilidades centrales
│   ├── models/               # Schemas de validación (Pydantic)
│   ├── routes/               # Endpoints de la API
│   ├── services/             # Lógica de negocio
│   └── main.py               # Aplicación FastAPI
├── run.py                    # Punto de entrada
├── requirements.txt          # Dependencias
└── .env.example              # Variables de entorno
```

Ver [README_PROYECTO.md](README_PROYECTO.md) para detalles completos de la arquitectura.

## 🚀 Instalación Local (Desarrollo)

> **Nota:** Para uso en producción o pruebas rápidas, se recomienda usar Docker (ver arriba).

### 1. Crear entorno virtual e instalar dependencias

```bash
# Crear venv
python -m venv venv

# Activar (Windows Git Bash)
source venv/Scripts/activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegador Chromium
playwright install chromium
```

### 2. Configurar variables de entorno (opcional)

```bash
cp .env.example .env
# Editar .env según necesites
```

### 3. Iniciar el servidor

```bash
# Opción 1: Script directo
python run.py

# Opción 2: Script batch (Windows)
iniciar_servidor.bat

# Opción 3: Script shell (Linux/Mac)
./iniciar_servidor.sh
```

El servidor estará disponible en: **http://localhost:8000**

Documentación interactiva: **http://localhost:8000/docs**

## 📡 Endpoints

### 1. Iniciar descarga de documentos

**POST** `/api/iniciar-descarga`

Inicia una tarea de descarga de documentos de la DIAN.

**Body (JSON):**
```json
{
  "token_url": "https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=10910094%7C32489202&rk=901272421&token=78ee5cb2-1278-4151-bc52-c2fe80aa71f2",
  "fecha_inicio": "11-04-2026",
  "fecha_fin": "12-04-2026"
}
```

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "mensaje": "Tarea iniciada exitosamente",
  "status": "pending"
}
```

### 2. Consultar estado de la tarea

**GET** `/api/estado-tarea/{task_id}`

Obtiene el progreso y estado actual de una tarea.

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45.5,
  "total_documentos": 87,
  "descargados": 40,
  "pagina_actual": 4,
  "mensaje": "Descargado 40/87 - Recibido_P4_005_abc123_143022.zip",
  "created_at": "2026-04-13T10:30:00",
  "updated_at": "2026-04-13T10:35:22",
  "download_folder": "./descargas/tarea_550e8400_20260413_103000"
}
```

**Estados posibles:**
- `pending`: Tarea creada, esperando inicio
- `running`: Tarea en ejecución
- `completed`: Tarea completada exitosamente
- `failed`: Tarea falló con error

### 3. Listar archivos descargados

**GET** `/api/listar-archivos/{task_id}`

Lista todos los archivos descargados de una tarea.

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "archivos": [
    {
      "nombre": "Recibido_P1_001_abc123_140522.zip",
      "tamaño_kb": 125.67,
      "tipo": "ZIP"
    },
    {
      "nombre": "Recibido_P1_002_def456_140525.zip",
      "tamaño_kb": 98.23,
      "tipo": "ZIP"
    }
  ],
  "total": 2
}
```

### 4. Descargar un archivo específico

**GET** `/api/descargar-archivo/{task_id}/{nombre_archivo}`

Descarga un archivo específico (ZIP, PDF, XML).

**Ejemplo:**
```
GET /api/descargar-archivo/550e8400-e29b-41d4-a716-446655440000/Recibido_P1_001_abc123_140522.zip
```

**Respuesta:** Archivo binario

### 5. Listar archivos con filtro

**GET** `/api/descargar-todos/{task_id}?tipo=zip`

Lista archivos con opción de filtrar por tipo.

**Parámetros:**
- `tipo` (opcional): `zip`, `pdf`, o `xml`

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "filtro_tipo": "zip",
  "archivos": [
    {
      "nombre": "Recibido_P1_001_abc123_140522.zip",
      "tamaño_kb": 125.67,
      "tipo": "ZIP",
      "url_descarga": "/api/descargar-archivo/550e8400.../Recibido_P1_001_abc123_140522.zip"
    }
  ],
  "total": 1
}
```

### 6. Health Check

**GET** `/health`

Verifica el estado del servicio.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T10:30:00",
  "tareas_activas": 2
}
```

## 🔄 Flujo de trabajo típico

```bash
# 1. Iniciar descarga
curl -X POST http://localhost:8000/api/iniciar-descarga \
  -H "Content-Type: application/json" \
  -d '{
    "token_url": "https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz",
    "fecha_inicio": "11-04-2026",
    "fecha_fin": "12-04-2026"
  }'

# Respuesta: { "task_id": "abc-123", ... }

# 2. Consultar progreso (repetir hasta que status sea "completed")
curl http://localhost:8000/api/estado-tarea/abc-123

# 3. Listar archivos descargados
curl http://localhost:8000/api/listar-archivos/abc-123

# 4. Descargar un archivo específico
curl -O http://localhost:8000/api/descargar-archivo/abc-123/archivo.zip
```

## 📝 Notas importantes

- Los archivos se descargan en la carpeta `./descargas/tarea_{task_id}_{timestamp}/`
- Las tareas se mantienen en memoria mientras el servicio esté corriendo
- Para producción, considera implementar:
  - Persistencia de tareas en base de datos
  - Sistema de colas (Celery, Redis)
  - Limpieza automática de archivos antiguos
  - Autenticación y autorización
  - Límite de tareas concurrentes

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **Playwright**: Automatización de navegador
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos

## 📄 Licencia

MIT

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
