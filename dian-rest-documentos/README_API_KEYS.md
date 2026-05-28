# 🔐 Sistema de Autenticación con API Keys

Esta guía explica cómo usar el sistema de autenticación basado en API Keys implementado en el servicio DIAN REST API.

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Configuración Inicial](#configuración-inicial)
3. [Administración de API Keys](#administración-de-api-keys)
4. [Uso de API Keys](#uso-de-api-keys)
5. [Ejemplos](#ejemplos)
6. [Seguridad](#seguridad)

---

## Descripción General

### ¿Qué son las API Keys?

Las API Keys son tokens de autenticación que permiten controlar el acceso a los endpoints de la API. Cada cliente/usuario recibe una API Key única que debe incluir en cada request.

### Características

✅ **Autenticación basada en API Keys** - Control de acceso por cliente  
✅ **Almacenamiento seguro** - Las keys se hashean con bcrypt antes de almacenarse  
✅ **Master API Key** - Key especial para administrar otras keys  
✅ **Persistencia en PostgreSQL** - Base de datos relacional para gestión de keys  
✅ **Estadísticas de uso** - Tracking de requests por API Key  
✅ **Expiración opcional** - Keys con tiempo de vida limitado  

### Endpoints Protegidos

Los siguientes endpoints **requieren API Key** válida:

- `POST /api/iniciar-descarga` - Iniciar descarga de documentos
- `GET /api/estado-tarea/{task_id}` - Consultar estado de tarea
- `GET /api/listar-archivos/{task_id}` - Listar archivos descargados
- `GET /api/descargar-archivo/{task_id}/{nombre}` - Descargar archivo específico
- `GET /api/descargar-todos/{task_id}` - Descargar todos los archivos

### Endpoints Públicos (sin API Key)

- `GET /` - Información del servicio
- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

### Endpoints de Administración (requieren Master Key)

- `POST /admin/api-keys` - Crear nueva API Key
- `GET /admin/api-keys` - Listar todas las API Keys
- `GET /admin/api-keys/{key_id}` - Ver detalles de una API Key
- `PATCH /admin/api-keys/{key_id}` - Actualizar API Key
- `DELETE /admin/api-keys/{key_id}` - Revocar API Key

---

## Configuración Inicial

### 1. Variables de Entorno

Asegúrate de configurar las siguientes variables en tu `.env`:

```bash
# Base de datos PostgreSQL
DB_HOST=db
DB_PORT=5432
DB_USER=dian_user
DB_PASSWORD=dian_secure_password_2026
DB_NAME=dian_db

# Seguridad
API_KEY_ENABLED=true
MASTER_API_KEY=master_abc123def456_CHANGE_IN_PRODUCTION
API_KEY_HEADER_NAME=X-API-Key
```

⚠️ **IMPORTANTE**: Cambia `MASTER_API_KEY` en producción por un valor seguro.

### 2. Iniciar el Servicio con Docker

```bash
docker-compose up -d
```

Esto iniciará:
- PostgreSQL en el puerto 5432
- API REST en el puerto 8000

### 3. Verificar Conexión

```bash
curl http://localhost:8000/health
```

---

## Administración de API Keys

### Crear una Nueva API Key

**Endpoint**: `POST /admin/api-keys`  
**Requiere**: Master API Key

```bash
curl -X POST http://localhost:8000/admin/api-keys \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cliente ABC Corp",
    "description": "API key para cliente ABC - Proyecto DIAN",
    "expires_at": null
  }'
```

**Respuesta**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "name": "Cliente ABC Corp",
  "description": "API key para cliente ABC - Proyecto DIAN",
  "is_active": true,
  "created_at": "2026-04-13T10:30:00",
  "expires_at": null
}
```

⚠️ **CRÍTICO**: La API Key (`key`) **solo se muestra una vez** al crearla. Guárdala en un lugar seguro.

### Listar Todas las API Keys

```bash
curl -X GET http://localhost:8000/admin/api-keys \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION"
```

**Respuesta**:
```json
{
  "total": 2,
  "keys": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Cliente ABC Corp",
      "description": "API key para cliente ABC",
      "is_active": true,
      "created_at": "2026-04-13T10:30:00",
      "updated_at": "2026-04-13T10:30:00",
      "expires_at": null,
      "last_used_at": "2026-04-13T11:15:30",
      "request_count": 45
    }
  ]
}
```

### Ver Detalles de una API Key

```bash
curl -X GET http://localhost:8000/admin/api-keys/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION"
```

### Actualizar una API Key

```bash
curl -X PATCH http://localhost:8000/admin/api-keys/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cliente ABC Corp - Actualizado",
    "is_active": true
  }'
```

### Revocar (Desactivar) una API Key

```bash
curl -X DELETE http://localhost:8000/admin/api-keys/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION"
```

---

## Uso de API Keys

### Incluir API Key en las Peticiones

Todas las peticiones a endpoints protegidos deben incluir el header `X-API-Key`:

```bash
curl -X POST http://localhost:8000/api/iniciar-descarga \
  -H "X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" \
  -H "Content-Type: application/json" \
  -d '{
    "token_url": "https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz",
    "fecha_inicio": "11-04-2026",
    "fecha_fin": "12-04-2026"
  }'
