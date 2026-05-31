from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crypto import cifrar_aes_gcm, descifrar_aes_gcm
from app.database import get_db
from app.models import Cuenta, EstadoCuenta, EstadoTransaccion, Transaccion
from app.qkd_client import QKDServiceError, recuperar_clave, solicitar_clave
from app.schemas import (
    TransaccionCreate, TransaccionDecifrada, TransaccionResponse, TransaccionUpdate,
)

router = APIRouter(prefix="/transacciones", tags=["Transacciones"])


def _get_cuenta_activa(db: Session, cuenta_id: int) -> Cuenta:
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, f"Cuenta {cuenta_id} no encontrada")
    if c.estado == EstadoCuenta.ELIMINADA:
        raise HTTPException(410, f"Cuenta {cuenta_id} fue eliminada permanentemente")
    if c.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(400, f"Cuenta {cuenta_id} está inactiva")
    return c


def _load_cuentas(db: Session, *ids: int) -> dict[int, Cuenta]:
    """Load a set of account IDs into a dict. SQLAlchemy identity map ensures
    that the same ID always returns the same Python object within the session."""
    result: dict[int, Cuenta] = {}
    for cid in set(ids):
        c = db.query(Cuenta).filter(Cuenta.id == cid).first()
        if not c:
            raise HTTPException(404, f"Cuenta {cid} no encontrada")
        result[cid] = c
    return result


def _cifrar_con_nueva_clave(payload: dict) -> tuple[str, str]:
    """Request a fresh BB84 key, encrypt the payload, return (payload_hex, session_id)."""
    try:
        qkd_session = solicitar_clave(client_id="transaction_service", n_bits=128)
    except QKDServiceError as e:
        raise HTTPException(503, f"QKD Service error: {e}")
    return cifrar_aes_gcm(payload, qkd_session["clave_hex"]), qkd_session["id"]


# ── Endpoints ────────────────────────────────────────────────────────────────

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
2. Llama al **QKD Service** — ejecuta BB84 en Qiskit AerSimulator, devuelve clave 128 bits.
3. Cifra los campos sensibles con **AES-256-GCM** usando esa clave.
4. Almacena solo el `qkd_session_id` (no la clave) en la base de datos.
5. Transfiere el saldo y marca la transacción como COMPLETADA.
""",
)
def crear_transaccion(datos: TransaccionCreate, db: Session = Depends(get_db)):
    if datos.cuenta_origen_id == datos.cuenta_destino_id:
        raise HTTPException(400, "Cuenta origen y destino no pueden ser iguales")

    origen = _get_cuenta_activa(db, datos.cuenta_origen_id)
    destino = _get_cuenta_activa(db, datos.cuenta_destino_id)

    if Decimal(str(origen.saldo)) < datos.monto:
        raise HTTPException(
            400, f"Saldo insuficiente. Disponible: {origen.saldo}, requerido: {datos.monto}"
        )

    payload = {
        "monto": str(datos.monto),
        "concepto": datos.concepto,
        "cuenta_origen": origen.numero_cuenta,
        "cuenta_destino": destino.numero_cuenta,
    }
    payload_cifrado, session_id = _cifrar_con_nueva_clave(payload)

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


@router.put(
    "/{txn_id}",
    response_model=TransaccionResponse,
    summary="Modificar transacción con ajuste automático de saldos",
    description="""
Permite cambiar la cuenta origen, la cuenta destino, el monto o el concepto.

**Ajuste de saldos (solo si estado = COMPLETADA):**
1. Se revierten los saldos al estado anterior a la transacción original.
2. Se validan los nuevos valores (saldo suficiente en la nueva cuenta origen).
3. Se aplican los nuevos movimientos de saldo.
4. Se re-cifra el payload con una nueva clave BB84.

