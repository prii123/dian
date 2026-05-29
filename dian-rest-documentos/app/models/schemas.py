"""
Schemas de Pydantic para validación de datos
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Request para crear una tarea de descarga"""

    token_url: str = Field(
        ..., description="URL completa con el token de autenticación de DIAN"
    )
    fecha_inicio: str = Field(
        ...,
        description="Fecha inicio en formato DD-MM-YYYY",
        pattern=r"^\d{2}-\d{2}-\d{4}$",
    )
    fecha_fin: str = Field(
        ...,
        description="Fecha fin en formato DD-MM-YYYY",
        pattern=r"^\d{2}-\d{2}-\d{4}$",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "token_url": "https://catalogo-vpfe.dian.gov.co/User/AuthToken?pk=xxx&rk=yyy&token=zzz",
                "fecha_inicio": "11-04-2026",
                "fecha_fin": "12-04-2026",
            }
        }


class TaskStatus(BaseModel):
    """Estado de una tarea"""

    task_id: str
    status: str = Field(..., description="Estado: pending, running, completed, failed")
    progress: float = Field(..., ge=0, le=100, description="Progreso en porcentaje")
    total_documentos: int = Field(..., ge=0)
    descargados: int = Field(..., ge=0)
    pagina_actual: int = Field(..., ge=0)
    mensaje: str
    created_at: str
    updated_at: str
    download_folder: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None


class TaskCreateResponse(BaseModel):
    """Respuesta al crear una tarea"""

    task_id: str
    mensaje: str
    status: str


class FileInfo(BaseModel):
    """Información de un archivo"""

    nombre: str
    tamaño_kb: float
    tipo: str


class FileListResponse(BaseModel):
    """Listado de archivos"""

    task_id: str
    filtro_tipo: Optional[str] = None
    archivos: List[FileInfo]
    total: int


class TaskListResponse(BaseModel):
    """Listado de tareas de un usuario"""

    total: int
    tareas: List[TaskStatus]


class HealthResponse(BaseModel):
    """Respuesta del health check"""

    status: str
    timestamp: str
    tareas_activas: int
    version: str


# =====================================================
# Schemas para API Keys
# =====================================================


class ApiKeyCreate(BaseModel):
    """Request para crear una nueva API Key"""

    name: str = Field(
        ..., min_length=3, max_length=255, description="Nombre descriptivo del cliente"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Descripción opcional"
    )
    expires_at: Optional[str] = Field(
        None, description="Fecha de expiración (ISO format) - opcional"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Cliente ABC Corp",
                "description": "API key para cliente ABC - Proyecto DIAN",
                "expires_at": None,
            }
        }


class ApiKeyResponse(BaseModel):
    """Respuesta al crear una API Key (incluye la key en texto plano SOLO al crear)"""

    id: str
    key: str = Field(
        ...,
        description="⚠️ API Key en texto plano - GUARDAR EN LUGAR SEGURO - Solo se muestra una vez",
    )
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    expires_at: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "name": "Cliente ABC Corp",
                "description": "API key para cliente ABC",
                "is_active": True,
                "created_at": "2026-04-13T10:30:00",
                "expires_at": None,
            }
        }


class ApiKeyInfo(BaseModel):
    """Información de una API Key (sin mostrar la key completa)"""

    id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    request_count: int

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    """Listado de API Keys"""

    total: int
    keys: List[ApiKeyInfo]


class ApiKeyUpdate(BaseModel):
    """Update de una API Key"""

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ApiKeyValidation(BaseModel):
    """Información de validación de API Key"""

    api_key_id: str
    name: str
    is_valid: bool
    message: str
