from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crypto import cifrar_aes_gcm, descifrar_aes_gcm
from app.database import get_db
from app.models import Cuenta, EstadoCuenta, EstadoTransaccion, Transaccion
from app.qkd_client import QKDServiceError, recuperar_clave, solicitar_clave
from app.schemas import (
    TransaccionCreate, TransaccionDecifrada, TransaccionResponse,
)

router = APIRouter(prefix="/transacciones", tags=["Transacciones"])


def _get_cuenta_activa(db: Session, cuenta_id: int) -> Cuenta:
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, f"Cuenta {cuenta_id} no encontrada")
    if c.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(400, f"Cuenta {cuenta_id} está inactiva")
    return c


@router.get("/", response_model=list[TransaccionResponse], summary="Listar transacciones")
def listar_transacciones(
    skip: int = 0, limit: int = 50,
    cuenta_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Transaccion)
    if cuenta_id is not None:
        q = q.filter(
            (Transaccion.cuenta_origen_id == cuenta_id)
            | (Transaccion.cuenta_destino_id == cuenta_id)
        )
    return q.order_by(Transaccion.timestamp.desc()).offset(skip).limit(limit).all()


@router.post(
    "/",
    response_model=TransaccionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear transacción cifrada con clave cuántica (BB84 + AES-256-GCM)",
    description="""
**Flujo completo de una transferencia quantum-safe:**

1. Valida cuentas origen/destino y saldo disponible.
2. Llama al **QKD Service** (POST /session-key) — ejecuta el protocolo BB84
   en IBM Qiskit + AerSimulator y devuelve una clave de 128 bits cuántico-aleatoria.
3. Cifra los campos sensibles (`monto`, `concepto`, números de cuenta) con
   **AES-256-GCM** usando la clave del paso anterior.
4. Almacena solo el `qkd_session_id` (no la clave) en la base de datos.
5. Transfiere el saldo y marca la transacción como COMPLETADA.

> La clave vive únicamente en el QKD Service.
> Si se necesita descifrar, el Transaction Service la solicita bajo demanda.
""",
)
def crear_transaccion(datos: TransaccionCreate, db: Session = Depends(get_db)):
    if datos.cuenta_origen_id == datos.cuenta_destino_id:
        raise HTTPException(400, "Cuenta origen y destino no pueden ser iguales")

    origen = _get_cuenta_activa(db, datos.cuenta_origen_id)
    destino = _get_cuenta_activa(db, datos.cuenta_destino_id)

    if Decimal(str(origen.saldo)) < datos.monto:
        raise HTTPException(
            400,
            f"Saldo insuficiente. Disponible: {origen.saldo}, requerido: {datos.monto}",
        )

    # ── Step 1: Request quantum session key from QKD service ─────────────────
    try:
        qkd_session = solicitar_clave(client_id="transaction_service", n_bits=128)
    except QKDServiceError as e:
        raise HTTPException(503, f"QKD Service error: {e}")

    session_id = qkd_session["id"]
    clave_hex = qkd_session["clave_hex"]

    # ── Step 2: Encrypt sensitive payload with AES-256-GCM ───────────────────
    payload = {
        "monto": str(datos.monto),
        "concepto": datos.concepto,
        "cuenta_origen": origen.numero_cuenta,
        "cuenta_destino": destino.numero_cuenta,
        "qkd_qber": qkd_session["qber"],
    }
    payload_cifrado = cifrar_aes_gcm(payload, clave_hex)

    # ── Step 3: Persist transaction (key is NOT stored here) ─────────────────
    txn = Transaccion(
        cuenta_origen_id=datos.cuenta_origen_id,
        cuenta_destino_id=datos.cuenta_destino_id,
        monto=datos.monto,
        concepto=datos.concepto,
        payload_cifrado=payload_cifrado,
        qkd_session_id=session_id,
        estado=EstadoTransaccion.PENDIENTE,
    )
    db.add(txn)
    db.flush()

    # ── Step 4: Transfer funds ────────────────────────────────────────────────
    origen.saldo = Decimal(str(origen.saldo)) - datos.monto
    destino.saldo = Decimal(str(destino.saldo)) + datos.monto
    txn.estado = EstadoTransaccion.COMPLETADA

    db.commit()
    db.refresh(txn)
    return txn


@router.get("/{txn_id}", response_model=TransaccionResponse, summary="Obtener transacción")
def obtener_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "Transacción no encontrada")
    return txn


@router.get(
    "/{txn_id}/descifrar",
    response_model=TransaccionDecifrada,
    summary="Descifrar payload — recupera clave del QKD Service y aplica AES-256-GCM",
    description="""
Retrieves the QKD session key from the QKD Service and uses it to decrypt
the AES-256-GCM payload of the transaction.

This demonstrates the separation of concerns:
- The **Transaction DB** stores only the encrypted payload and the session ID.
- The **QKD Service** holds the key.
- Neither database alone is sufficient to read the transaction details.
""",
)
def descifrar_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "Transacción no encontrada")

    payload_dec = None
    if txn.payload_cifrado and txn.qkd_session_id:
        try:
            clave_hex = recuperar_clave(txn.qkd_session_id)
            payload_dec = descifrar_aes_gcm(txn.payload_cifrado, clave_hex)
        except QKDServiceError as e:
            raise HTTPException(503, f"No se pudo recuperar la clave del QKD Service: {e}")

    response = TransaccionDecifrada.model_validate(txn)
    response.payload_descifrado = payload_dec
    return response


@router.delete(
    "/{txn_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar transacción (solo PENDIENTE)",
)
def eliminar_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "Transacción no encontrada")
    if txn.estado != EstadoTransaccion.PENDIENTE:
        raise HTTPException(400, "Solo se pueden eliminar transacciones PENDIENTE")
    db.delete(txn)
    db.commit()
