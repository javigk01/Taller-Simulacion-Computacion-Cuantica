from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import cuentas, quantum_keys, transacciones

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QuantumBank API",
    version="1.0.0",
    description="""
## Sistema de Transacciones Bancarias con Criptografía Cuántica

Este sistema utiliza el **protocolo BB84 de Distribución de Clave Cuántica (QKD)**
para proteger las transacciones bancarias.

### Flujo de una transacción segura:
1. Se valida la cuenta origen y el saldo disponible.
2. Se ejecuta el protocolo **BB84** en un simulador cuántico (IBM Qiskit + AerSimulator).
3. Se genera una clave cuántica-aleatoria de 128 bits.
4. Los detalles de la transacción se **cifran con la clave cuántica** (XOR/OTP).
5. Se transfiere el saldo y se almacena el payload cifrado.

### Entidades:
- **Cuentas** — cuentas bancarias con CRUD completo.
- **Transacciones** — transferencias cifradas cuánticamente.
- **Claves Cuánticas** — registro de cada clave BB84 generada.

### Stack tecnológico:
- FastAPI + SQLAlchemy + PostgreSQL
- IBM Qiskit 1.x + Qiskit Aer (AerSimulator stabilizer)
- Docker + Docker Compose
""",
    contact={"name": "QuantumBank — Arquitectura de Software, Javeriana"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cuentas.router)
app.include_router(transacciones.router)
app.include_router(quantum_keys.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "QuantumBank API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "quantum_protocol": "BB84 QKD (IBM Qiskit)",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
