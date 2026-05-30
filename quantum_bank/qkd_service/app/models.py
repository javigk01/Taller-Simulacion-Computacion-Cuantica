import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.database import Base


class SesionQKD(Base):
    __tablename__ = "sesiones_qkd"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), nullable=False, index=True)
    clave_hex = Column(String(1024), nullable=True)  # None if key was rejected
    protocolo = Column(String(20), default="BB84", nullable=False)
    n_bits = Column(Integer, nullable=False)
    qber = Column(Float, default=0.0)
    sifted_ratio = Column(Float, default=0.0)
    entropia = Column(Float, default=0.0)
    n_qubits_usados = Column(Integer, default=0)
    intercept_prob = Column(Float, default=0.0)
    seguro = Column(Boolean, default=True)
    espia_detectado = Column(Boolean, default=False)
    generado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
