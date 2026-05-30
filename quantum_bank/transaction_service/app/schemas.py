from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EstadoCuentaEnum(str, Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


# ── Cuenta ────────────────────────────────────────────────────────────────────

class CuentaCreate(BaseModel):
    titular: str = Field(..., min_length=3, max_length=100, examples=["Ana García"])
    saldo_inicial: Decimal = Field(default=Decimal("0.00"), ge=0, examples=[5000000.00])


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


# ── Transaccion ───────────────────────────────────────────────────────────────

class TransaccionCreate(BaseModel):
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: Decimal = Field(..., gt=0, examples=[250000.00])
    concepto: str = Field(..., min_length=3, max_length=200,
                          examples=["Pago cuota universitaria"])

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
    qkd_session_id: Optional[str]
    estado: str
    timestamp: datetime


class TransaccionDecifrada(TransaccionResponse):
    """Same as TransaccionResponse but with the decrypted payload appended."""
    payload_descifrado: Optional[dict] = None
    nota_seguridad: str = (
        "La clave de cifrado fue generada vía protocolo BB84 (QKD) y "
        "nunca se almacenó en esta base de datos."
    )
