from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import cuentas, transacciones

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transaction Service — QuantumBank",
    version="1.0.0",
    description="""
## Servicio de Transacciones Bancarias (Quantum-Ready)

API clásica de pagos que integra **criptografía cuántica** para proteger
los campos sensibles de cada transacción.

### Arquitectura de microservicios

```
┌─────────────────────┐        BB84 QKD        ┌──────────────────────┐
│  Transaction Service│ ──POST /session-key──> │     QKD Service      │
│   (este servicio)   │ <── clave 128-bit ───  │  (Qiskit + Aer BB84) │
│   Puerto 8000       │                        │   Puerto 8001        │
└────────┬────────────┘                        └──────────────────────┘
         │  AES-256-GCM (payload cifrado)
         ▼
   ┌─────────────┐
   │  PostgreSQL │  ← almacena payload cifrado + qkd_session_id (no la clave)
   └─────────────┘
```

### Rol de cada tecnología
- **BB84 (QKD Service)**: genera la clave de forma cuántico-aleatoria e
  intercambia solo los parámetros públicos. La clave nunca viaja sin protección.
- **AES-256-GCM (este servicio)**: cifra el payload con autenticación de integridad.
  Si el ciphertext es manipulado, el descifrado falla con `InvalidTag`.
- **PostgreSQL**: almacena el ciphertext y la referencia a la sesión QKD,
  pero **nunca la clave en sí**.
""",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(cuentas.router)
app.include_router(transacciones.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Transaction Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "encryption": "AES-256-GCM",
        "key_exchange": "BB84 QKD (via qkd_service:8001)",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
