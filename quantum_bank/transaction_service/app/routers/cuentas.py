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


def _get_or_404(db: Session, cuenta_id: int) -> Cuenta:
    c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    return c


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
    return _get_or_404(db, cuenta_id)


@router.put(
    "/{cuenta_id}",
    response_model=CuentaResponse,
    summary="Actualizar titular o reactivar cuenta",
    description="""
Permite:
- Cambiar el `titular` de la cuenta.
- **Reactivar** una cuenta INACTIVA enviando `{"estado": "ACTIVA"}`.

No permite cambiar a `ELIMINADA` desde este endpoint
(use `DELETE /cuentas/{id}/permanente` para eso).
""",
)
def actualizar_cuenta(cuenta_id: int, datos: CuentaUpdate, db: Session = Depends(get_db)):
    c = _get_or_404(db, cuenta_id)
    if c.estado == EstadoCuenta.ELIMINADA:
        raise HTTPException(400, "La cuenta fue eliminada permanentemente y no puede modificarse")
    if datos.estado is not None and datos.estado.value == EstadoCuenta.ELIMINADA:
        raise HTTPException(400, "Use DELETE /cuentas/{id}/permanente para eliminar permanentemente")
    if datos.titular is not None:
        c.titular = datos.titular
    if datos.estado is not None:
        c.estado = datos.estado.value
    db.commit()
    db.refresh(c)
    return c


@router.delete(
    "/{cuenta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar cuenta (ACTIVA → INACTIVA)",
)
def desactivar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    c = _get_or_404(db, cuenta_id)
    if c.estado == EstadoCuenta.ELIMINADA:
        raise HTTPException(400, "La cuenta fue eliminada permanentemente")
    if c.estado == EstadoCuenta.INACTIVA:
        raise HTTPException(400, "La cuenta ya está inactiva. Use PUT para reactivarla")
    c.estado = EstadoCuenta.INACTIVA
    db.commit()


@router.delete(
    "/{cuenta_id}/permanente",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cuenta permanentemente",
    description="""
Marca la cuenta como `ELIMINADA` (no se borra la fila para conservar el historial de transacciones).

Efectos:
- La cuenta desaparece de los listados activos y no puede recibir ni enviar transferencias.
- Sus transacciones históricas siguen siendo visibles pero **no editables ni eliminables**
  (a menos que la otra cuenta involucrada también haya sido eliminada).
""",
)
def eliminar_cuenta_permanente(cuenta_id: int, db: Session = Depends(get_db)):
    c = _get_or_404(db, cuenta_id)
    if c.estado == EstadoCuenta.ELIMINADA:
        raise HTTPException(400, "La cuenta ya fue eliminada permanentemente")
    c.estado = EstadoCuenta.ELIMINADA
    db.commit()
