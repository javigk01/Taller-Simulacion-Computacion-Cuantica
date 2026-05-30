import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.bb84 import bb84_protocol
from app.database import Base, engine, get_db
from app.models import SesionQKD
from app.schemas import (
    ClaveResponse, EavesdropCompareResponse,
    SesionQKDMeta, SesionQKDResponse, SolicitarClaveRequest,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QKD Service — BB84 Quantum Key Distribution",
    version="1.0.0",
    description="""
## Servicio de Gestión de Claves Cuánticas (QKD)

Implementa el protocolo **BB84** de Distribución de Clave Cuántica usando
IBM Qiskit + AerSimulator (simulador estabilizador — maneja cientos de qubits en milisegundos).

### ¿Qué hace este servicio?
- Simula el protocolo BB84 entre Alice (este servicio) y Bob (el cliente).
- Genera una clave cuántico-aleatoria compartida.
- **Detecta eavesdroppers**: si Eve intercepta qubits, el QBER sube a ~25%
  y la clave es **descartada** automáticamente.
- El Transaction Service llama a este servicio para obtener una clave antes
  de cifrar cada transacción sensible con AES-256-GCM.

### Por qué lo cuántico importa
En el modelo clásico, Eve puede copiar los bits sin dejar rastro.
En BB84, medir un qubit **destruye su estado original** → el espionaje es
físicamente detectable. Esta es la garantía de seguridad de QKD.
""",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _bb84_to_db(result: dict, client_id: str) -> SesionQKD:
    return SesionQKD(
        id=str(uuid.uuid4()),
        client_id=client_id,
        clave_hex=result["clave_hex"],
        protocolo=result["protocolo"],
        n_bits=result["n_bits"],
        qber=result["qber"],
        sifted_ratio=result["sifted_ratio"],
        entropia=result["entropia_shannon"],
        n_qubits_usados=result["n_qubits_usados"],
        intercept_prob=result["intercept_prob"],
        seguro=result["seguro"],
        espia_detectado=result["espia_detectado"],
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "qkd_service", "protocol": "BB84"}


@app.post(
    "/session-key",
    response_model=SesionQKDResponse,
    status_code=201,
    tags=["QKD"],
    summary="Solicitar nueva clave de sesión vía BB84",
    description="""
Runs the full BB84 QKD simulation and returns the shared key.

**Normal flow** (`simular_espia: false`): QBER ≈ 0%, key accepted.

**Eavesdrop demo** (`simular_espia: true`): Eve intercepts all qubits,
QBER ≈ 25%, `seguro: false`, `clave_hex: null` — key discarded, transaction
service must retry.
""",
)
def solicitar_clave(req: SolicitarClaveRequest, db: Session = Depends(get_db)):
    prob = req.intercept_prob if req.simular_espia else 0.0
    result = bb84_protocol(n_bits=req.n_bits, intercept_prob=prob)

    sesion = _bb84_to_db(result, req.client_id)
    db.add(sesion)
    db.commit()
    db.refresh(sesion)

    mensaje = None
    if not result["seguro"]:
        mensaje = (
            f"ALERTA: QBER={result['qber']:.1%} ≥ 11% — posible espía detectado. "
            "Clave descartada. No proceder con la transacción."
        )
    else:
        mensaje = f"Clave establecida. QBER={result['qber']:.1%} — canal seguro."

    return SesionQKDResponse(
        **sesion.__dict__,
        mensaje=mensaje,
    )


@app.get(
    "/session-key/{session_id}",
    response_model=SesionQKDMeta,
    tags=["QKD"],
    summary="Metadatos de una sesión (sin clave)",
)
def obtener_sesion(session_id: str, db: Session = Depends(get_db)):
    s = db.query(SesionQKD).filter(SesionQKD.id == session_id).first()
    if not s:
        raise HTTPException(404, "Sesión QKD no encontrada")
    return s


@app.get(
    "/session-key/{session_id}/clave",
    response_model=ClaveResponse,
    tags=["QKD"],
    summary="Recuperar clave de una sesión (uso interno del Transaction Service)",
)
def recuperar_clave(session_id: str, db: Session = Depends(get_db)):
    s = db.query(SesionQKD).filter(SesionQKD.id == session_id).first()
    if not s:
        raise HTTPException(404, "Sesión QKD no encontrada")
    if not s.seguro or not s.clave_hex:
        raise HTTPException(403, "Esta sesión fue marcada como insegura — clave no disponible")
    return ClaveResponse(session_id=s.id, clave_hex=s.clave_hex, seguro=s.seguro)


@app.get(
    "/sessions",
    response_model=list[SesionQKDMeta],
    tags=["QKD"],
    summary="Listar todas las sesiones QKD generadas",
)
def listar_sesiones(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(SesionQKD)
        .order_by(SesionQKD.generado_en.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@app.post(
    "/demo/eavesdrop-compare",
    response_model=EavesdropCompareResponse,
    tags=["Demo — Detección de Espía"],
    summary="Comparativa BB84: canal seguro vs. canal con espía",
    description="""
Runs BB84 twice — once without Eve and once with Eve intercepting 100% of qubits.

**Purpose:** Show that eavesdropping is physically detectable via QBER.

Expected results:
- `sin_espia.qber` ≈ 0.0%  → `seguro: true`
- `con_espia.qber` ≈ 25%   → `seguro: false`, `espia_detectado: true`
""",
)
def demo_eavesdrop(n_bits: int = 64, db: Session = Depends(get_db)):
    # Run without Eve
    r_clean = bb84_protocol(n_bits=n_bits, intercept_prob=0.0)
    s_clean = _bb84_to_db(r_clean, "demo_alice")
    db.add(s_clean)

    # Run with Eve intercepting everything
    r_eve = bb84_protocol(n_bits=n_bits, intercept_prob=1.0)
    s_eve = _bb84_to_db(r_eve, "demo_alice_with_eve")
    db.add(s_eve)

    db.commit()
    db.refresh(s_clean)
    db.refresh(s_eve)

    conclusion = (
        f"Sin espía → QBER={r_clean['qber']:.1%} (seguro). "
        f"Con espía → QBER={r_eve['qber']:.1%} "
        f"({'DETECTADO — clave descartada' if r_eve['espia_detectado'] else 'no detectado'})."
    )

    return EavesdropCompareResponse(
        sin_espia=SesionQKDResponse(**s_clean.__dict__, mensaje="Canal limpio"),
        con_espia=SesionQKDResponse(
            **s_eve.__dict__,
            mensaje="Espía detectado — clave descartada" if r_eve["espia_detectado"] else "No detectado",
        ),
        conclusion=conclusion,
    )
