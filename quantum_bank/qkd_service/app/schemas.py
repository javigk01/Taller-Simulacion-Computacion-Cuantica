from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SolicitarClaveRequest(BaseModel):
    client_id: str = Field(..., examples=["transaction_service"])
    n_bits: int = Field(default=128, ge=8, le=512, multiple_of=8,
                        description="Key length in bits (8–512, multiple of 8)")
    simular_espia: bool = Field(
        default=False,
        description="If True, simulates an eavesdropper intercepting all qubits. "
                    "Expected QBER ≈ 25%, key will be rejected."
    )
    intercept_prob: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Fraction of qubits intercepted by Eve (only used when simular_espia=True)"
    )


class SesionQKDResponse(BaseModel):
    """Full response — includes the key. Returned only on POST /session-key."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    clave_hex: Optional[str]
    protocolo: str
    n_bits: int
    qber: float
    sifted_ratio: float
    entropia: float
    n_qubits_usados: int
    intercept_prob: float
    seguro: bool
    espia_detectado: bool
    generado_en: datetime
    mensaje: Optional[str] = None


class SesionQKDMeta(BaseModel):
    """Metadata only — key is NOT included. Returned on GET /session-key/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    protocolo: str
    n_bits: int
    qber: float
    sifted_ratio: float
    entropia: float
    n_qubits_usados: int
    intercept_prob: float
    seguro: bool
    espia_detectado: bool
    generado_en: datetime


class ClaveResponse(BaseModel):
    """Used internally by the transaction service to retrieve a stored key."""
    session_id: str
    clave_hex: str
    seguro: bool


class EavesdropCompareResponse(BaseModel):
    """Side-by-side comparison: normal BB84 vs. BB84 with Eve."""
    sin_espia: SesionQKDResponse
    con_espia: SesionQKDResponse
    conclusion: str