```

### Respuestas de Error

#### Sin API Key (401 Unauthorized)

```bash
curl -X GET http://localhost:8000/api/estado-tarea/abc123
```

**Respuesta**:
```json
{
  "detail": "API Key requerida. Incluye el header 'X-API-Key' en tu request."
}
```

#### API Key Inválida (401 Unauthorized)

```bash
curl -X GET http://localhost:8000/api/estado-tarea/abc123 \
  -H "X-API-Key: invalid_key"
```

**Respuesta**:
```json
{
  "detail": "API Key inválida, expirada o revocada"
}
```

#### Master Key Inválida (403 Forbidden)

```bash
curl -X POST http://localhost:8000/admin/api-keys \
  -H "X-API-Key: wrong_master_key"
```

**Respuesta**:
```json
{
  "detail": "Acceso denegado. Se requiere Master API Key para esta operación."
}
```

---

## Ejemplos

### Flujo Completo de Uso

#### 1. Admin crea API Key para un cliente

```bash
# Crear API Key
curl -X POST http://localhost:8000/admin/api-keys \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sistema de Contabilidad XYZ",
    "description": "Integración automática para descarga de documentos DIAN"
  }'
```

**Respuesta**:
```json
{
  "id": "client-uuid-1234",
  "key": "clientkey123abc456def789",
  "name": "Sistema de Contabilidad XYZ",
  ...
}
```

👉 **Entregar `clientkey123abc456def789` al cliente de forma segura**

#### 2. Cliente usa su API Key

```bash
# Cliente inicia descarga
curl -X POST http://localhost:8000/api/iniciar-descarga \
  -H "X-API-Key: clientkey123abc456def789" \
  -H "Content-Type: application/json" \
  -d '{
    "token_url": "https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz",
    "fecha_inicio": "01-04-2026",
    "fecha_fin": "10-04-2026"
  }'
```

**Respuesta**:
```json
{
  "task_id": "task-uuid-5678",
  "mensaje": "Tarea iniciada exitosamente",
  "status": "pending"
}
```

#### 3. Cliente consulta el progreso

```bash
curl -X GET http://localhost:8000/api/estado-tarea/task-uuid-5678 \
  -H "X-API-Key: clientkey123abc456def789"
```

#### 4. Cliente descarga archivos

```bash
# Listar archivos
curl -X GET http://localhost:8000/api/listar-archivos/task-uuid-5678 \
  -H "X-API-Key: clientkey123abc456def789"

# Descargar archivo específico
curl -O http://localhost:8000/api/descargar-archivo/task-uuid-5678/archivo.zip \
  -H "X-API-Key: clientkey123abc456def789"
```

#### 5. Admin revisa estadísticas

```bash
# Ver uso de la API Key del cliente
curl -X GET http://localhost:8000/admin/api-keys/client-uuid-1234 \
  -H "X-API-Key: master_abc123def456_CHANGE_IN_PRODUCTION"
