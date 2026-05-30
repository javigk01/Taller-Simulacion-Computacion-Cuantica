import json
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClaveQuantica, Cuenta, EstadoCuenta, EstadoTransaccion, Transaccion
from app.quantum.bb84 import generar_clave_bb84
from app.quantum.crypto import cifrar_payload, descifrar_payload
from app.schemas import (
    TransaccionCreate, TransaccionDecifrada, TransaccionResponse,
)

router = APIRouter(prefix="/transacciones", tags=["Transacciones"])


def _get_cuenta_activa(db: Session, cuenta_id: int) -> Cuenta:
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail=f"Cuenta {cuenta_id} no encontrada")
    if cuenta.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(status_code=400, detail=f"Cuenta {cuenta_id} está inactiva")
    return cuenta


@router.get("/", response_model=list[TransaccionResponse], summary="Listar transacciones")
def listar_transacciones(
    skip: int = 0,
    limit: int = 50,
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
    summary="Crear transacción cifrada con clave cuántica BB84",
    description="""
Proceso completo de transferencia con criptografía cuántica:
1. Valida las cuentas y el saldo disponible.
2. Genera una clave cuántica usando el protocolo BB84 (IBM Qiskit + AerSimulator).
3. Cifra los detalles de la transacción (monto + concepto) con la clave cuántica (XOR/OTP).
4. Registra la clave cuántica y el payload cifrado.
5. Transfiere el saldo y marca la transacción como COMPLETADA.
""",
)
def crear_transaccion(datos: TransaccionCreate, db: Session = Depends(get_db)):
    if datos.cuenta_origen_id == datos.cuenta_destino_id:
        raise HTTPException(
            status_code=400, detail="La cuenta origen y destino no pueden ser la misma"
        )

    origen = _get_cuenta_activa(db, datos.cuenta_origen_id)
    destino = _get_cuenta_activa(db, datos.cuenta_destino_id)

    if Decimal(str(origen.saldo)) < datos.monto:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente. Disponible: {origen.saldo}, requerido: {datos.monto}",
        )

    # ── Step 1: Generate quantum key via BB84 ────────────────────────────────
    bb84_result = generar_clave_bb84(n_bits=128)

    clave = ClaveQuantica(
        clave_hex=bb84_result["clave_hex"],
        protocolo=bb84_result["protocolo"],
        n_bits=bb84_result["n_bits"],
        qber=Decimal(str(bb84_result["qber"])),
        entropia=Decimal(str(bb84_result["entropia_shannon"])),
        sifted_ratio=Decimal(str(bb84_result["sifted_ratio"])),
        n_qubits_usados=bb84_result["n_qubits_usados"],
        seguro=str(bb84_result["seguro"]),
    )
    db.add(clave)
    db.flush()  # get clave.id without committing

    # ── Step 2: Encrypt transaction payload ──────────────────────────────────
    payload = {
        "monto": str(datos.monto),
        "concepto": datos.concepto,
        "origen": origen.numero_cuenta,
        "destino": destino.numero_cuenta,
    }
    payload_hex = cifrar_payload(payload, bb84_result["clave_hex"])

    # ── Step 3: Create transaction record ────────────────────────────────────
    txn = Transaccion(
        cuenta_origen_id=datos.cuenta_origen_id,
        cuenta_destino_id=datos.cuenta_destino_id,
        monto=datos.monto,
        concepto=datos.concepto,
        payload_cifrado=payload_hex,
        clave_id=clave.id,
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


@router.get(
    "/{txn_id}",
    response_model=TransaccionResponse,
    summary="Obtener transacción por ID",
)
def obtener_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return txn


@router.get(
    "/{txn_id}/descifrar",
    response_model=TransaccionDecifrada,
    summary="Descifrar payload de una transacción",
    description="Returns the transaction with its encrypted payload decrypted using the stored quantum key.",
)
def descifrar_transaccion(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    payload_dec = None
    if txn.payload_cifrado and txn.clave_quantica:
        payload_dec = descifrar_payload(txn.payload_cifrado, txn.clave_quantica.clave_hex)

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
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    if txn.estado != EstadoTransaccion.PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar transacciones en estado PENDIENTE",
        )
    db.delete(txn)
    db.commit()
