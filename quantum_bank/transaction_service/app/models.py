import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class EstadoCuenta(str, enum.Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"
    ELIMINADA = "ELIMINADA"


class EstadoTransaccion(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"


class Cuenta(Base):
    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True, index=True)
    numero_cuenta = Column(String(20), unique=True, nullable=False, index=True)
    titular = Column(String(100), nullable=False)
    saldo = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    # String instead of PostgreSQL Enum so adding new states never requires a migration
    estado = Column(String(20), default=EstadoCuenta.ACTIVA, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    transacciones_origen = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_origen_id",
        back_populates="cuenta_origen",
    )
    transacciones_destino = relationship(
        "Transaccion", foreign_keys="Transaccion.cuenta_destino_id",
        back_populates="cuenta_destino",
    )


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    cuenta_origen_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    cuenta_destino_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    concepto = Column(String(200), nullable=False)

    # AES-GCM encrypted payload: nonce ‖ ciphertext ‖ tag (hex)
    payload_cifrado = Column(Text, nullable=True)

    # Reference to the QKD session that provided the encryption key.
    # The actual key lives in the QKD Service — we never persist it here.
    qkd_session_id = Column(String(36), nullable=True, index=True)

    estado = Column(String(20), default=EstadoTransaccion.PENDIENTE, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    cuenta_origen = relationship(
        "Cuenta", foreign_keys=[cuenta_origen_id], back_populates="transacciones_origen",
    )
    cuenta_destino = relationship(
        "Cuenta", foreign_keys=[cuenta_destino_id], back_populates="transacciones_destino",
    )