```

**Respuesta**:
```json
{
  "id": "client-uuid-1234",
  "name": "Sistema de Contabilidad XYZ",
  "is_active": true,
  "last_used_at": "2026-04-13T14:30:00",
  "request_count": 127
}
```

---

## Seguridad

### Mejores Prácticas

#### ✅ DO (Hacer)

1. **Cambiar Master Key en producción**
   ```bash
   MASTER_API_KEY=$(openssl rand -hex 32)
   ```

2. **Usar HTTPS en producción**
   - Nunca envíes API Keys por HTTP sin cifrar

3. **Rotar API Keys periódicamente**
   - Revoca keys antiguas y genera nuevas cada X meses

4. **Limitar permisos por cliente**
   - Cada cliente debe tener su propia API Key única

5. **Monitorear uso sospechoso**
   - Revisa logs y estadísticas de `request_count`

6. **Guardar keys en variables de entorno**
   ```bash
   export DIAN_API_KEY="clientkey123abc456def789"
   curl ... -H "X-API-Key: $DIAN_API_KEY"
   ```

#### ❌ DON'T (No hacer)

1. **No commitear API Keys en Git**
   - Usa `.gitignore` para archivos `.env`

2. **No compartir keys por email/chat sin cifrar**
   - Usa canales seguros como password managers compartidos

3. **No hardcodear keys en el código**
   ```python
   # ❌ MAL
   headers = {"X-API-Key": "clientkey123abc456def789"}
   
   # ✅ BIEN
   headers = {"X-API-Key": os.getenv("DIAN_API_KEY")}
   ```

4. **No usar la misma key para múltiples clientes**

5. **No loggear API Keys completas**
   ```python
   # ❌ MAL
   logger.info(f"API Key: {api_key}")
   
   # ✅ BIEN
   logger.info(f"API Key: {api_key[:8]}...")
   ```

### Almacenamiento de Keys

Las API Keys se almacenan de forma segura:

1. **Hash con bcrypt** - Solo el hash se guarda en PostgreSQL
2. **Nunca en texto plano** - Imposible recuperar la key original
3. **Solo visible al crear** - Se muestra una sola vez al generarla

### Validación

El flujo de autenticación es:

1. Cliente envía API Key en header `X-API-Key`
2. Sistema busca todas las keys activas
3. Verifica el hash contra cada una (bcrypt.verify)
4. Comprueba que no esté expirada
5. Actualiza `last_used_at` y `request_count`
6. Permite o deniega el acceso

---

## Troubleshooting

### Error: "Import sqlalchemy could not be resolved"

Las dependencias no están instaladas. Ejecuta:

```bash
docker-compose down
docker-compose up --build
```

### Error: "PostgreSQL connection refused"

PostgreSQL no está disponible:

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs de PostgreSQL
docker-compose logs db

# Reiniciar servicios
docker-compose restart
```

### No puedo crear API Keys

Verifica que estés usando la Master API Key correcta:

```bash
# Ver Master Key configurada
docker-compose exec dian-api env | grep MASTER_API_KEY
```

### Las API Keys no persisten

El volumen de PostgreSQL podría no estar funcionando:

```bash
# Ver volúmenes
docker volume ls

# Recrear volumen
docker-compose down -v
docker-compose up -d
```

---

## FAQ

**Q: ¿Puedo desactivar la autenticación?**  
A: Sí, establece `API_KEY_ENABLED=false` en el `.env` (solo para desarrollo).

**Q: ¿Cómo genero una Master Key segura?**  
A: Usa `openssl rand -hex 32` o genera un UUID largo.

**Q: ¿Las API Keys expiran?**  
A: Solo si especificas `expires_at` al crearlas. Por defecto no expiran.

**Q: ¿Puedo reactivar una key revocada?**  
A: Sí, usa `PATCH /admin/api-keys/{key_id}` con `{"is_active": true}`.

**Q: ¿Cuántas API Keys puedo crear?**  
A: No hay límite, pero recomendamos una por cliente/aplicación.

---

## Recursos Adicionales

- [Swagger UI](http://localhost:8000/docs) - Documentación interactiva
- [README Docker](README_DOCKER.md) - Guía de despliegue
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - Documentación oficial
