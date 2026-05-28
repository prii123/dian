# 🐳 Guía de Despliegue con Docker

Esta guía explica cómo ejecutar el servicio DIAN REST API usando Docker y Docker Compose.

## 📋 Prerrequisitos

- Docker Engine 20.10 o superior
- Docker Compose 2.0 o superior

## 🚀 Inicio Rápido

### 1. Construir y ejecutar con Docker Compose

```bash
# Construir la imagen y ejecutar el contenedor
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener el servicio
docker-compose down
```

### 2. Acceder a la aplicación

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Estructura de Volúmenes

```
proyectos/dian-rest-documentos/
├── descargas/          # Archivos descargados (persistente)
└── logs/               # Logs de la aplicación (opcional)
```

Los archivos descargados se guardan en `./descargas` en tu máquina host y persisten después de detener el contenedor.

## ⚙️ Configuración

### Variables de Entorno

Puedes personalizar la configuración editando el archivo `docker-compose.yml`:

```yaml
environment:
  APP_NAME: "DIAN Document Service"
  SERVER_PORT: "8000"
  BROWSER_HEADLESS: "true"
  MAX_CONCURRENT_TASKS: "3"
  LOG_LEVEL: "INFO"
  # ... más configuraciones
```

### Archivo .env (Opcional)

También puedes crear un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Y modificar `docker-compose.yml` para usarlo:

```yaml
services:
  dian-api:
    env_file:
      - .env
```

## 🛠️ Comandos Útiles

### Ver logs en tiempo real
```bash
docker-compose logs -f dian-api
```

### Reiniciar el servicio
```bash
docker-compose restart
```

### Reconstruir la imagen después de cambios
```bash
docker-compose up -d --build
```

### Entrar al contenedor
```bash
docker-compose exec dian-api bash
```

### Ver estado de los contenedores
```bash
docker-compose ps
```

### Limpiar todo (contenedores, volúmenes, redes)
```bash
docker-compose down -v
```

## 🔍 Verificar que todo funciona

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Verificar que Playwright está instalado
```bash
docker-compose exec dian-api playwright --version
```

### 3. Probar endpoint principal
```bash
curl http://localhost:8000/
```

## 🐛 Troubleshooting

### El navegador no inicia (Error de memoria compartida)

Si ves errores relacionados con memoria compartida, asegúrate de que el `docker-compose.yml` tenga:

```yaml
shm_size: '2gb'
```

### Problemas de permisos en ./descargas

```bash
# Dar permisos a la carpeta
chmod -R 777 descargas/
```

### Ver logs detallados

```bash
# Cambiar LOG_LEVEL a DEBUG en docker-compose.yml
environment:
  LOG_LEVEL: "DEBUG"

# Reiniciar
docker-compose restart
```

### El contenedor no inicia

```bash
# Ver logs completos
docker-compose logs dian-api

# Ver estado
docker-compose ps
```

## 📊 Monitoreo

### Ver recursos utilizados
```bash
docker stats dian-api
```

### Ver logs de salud
```bash
docker inspect --format='{{json .State.Health}}' dian-api | jq
```

## 🔐 Seguridad

### Notas importantes:

1. **SYS_ADMIN capability**: Necesaria para que Chromium funcione en contenedores
2. **Headless mode**: Siempre usa `BROWSER_HEADLESS=true` en producción
3. **CORS**: Ajusta `CORS_ORIGINS` según tus necesidades de seguridad
4. **Red de Docker**: Usa `dian-network` para aislar el servicio

## 🚢 Despliegue en Producción

### Usando Docker Run

Si prefieres usar `docker run` directamente:

```bash
# Construir la imagen
docker build -t dian-rest-api:latest .

# Ejecutar el contenedor
docker run -d \
  --name dian-api \
  -p 8000:8000 \
  -v $(pwd)/descargas:/app/descargas \
  --shm-size=2g \
  --cap-add=SYS_ADMIN \
  -e BROWSER_HEADLESS=true \
  -e LOG_LEVEL=INFO \
  dian-rest-api:latest
```

### Usando Docker Swarm o Kubernetes

Para orquestación avanzada, revisa los archivos de ejemplo:
- `k8s-deployment.yaml` (próximamente)
- `docker-stack.yml` (próximamente)

## 📝 Ejemplo de Uso

```bash
# 1. Iniciar descarga
curl -X POST http://localhost:8000/api/iniciar-descarga \
  -H "Content-Type: application/json" \
  -d '{
    "token_url": "https://catalogo-vpfe.dian.gov.co/...token...",
    "fecha_inicio": "11-04-2026",
    "fecha_fin": "12-04-2026"
  }'

# Respuesta: {"task_id": "abc123...", "mensaje": "Tarea iniciada...", "status": "pending"}

# 2. Consultar estado
curl http://localhost:8000/api/estado-tarea/abc123...

# 3. Listar archivos descargados
curl http://localhost:8000/api/listar-archivos/abc123...

# 4. Descargar archivo
curl -O http://localhost:8000/api/descargar-archivo/abc123.../archivo.xml
```

## 📚 Recursos Adicionales

- [Documentación de Docker](https://docs.docker.com/)
- [Playwright en Docker](https://playwright.dev/python/docs/docker)
- [FastAPI](https://fastapi.tiangolo.com/)

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica la configuración en `docker-compose.yml`
3. Asegúrate de tener suficiente RAM (mínimo 2GB para Chromium)
