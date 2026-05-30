from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Enums ────────────────────────────────────────────────────────────────────

class EstadoCuentaEnum(str, Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


class EstadoTransaccionEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"


# ── Cuenta ────────────────────────────────────────────────────────────────────

class CuentaCreate(BaseModel):
    titular: str = Field(..., min_length=3, max_length=100, examples=["Ana García"])
    saldo_inicial: Decimal = Field(default=Decimal("0.00"), ge=0, examples=[1000000.00])


class CuentaUpdate(BaseModel):
    titular: Optional[str] = Field(None, min_length=3, max_length=100)
    estado: Optional[EstadoCuentaEnum] = None


class CuentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_cuenta: str
    titular: str
    saldo: Decimal
    estado: str
    creado_en: datetime


# ── ClaveQuantica ─────────────────────────────────────────────────────────────

class ClaveQuanticaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    protocolo: str
    n_bits: int
    qber: Decimal
    entropia: Decimal
    sifted_ratio: Decimal
    n_qubits_usados: int
    seguro: str
    generado_en: datetime


class ClaveQuanticaDetalle(ClaveQuanticaResponse):
    """Extended response that also includes the raw hex key (admin use only)."""
    clave_hex: str


# ── Transaccion ───────────────────────────────────────────────────────────────

class TransaccionCreate(BaseModel):
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: Decimal = Field(..., gt=0, examples=[250000.00])
    concepto: str = Field(..., min_length=3, max_length=200, examples=["Pago cuota universitaria"])

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v


class TransaccionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: Decimal
    concepto: str
    payload_cifrado: Optional[str]
    clave_id: Optional[int]
    estado: str
    timestamp: datetime
    clave_quantica: Optional[ClaveQuanticaResponse] = None


class TransaccionDecifrada(TransaccionResponse):
    """Same as TransaccionResponse but with decrypted payload attached."""
    payload_descifrado: Optional[dict] = None


# ── Quantum key generation (standalone) ──────────────────────────────────────

class GenerarClaveRequest(BaseModel):
    n_bits: int = Field(default=128, ge=8, le=512, multiple_of=8,
                        description="Key length in bits (multiple of 8, 8–512)")


class GenerarClaveResponse(BaseModel):
    id: int
    clave_hex: str
    n_bits: int
    protocolo: str
    qber: float
    sifted_ratio: float
    entropia_shannon: float
    seguro: bool
    n_qubits_usados: int
    generado_en: datetime
