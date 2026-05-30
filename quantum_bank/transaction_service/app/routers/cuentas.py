import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cuenta, EstadoCuenta
from app.schemas import CuentaCreate, CuentaResponse, CuentaUpdate

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


def _generar_numero_cuenta() -> str:
    return "".join(random.choices(string.digits, k=16))


@router.get("/", response_model=list[CuentaResponse], summary="Listar cuentas")
def listar_cuentas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Cuenta).offset(skip).limit(limit).all()


@router.post("/", response_model=CuentaResponse, status_code=status.HTTP_201_CREATED,
             summary="Crear cuenta bancaria")
def crear_cuenta(datos: CuentaCreate, db: Session = Depends(get_db)):
    numero = _generar_numero_cuenta()
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


@router.get("/{cuenta_id}", response_model=CuentaResponse, summary="Obtener cuenta")
def obtener_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    return c


@router.put("/{cuenta_id}", response_model=CuentaResponse, summary="Actualizar cuenta")
def actualizar_cuenta(cuenta_id: int, datos: CuentaUpdate, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    if datos.titular is not None:
        c.titular = datos.titular
    if datos.estado is not None:
        c.estado = EstadoCuenta(datos.estado.value)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Desactivar cuenta (soft delete)")
def desactivar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    if c.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(400, "La cuenta ya está inactiva")
    c.estado = EstadoCuenta.INACTIVA
    db.commit()
