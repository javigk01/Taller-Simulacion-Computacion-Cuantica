from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClaveQuantica
from app.quantum.bb84 import generar_clave_bb84
from app.schemas import (
    ClaveQuanticaDetalle, ClaveQuanticaResponse,
    GenerarClaveRequest, GenerarClaveResponse,
)

router = APIRouter(prefix="/quantum-keys", tags=["Criptografía Cuántica BB84"])


@router.get(
    "/",
    response_model=list[ClaveQuanticaResponse],
    summary="Listar claves cuánticas generadas",
)
def listar_claves(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(ClaveQuantica)
        .order_by(ClaveQuantica.generado_en.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{clave_id}",
    response_model=ClaveQuanticaDetalle,
    summary="Obtener clave cuántica (incluye hex completo)",
)
def obtener_clave(clave_id: int, db: Session = Depends(get_db)):
    clave = db.query(ClaveQuantica).filter(ClaveQuantica.id == clave_id).first()
    if not clave:
        raise HTTPException(status_code=404, detail="Clave cuántica no encontrada")
    return clave


@router.post(
    "/generate",
    response_model=GenerarClaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar nueva clave cuántica BB84 (demo standalone)",
    description="""
Runs the full BB84 QKD simulation and stores the resulting key.
Useful for demonstrating the quantum key generation independently of a transaction.

The response includes:
- **clave_hex**: The generated quantum-random key in hexadecimal.
- **qber**: Quantum Bit Error Rate (0.0 in ideal simulation = no eavesdropper).
- **sifted_ratio**: Fraction of qubits kept after basis sifting (~0.50).
- **entropia_shannon**: Bits of entropy per bit (ideal = 1.0).
- **seguro**: True if QBER < 11% (BB84 security threshold).
""",
)
def generar_clave(req: GenerarClaveRequest, db: Session = Depends(get_db)):
    resultado = generar_clave_bb84(n_bits=req.n_bits)

    clave = ClaveQuantica(
        clave_hex=resultado["clave_hex"],
        protocolo=resultado["protocolo"],
        n_bits=resultado["n_bits"],
        qber=Decimal(str(resultado["qber"])),
        entropia=Decimal(str(resultado["entropia_shannon"])),
        sifted_ratio=Decimal(str(resultado["sifted_ratio"])),
        n_qubits_usados=resultado["n_qubits_usados"],
        seguro=str(resultado["seguro"]),
    )
    db.add(clave)
    db.commit()
    db.refresh(clave)

    return GenerarClaveResponse(
        id=clave.id,
        clave_hex=clave.clave_hex,
        n_bits=clave.n_bits,
        protocolo=clave.protocolo,
        qber=float(clave.qber),
        sifted_ratio=float(clave.sifted_ratio),
        entropia_shannon=float(clave.entropia),
        seguro=resultado["seguro"],
        n_qubits_usados=clave.n_qubits_usados,
        generado_en=clave.generado_en,
    )
