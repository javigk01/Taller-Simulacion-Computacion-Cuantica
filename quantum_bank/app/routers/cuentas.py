import random
import string
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cuenta, EstadoCuenta
from app.schemas import CuentaCreate, CuentaResponse, CuentaUpdate

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


def _generar_numero_cuenta() -> str:
    """Generates a unique 16-digit account number."""
    return "".join(random.choices(string.digits, k=16))


@router.get("/", response_model=list[CuentaResponse], summary="Listar todas las cuentas")
def listar_cuentas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Cuenta).offset(skip).limit(limit).all()


@router.post(
    "/",
    response_model=CuentaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta bancaria",
)
def crear_cuenta(datos: CuentaCreate, db: Session = Depends(get_db)):
    numero = _generar_numero_cuenta()
    # Ensure uniqueness
    while db.query(Cuenta).filter(Cuenta.numero_cuenta == numero).first():
        numero = _generar_numero_cuenta()

    cuenta = Cuenta(
        numero_cuenta=numero,
        titular=datos.titular,
        saldo=datos.saldo_inicial,
        estado=EstadoCuenta.ACTIVA,
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.get("/{cuenta_id}", response_model=CuentaResponse, summary="Obtener cuenta por ID")
def obtener_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta


@router.put("/{cuenta_id}", response_model=CuentaResponse, summary="Actualizar cuenta")
def actualizar_cuenta(
    cuenta_id: int, datos: CuentaUpdate, db: Session = Depends(get_db)
):
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    if datos.titular is not None:
        cuenta.titular = datos.titular
    if datos.estado is not None:
        cuenta.estado = EstadoCuenta(datos.estado.value)

    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.delete(
    "/{cuenta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar cuenta (soft delete)",
)
def desactivar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if cuenta.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(status_code=400, detail="La cuenta ya está inactiva")

    cuenta.estado = EstadoCuenta.INACTIVA
    db.commit()
