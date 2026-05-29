"""
Modelos de base de datos SQLAlchemy
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class APIKey(Base):
    """Modelo de API Key para autenticación"""

    __tablename__ = "api_keys"

    # Identificador único
    id = Column(String(36), primary_key=True, index=True)

    # API Key hasheada (nunca almacenar en texto plano)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Información del cliente
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Estado y control
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Fechas
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    # Estadísticas de uso
    request_count = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, is_active={self.is_active})>"


class Task(Base):
    """Modelo de Tarea de descarga de documentos DIAN"""

    __tablename__ = "tasks"

    # Identificador único
    id = Column(String(36), primary_key=True, index=True)

    # Estado de la tarea
    status = Column(
        String(20), nullable=False, index=True, default="pending"
    )  # pending, running, completed, failed

    # URLs y parámetros
    token_url = Column(Text, nullable=False)
    fecha_inicio = Column(String(10), nullable=False)  # DD-MM-YYYY
    fecha_fin = Column(String(10), nullable=False)  # DD-MM-YYYY

    # Progreso
    progress = Column(Float, default=0.0, nullable=False)  # 0-100
    total_documentos = Column(Integer, default=0, nullable=False)
    descargados = Column(Integer, default=0, nullable=False)
    pagina_actual = Column(Integer, default=0, nullable=False)

    # Información adicional
    mensaje = Column(Text, nullable=True)
    download_folder = Column(String(500), nullable=True)

    # Relación con API Key (opcional)
    api_key_id = Column(String(36), nullable=True, index=True)

    # Fechas
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, status={self.status}, progress={self.progress}%)>"


class Lote(Base):
    """Modelo de Lote - procesamiento masivo por CUFE desde Excel"""

    __tablename__ = "lotes"

    id = Column(String(36), primary_key=True, index=True)
    status = Column(
        String(20), nullable=False, index=True, default="pending"
    )  # pending, running, completed, failed, partial
    filename = Column(String(500), nullable=False)
    token_url = Column(Text, nullable=False)
    fecha_inicio = Column(String(10), nullable=True)
    fecha_fin = Column(String(10), nullable=True)
    total_cufes = Column(Integer, default=0, nullable=False)
    descargados = Column(Integer, default=0, nullable=False)
    fallidos = Column(Integer, default=0, nullable=False)
    no_encontrados = Column(Integer, default=0, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    mensaje = Column(Text, nullable=True)
    download_folder = Column(String(500), nullable=True)
    api_key_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    detalles = relationship("LoteDetalle", back_populates="lote", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lote(id={self.id}, status={self.status}, descargados={self.descargados}/{self.total_cufes})>"


class LoteDetalle(Base):
    """Modelo de detalle de lote - estado por cada CUFE"""

    __tablename__ = "lote_detalles"

    id = Column(String(36), primary_key=True, index=True)
    lote_id = Column(String(36), ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False, index=True)
    cufe = Column(String(255), nullable=False, index=True)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, downloading, downloaded, failed, not_found
    download_path = Column(String(500), nullable=True)
    mensaje = Column(Text, nullable=True)
    intentos = Column(Integer, default=0, nullable=False)
    ultimo_intento = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    lote = relationship("Lote", back_populates="detalles")

    def __repr__(self):
        return f"<LoteDetalle(id={self.id}, cufe={self.cufe[:20]}..., status={self.status})>"