Si la cuenta destino original no tiene saldo suficiente para ser debitada
(por ejemplo, porque ya gastó el dinero recibido), la operación falla con 400.
""",
)
def actualizar_transaccion(
    txn_id: int, datos: TransaccionUpdate, db: Session = Depends(get_db)
):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "Transacción no encontrada")
    if txn.estado == EstadoTransaccion.FALLIDA:
        raise HTTPException(400, "No se puede modificar una transacción en estado FALLIDA")

    # Block edits if either account was permanently deleted
    for cid, role in [(txn.cuenta_origen_id, "origen"), (txn.cuenta_destino_id, "destino")]:
        c = db.query(Cuenta).filter(Cuenta.id == cid).first()
        if c and c.estado == EstadoCuenta.ELIMINADA:
            raise HTTPException(
                403,
                f"Esta transacción es de solo lectura: la cuenta {role} (id={cid}) "
                "fue eliminada permanentemente. Solo se puede consultar el registro histórico.",
            )

    # Resolve final values (keep originals when not provided)
    new_origen_id  = datos.cuenta_origen_id  or txn.cuenta_origen_id
    new_destino_id = datos.cuenta_destino_id or txn.cuenta_destino_id
    new_monto      = datos.monto             or Decimal(str(txn.monto))
    new_concepto   = datos.concepto          or txn.concepto

    if new_origen_id == new_destino_id:
        raise HTTPException(400, "Cuenta origen y destino no pueden ser iguales")

    # Load all accounts involved (old + new) in one pass
    cuentas = _load_cuentas(
        db,
        txn.cuenta_origen_id, txn.cuenta_destino_id,
        new_origen_id, new_destino_id,
    )

    # Validate new accounts are active
    for cid in (new_origen_id, new_destino_id):
        if cuentas[cid].estado == EstadoCuenta.INACTIVA:
            raise HTTPException(400, f"La cuenta {cid} está inactiva")

    if txn.estado == EstadoTransaccion.COMPLETADA:
        old_monto = Decimal(str(txn.monto))

        # Guard: destination must have enough to be reversed
        if Decimal(str(cuentas[txn.cuenta_destino_id].saldo)) < old_monto:
            raise HTTPException(
                400,
                f"La cuenta destino (id={txn.cuenta_destino_id}) no tiene saldo suficiente "
                f"para revertir la transacción original. "
                f"Saldo actual: {cuentas[txn.cuenta_destino_id].saldo}, "
                f"monto a revertir: {old_monto}",
            )

        # Step 1 — Reverse original transfer
        cuentas[txn.cuenta_origen_id].saldo  = Decimal(str(cuentas[txn.cuenta_origen_id].saldo))  + old_monto
        cuentas[txn.cuenta_destino_id].saldo = Decimal(str(cuentas[txn.cuenta_destino_id].saldo)) - old_monto
        db.flush()  # flush so identity map reflects updated balances before the next check

        # Step 2 — Check new origin has enough (after reversal)
        if Decimal(str(cuentas[new_origen_id].saldo)) < new_monto:
            raise HTTPException(
                400,
                f"Saldo insuficiente en la cuenta origen (id={new_origen_id}). "
                f"Disponible tras revertir: {cuentas[new_origen_id].saldo}, "
                f"requerido: {new_monto}",
            )

        # Step 3 — Apply new transfer
        cuentas[new_origen_id].saldo  = Decimal(str(cuentas[new_origen_id].saldo))  - new_monto
        cuentas[new_destino_id].saldo = Decimal(str(cuentas[new_destino_id].saldo)) + new_monto

    # Re-encrypt payload with a fresh BB84 key
    payload = {
        "monto": str(new_monto),
        "concepto": new_concepto,
        "cuenta_origen": cuentas[new_origen_id].numero_cuenta,
        "cuenta_destino": cuentas[new_destino_id].numero_cuenta,
    }
    nuevo_payload_cifrado, nuevo_session_id = _cifrar_con_nueva_clave(payload)

    txn.cuenta_origen_id  = new_origen_id
    txn.cuenta_destino_id = new_destino_id
    txn.monto             = new_monto
    txn.concepto          = new_concepto
    txn.payload_cifrado   = nuevo_payload_cifrado
    txn.qkd_session_id    = nuevo_session_id

    db.commit()
    db.refresh(txn)
    return txn


@router.get(
    "/{txn_id}/descifrar",
    response_model=TransaccionDecifrada,
    summary="Descifrar payload con clave del QKD Service",
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
    summary="Eliminar transacción — revierte saldo si está COMPLETADA",
    description="""
- **PENDIENTE**: se elimina directamente (no hubo movimiento de saldo).
- **COMPLETADA**: se devuelve el monto a la cuenta origen y se debita de la
  cuenta destino antes de eliminar el registro. Si la cuenta destino no tiene
  saldo suficiente (lo gastó) la operación falla con 400.
""",
)
def eliminar_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(404, "Transacción no encontrada")

    if txn.estado == EstadoTransaccion.COMPLETADA:
        origen  = db.query(Cuenta).filter(Cuenta.id == txn.cuenta_origen_id).first()
        destino = db.query(Cuenta).filter(Cuenta.id == txn.cuenta_destino_id).first()
        monto   = Decimal(str(txn.monto))

        origen_eliminada  = not origen  or origen.estado  == EstadoCuenta.ELIMINADA
        destino_eliminada = not destino or destino.estado == EstadoCuenta.ELIMINADA

        if not origen_eliminada and not destino_eliminada:
            # Caso 1: ambas cuentas existen → revertir saldos
            if Decimal(str(destino.saldo)) < monto:
                raise HTTPException(
                    400,
                    f"La cuenta destino (id={txn.cuenta_destino_id}) no tiene saldo "
                    f"suficiente para revertir. Saldo: {destino.saldo}, requerido: {monto}",
                )
            origen.saldo  = Decimal(str(origen.saldo))  + monto
            destino.saldo = Decimal(str(destino.saldo)) - monto

        elif origen_eliminada and destino_eliminada:
            # Caso 2: ambas eliminadas → eliminar registro sin revertir (no hay cuentas que actualizar)
            pass

        else:
            # Caso 3: una existe y la otra fue eliminada → no permitir
            existente = "destino" if origen_eliminada else "origen"
            eliminada  = "origen"  if origen_eliminada else "destino"
            raise HTTPException(
                400,
                f"No se puede eliminar: la cuenta {eliminada} fue eliminada pero la "
                f"cuenta {existente} aún existe. Ambas deben estar eliminadas, o ambas "
                "deben existir para poder revertir el saldo.",
            )

    db.delete(txn)
    db.commit()
