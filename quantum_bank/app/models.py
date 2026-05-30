import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class EstadoCuenta(str, enum.Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


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
    estado = Column(
        Enum(EstadoCuenta, name="estadocuenta"),
        default=EstadoCuenta.ACTIVA,
        nullable=False,
    )
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    transacciones_origen = relationship(
        "Transaccion",
        foreign_keys="Transaccion.cuenta_origen_id",
        back_populates="cuenta_origen",
    )
    transacciones_destino = relationship(
        "Transaccion",
        foreign_keys="Transaccion.cuenta_destino_id",
        back_populates="cuenta_destino",
    )


class ClaveQuantica(Base):
    __tablename__ = "claves_quanticas"

    id = Column(Integer, primary_key=True, index=True)
    clave_hex = Column(String(512), nullable=False)
    protocolo = Column(String(20), default="BB84", nullable=False)
    n_bits = Column(Integer, default=128, nullable=False)
    qber = Column(Numeric(6, 4), default=Decimal("0.0000"))
    entropia = Column(Numeric(10, 6), default=Decimal("0.000000"))
    sifted_ratio = Column(Numeric(6, 4), default=Decimal("0.0000"))
    n_qubits_usados = Column(Integer, default=0)
    seguro = Column(String(5), default="True")
    generado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaccion = relationship(
        "Transaccion", back_populates="clave_quantica", uselist=False
    )


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    cuenta_origen_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    cuenta_destino_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    concepto = Column(String(200), nullable=False)
    payload_cifrado = Column(Text, nullable=True)
    clave_id = Column(Integer, ForeignKey("claves_quanticas.id"), nullable=True)
    estado = Column(
        Enum(EstadoTransaccion, name="estadotransaccion"),
        default=EstadoTransaccion.PENDIENTE,
        nullable=False,
    )
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    cuenta_origen = relationship(
        "Cuenta",
        foreign_keys=[cuenta_origen_id],
        back_populates="transacciones_origen",
    )
    cuenta_destino = relationship(
        "Cuenta",
        foreign_keys=[cuenta_destino_id],
        back_populates="transacciones_destino",
    )
    clave_quantica = relationship("ClaveQuantica", back_populates="transaccion")
