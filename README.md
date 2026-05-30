# Computación Cuántica — Arquitectura de Software, Javeriana

> **Temas:** Computación Cuántica · IBM Qiskit · AWS Braket · Criptografía Cuántica (BB84 QKD)
> **Caso práctico:** Sistema de transacciones bancarias cifradas con claves cuánticas

---

## Estructura del repositorio

```
.
├── quantum_bank/          # API REST bancaria con criptografía cuántica BB84
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── models.py      # SQLAlchemy: Cuenta, Transaccion, ClaveQuantica
│   │   ├── schemas.py     # Pydantic schemas
│   │   ├── database.py    # PostgreSQL connection
│   │   ├── quantum/
│   │   │   ├── bb84.py    # Protocolo BB84 QKD (IBM Qiskit + AerSimulator)
│   │   │   └── crypto.py  # Cifrado XOR/OTP con clave cuántica
│   │   └── routers/
│   │       ├── cuentas.py        # CRUD cuentas bancarias
│   │       ├── transacciones.py  # CRUD transacciones + cifrado
│   │       └── quantum_keys.py   # Generación y consulta de claves BB84
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── qiskit_demo/           # Demos de conceptos cuánticos con IBM Qiskit
│   ├── 01_superposicion.py
│   ├── 02_entrelazamiento.py
│   ├── 03_interferencia.py
│   ├── 04_grover.py
│   └── presentacion.py    # Menú interactivo
├── braket_demo/           # Demos equivalentes con AWS Braket LocalSimulator
│   ├── 01_superposicion.py
│   ├── 02_entrelazamiento.py
│   ├── 03_interferencia.py
│   ├── 04_grover.py
│   └── presentacion.py
├── requirements_qiskit.txt
└── requirements_braket.txt
```

---

## Opción A — IBM Qiskit (RECOMENDADA)

**100% gratis. Sin cuenta. Simulación local.**

```powershell
# Instalar dependencias (Python 3.12 recomendado)
pip install -r requirements_qiskit.txt

# Ejecutar menú de presentación
py qiskit_demo/presentacion.py

# O demos individuales
py qiskit_demo/01_superposicion.py
py qiskit_demo/02_entrelazamiento.py
py qiskit_demo/03_interferencia.py
py qiskit_demo/04_grover.py
```

---

## Opción B — AWS Braket (gratis con LocalSimulator)

> Requiere Python 3.12. El SDK de Braket es incompatible con Python 3.14+.

```powershell
# Crear venv con Python 3.12
py -3.12 -m venv C:\braket_venv
C:\braket_venv\Scripts\pip install -r requirements_braket.txt

# Ejecutar
C:\braket_venv\Scripts\python.exe braket_demo/presentacion.py
```

> **Costos AWS Braket:** El LocalSimulator es **gratis**. Los simuladores gestionados en la nube (SV1, TN1) y el hardware cuántico real cobran por tarea. Para esta demo, solo se usa LocalSimulator → $0.

---

## Caso práctico — QuantumBank API

### Despliegue con Docker (recomendado)

```powershell
cd quantum_bank
docker compose up -d --build
```

- API + Swagger UI: http://localhost:8000/docs
- Base de datos PostgreSQL: localhost:5432

### Despliegue local (sin Docker)

```powershell
# 1. Levantar PostgreSQL (Docker solo para la DB)
docker run -d --name qbank_db -e POSTGRES_DB=quantum_bank -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin123 -p 5432:5432 postgres:16-alpine

# 2. Instalar dependencias
cd quantum_bank
pip install -r requirements.txt

# 3. Configurar variable de entorno
copy .env.example .env

# 4. Iniciar API
uvicorn app.main:app --reload --port 8000
```

---

## Flujo de una transacción con criptografía cuántica

```
POST /transacciones
        │
        ├─ 1. Valida cuentas y saldo
        │
        ├─ 2. Ejecuta protocolo BB84 (Qiskit + AerSimulator stabilizer)
        │      Alice prepara N qubits en bases aleatorias Z/X
        │      Bob mide en bases aleatorias
        │      Sifting: conservar bits donde bases coinciden
        │      → Clave de 128 bits cuántico-aleatoria
        │
        ├─ 3. Cifra payload con la clave (XOR/OTP)
        │      {"monto": "...", "concepto": "...", "origen": "...", "destino": "..."}
        │
        ├─ 4. Transfiere saldo entre cuentas
        │
        └─ 5. Persiste: Transaccion + ClaveQuantica en PostgreSQL

GET /transacciones/{id}/descifrar
        └─ Recupera la clave BB84 y descifra el payload en tiempo real
```

---

## Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/cuentas` | Listar cuentas |
| POST | `/cuentas` | Crear cuenta |
| GET | `/cuentas/{id}` | Obtener cuenta |
| PUT | `/cuentas/{id}` | Actualizar cuenta |
| DELETE | `/cuentas/{id}` | Desactivar cuenta |
| GET | `/transacciones` | Listar transacciones |
| POST | `/transacciones` | **Crear transacción cifrada con BB84** |
| GET | `/transacciones/{id}` | Obtener transacción |
| GET | `/transacciones/{id}/descifrar` | Ver payload descifrado |
| GET | `/quantum-keys` | Listar claves cuánticas generadas |
| GET | `/quantum-keys/{id}` | Ver clave completa |
| POST | `/quantum-keys/generate` | **Generar clave BB84 (demo standalone)** |

Documentación interactiva completa en `/docs` (Swagger UI).

---

## Prueba rápida con curl / Postman

```bash
# 1. Crear dos cuentas
curl -X POST http://localhost:8000/cuentas \
  -H "Content-Type: application/json" \
  -d '{"titular": "Ana García", "saldo_inicial": 5000000}'

curl -X POST http://localhost:8000/cuentas \
  -H "Content-Type: application/json" \
  -d '{"titular": "Carlos López", "saldo_inicial": 1000000}'

# 2. Transferir con cifrado cuántico
curl -X POST http://localhost:8000/transacciones \
  -H "Content-Type: application/json" \
  -d '{"cuenta_origen_id": 1, "cuenta_destino_id": 2, "monto": 250000, "concepto": "Pago cuota universitaria"}'

# 3. Ver payload cifrado
curl http://localhost:8000/transacciones/1

# 4. Descifrar payload
curl http://localhost:8000/transacciones/1/descifrar

# 5. Ver clave BB84 generada
curl http://localhost:8000/quantum-keys/1
```

---

## Demos de conceptos cuánticos

| Demo | Concepto | Circuito |
|------|----------|---------|
| 01 | Superposición | `H \| M` |
| 02 | Entrelazamiento | Bell State: `H · CNOT` |
| 03 | Interferencia | `H · H = I` |
| 04 | Algoritmo de Grover | Oracle + Difusor (O(√N)) |

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| API REST | FastAPI + Uvicorn (Python 3.12) |
| ORM / Base de datos | SQLAlchemy 2.0 + PostgreSQL 16 |
| Validación | Pydantic v2 |
| Motor cuántico | IBM Qiskit 1.3 + Qiskit Aer 0.15 |
| Simulador alternativo | AWS Braket LocalSimulator |
| Cifrado | XOR/OTP con clave cuántica BB84 |
| Contenerización | Docker + Docker Compose |
| Documentación API | Swagger UI (OpenAPI 3.1) |

---

## Parar y limpiar

```powershell
cd quantum_bank
docker compose down -v   # elimina contenedores y volumen de la DB
```
