# Computación Cuántica — Arquitectura de Software

**Universidad Javeriana · Semestre 7 · 2026**

Temas: Computación Cuántica · IBM Qiskit · AWS Braket · Criptografía Cuántica (QKD BB84)

---

## ¿Qué es este proyecto?

Este repositorio contiene dos partes complementarias que juntas responden la pregunta:
**¿Cómo se aplica la computación cuántica en sistemas reales de software?**

### Parte 1 — Demos de conceptos cuánticos

Scripts interactivos que demuestran los 4 pilares de la computación cuántica
ejecutando **circuitos cuánticos reales** en simuladores locales (sin costo, sin cuenta).

Disponibles en **dos frameworks** para comparar:

| Framework | Empresa | Simulador local |
|---|---|---|
| **IBM Qiskit** | IBM | AerSimulator (método stabilizer) |
| **AWS Braket** | Amazon | LocalSimulator |

### Parte 2 — QuantumBank: sistema bancario quantum-safe

Sistema de transacciones bancarias que usa **criptografía cuántica** para
proteger los datos sensibles de cada transferencia.

La idea central: en un sistema quantum-ready, la computación cuántica no cifra
el payload directamente — su rol es **intercambiar la clave** de forma físicamente
segura (QKD). El payload lo cifra AES-256-GCM con esa clave.

> **Contexto real:** Bancos como Toshiba y ID Quantique ya despliegan QKD sobre
> fibra óptica entre sedes. Aquí simulamos el mismo protocolo (BB84) con Qiskit,
> lo que permite demostrar los conceptos sin hardware de fotónica especializado.

---

## Arquitectura del sistema bancario

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
│                                                                  │
│  ┌─────────────────┐    POST /session-key    ┌────────────────┐  │
│  │  Transaction    │ ──────────────────────► │  QKD Service   │  │
│  │  Service        │ ◄── clave 128 bits ───  │  (BB84+Qiskit) │  │
│  │  :8000          │                         │  :8001         │  │
│  │                 │  AES-256-GCM            └────────────────┘  │
│  │                 │ ──────────────────────► ┌────────────────┐  │
│  │                 │                         │  PostgreSQL    │  │
│  └────────┬────────┘                         │  :5432         │  │
│           │                                  └────────────────┘  │
│  ┌────────▼────────┐                                             │
│  │    Frontend     │                                             │
│  │  React + Vite   │                                             │
│  │  :3000          │                                             │
│  └─────────────────┘                                             │
└──────────────────────────────────────────────────────────────────┘
```

**QKD Service** (`qkd_service/`) — Solo hace una cosa: ejecutar el protocolo BB84
en Qiskit y devolver una clave cuántico-aleatoria. Detecta espías midiendo el QBER.

**Transaction Service** (`transaction_service/`) — API REST bancaria clásica.
Llama al QKD Service para obtener una clave, cifra los datos sensibles con
AES-256-GCM y transfiere el saldo. Nunca almacena la clave en su base de datos.

**Frontend** (`frontend/`) — Interfaz React con tema oscuro. Incluye:
visualización paso a paso del protocolo BB84 y demo interactiva del espía.

---

## Flujo de una transferencia segura

```
Usuario → POST /transacciones
    │
    ├─ 1. Valida cuentas y saldo disponible
    │
    ├─ 2. Transaction Service llama al QKD Service
    │       QKD Service ejecuta BB84 en Qiskit AerSimulator:
    │         · Alice prepara 384 qubits con compuertas X y H
    │         · Bob mide en bases aleatorias
    │         · Sifting: se descartan ~50% de los bits (bases no coincidentes)
    │         · QBER < 11% → canal seguro → clave de 128 bits generada
    │         · QBER ≥ 11% → espía detectado → clave descartada
    │
    ├─ 3. Transaction Service cifra el payload con AES-256-GCM
    │       (usando la clave BB84 como semilla)
    │       payload = { monto, concepto, cuenta_origen, cuenta_destino }
    │
    ├─ 4. Transfiere el saldo entre cuentas
    │
    └─ 5. Persiste en PostgreSQL:
            · payload cifrado (hex AES-GCM)
            · qkd_session_id (referencia a la clave en el QKD Service)
            · la clave NUNCA se almacena en la DB de transacciones
```

---

## Estructura del repositorio

```
.
├── quantum_bank/                    # Sistema bancario (Docker)
│   ├── qkd_service/                 # Microservicio QKD — BB84 + Qiskit
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI: /session-key, /demo/eavesdrop-compare
│   │   │   ├── bb84.py              # Protocolo BB84 con simulación de espía
│   │   │   ├── models.py            # SesionQKD (SQLite)
│   │   │   └── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── transaction_service/         # Microservicio de Transacciones
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI: /cuentas, /transacciones
│   │   │   ├── models.py            # Cuenta, Transaccion (PostgreSQL)
│   │   │   ├── crypto.py            # AES-256-GCM con clave cuántica
│   │   │   ├── qkd_client.py        # Cliente HTTP al QKD Service
│   │   │   └── routers/
│   │   │       ├── cuentas.py       # CRUD cuentas
│   │   │       └── transacciones.py # CRUD transacciones + cifrado
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── frontend/                    # Interfaz gráfica React + Vite + Tailwind
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── api.ts               # Llamadas a ambos servicios
│   │   │   └── pages/
│   │   │       ├── CuentasPage.tsx
│   │   │       ├── TransaccionesPage.tsx
│   │   │       └── QKDLabPage.tsx   # Demo interactiva del espía
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── docker-compose.yml           # Orquesta los 4 servicios
│   └── QuantumBank.postman_collection.json
│
├── qiskit_demo/                     # Demos de conceptos (IBM Qiskit)
│   ├── 01_superposicion.py
│   ├── 02_entrelazamiento.py
│   ├── 03_interferencia.py
│   ├── 04_grover.py
│   └── presentacion.py              # Menú interactivo
│
├── braket_demo/                     # Demos equivalentes (AWS Braket)
│   ├── 01_superposicion.py
│   ├── 02_entrelazamiento.py
│   ├── 03_interferencia.py
│   ├── 04_grover.py
│   └── presentacion.py
│
├── requirements_qiskit.txt
├── requirements_braket.txt
└── README.md
```

---

## Requisitos previos

| Herramienta | Versión mínima | Para qué |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 24+ | Correr el sistema bancario |
| Python | 3.12 recomendado | Correr las demos de conceptos |
| Git | cualquiera | Clonar el repositorio |

> Python 3.14 funciona con Qiskit pero **no** con AWS Braket (incompatibilidad con Pydantic v1).
> Se recomienda Python 3.12 para compatibilidad total.

---

## Despliegue — Sistema bancario (QuantumBank)

> **Un solo comando.** Docker construye y levanta los 4 servicios automáticamente.

```powershell
cd quantum_bank
docker compose up -d --build
```

La primera vez tarda ~5–10 minutos mientras Docker descarga las imágenes base
e instala Qiskit dentro del contenedor. Las siguientes veces es mucho más rápido.

### URLs disponibles después del despliegue

| URL | Servicio | Descripción |
|---|---|---|
| http://localhost:3000 | **Frontend** | Interfaz gráfica principal |
| http://localhost:8000/docs | Transaction Service | Swagger UI — CRUD cuentas y transacciones |
| http://localhost:8001/docs | QKD Service | Swagger UI — protocolo BB84, demo del espía |
| http://localhost:8000/health | Transaction Service | Health check |
| http://localhost:8001/health | QKD Service | Health check |

### Verificar que todo está corriendo

```powershell
docker compose ps
```

Todos los contenedores deben mostrar estado `running`:

```
NAME                  STATUS
quantumbank_ui        running   (frontend)
quantumbank_txn       running   (transaction_service)
quantumbank_qkd       running   (qkd_service)
quantumbank_db        running   (postgresql)
```

### Parar el sistema

```powershell
# Apagar (conserva los datos)
docker compose down

# Apagar y borrar todos los datos (reset completo)
docker compose down -v

# Apagar, borrar datos e imágenes construidas (rebuild desde cero)
docker compose down -v --rmi all
```

---

## Flujo de prueba recomendado

### Opción A — Interfaz gráfica (http://localhost:3000)

1. **Cuentas** → crear dos o más cuentas con saldo inicial
2. **Transferencias** → hacer una transferencia y observar la animación paso a paso del protocolo BB84
3. **Transferencias** → clic en "🔓 Descifrar" para ver los datos en claro (AES-256-GCM)
4. **Transferencias** → clic en "✏️" para modificar la transacción (origen, destino, monto o concepto) — los saldos se ajustan automáticamente
5. **Transferencias** → clic en "↩️" para eliminar la transacción y ver cómo se devuelve el saldo
6. **Cuentas** → desactivar una cuenta con "⏸ Desactivar", luego reactivarla con "▶️ Reactivar"
7. **Cuentas** → eliminar permanentemente una cuenta con "💀 Eliminar permanentemente" y verificar que sus transacciones aparecen con el badge "🔒 solo lectura"
8. **QKD Lab** → "Generar Clave BB84" y revisar métricas (QBER, entropía, sifted ratio)
9. **QKD Lab** → "🕵️ Lanzar ataque de Eve" para ver la comparativa de detección del espía

### Opción B — Postman

Importar `quantum_bank/QuantumBank.postman_collection.json` en Postman.
La colección ya tiene las variables de entorno y los ejemplos listos.

### Opción C — curl

```powershell
# 1. Crear cuentas
curl -X POST http://localhost:8000/cuentas/ `
  -H "Content-Type: application/json" `
  -d '{"titular": "Ana Garcia", "saldo_inicial": 5000000}'

curl -X POST http://localhost:8000/cuentas/ `
  -H "Content-Type: application/json" `
  -d '{"titular": "Carlos Lopez", "saldo_inicial": 1000000}'

# 2. Transferencia cifrada con BB84 (tarda ~2s mientras Qiskit genera la clave)
curl -X POST http://localhost:8000/transacciones/ `
  -H "Content-Type: application/json" `
  -d '{"cuenta_origen_id":1,"cuenta_destino_id":2,"monto":250000,"concepto":"Pago cuota"}'

# 3. Ver payload cifrado (AES-256-GCM, ilegible sin la clave)
curl http://localhost:8000/transacciones/1

# 4. Descifrar (Transaction Service recupera la clave del QKD Service)
curl http://localhost:8000/transacciones/1/descifrar

# 5. Demo del espía — compara canal limpio vs Eve interceptando
curl -X POST "http://localhost:8001/demo/eavesdrop-compare?n_bits=64"
```

---

## Endpoints del sistema

### Transaction Service — http://localhost:8000

#### Cuentas

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/cuentas/` | Listar todas las cuentas (incluye ELIMINADAS) |
| POST | `/cuentas/` | Crear cuenta |
| GET | `/cuentas/{id}` | Obtener cuenta por ID |
| PUT | `/cuentas/{id}` | Actualizar titular · enviar `{"estado":"ACTIVA"}` para reactivar |
| DELETE | `/cuentas/{id}` | Desactivar cuenta (ACTIVA → INACTIVA, reversible) |
| **DELETE** | **`/cuentas/{id}/permanente`** | **Eliminar permanentemente (→ ELIMINADA, conserva historial)** |

**Ciclo de vida de una cuenta:**
```
Crear → ACTIVA ──── Desactivar ──→ INACTIVA ──── Reactivar ──→ ACTIVA
                        │                              │
                        └─── Eliminar permanente ──────┘
                                      ↓
                                  ELIMINADA  (solo lectura, no reversible)
```

#### Transacciones

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/transacciones/` | Listar transacciones |
| **POST** | **`/transacciones/`** | **Crear transferencia — activa BB84 + AES-GCM** |
| GET | `/transacciones/{id}` | Ver transacción (payload cifrado) |
| **PUT** | **`/transacciones/{id}`** | **Modificar — ajusta saldos automáticamente** |
| GET | `/transacciones/{id}/descifrar` | Descifrar payload con clave del QKD Service |
| DELETE | `/transacciones/{id}` | Eliminar (ver reglas abajo) |

**Reglas de modificación y eliminación de transacciones:**

| Estado de las cuentas | PUT (modificar) | DELETE (eliminar) |
|---|---|---|
| Ambas cuentas existen | ✅ Revierte saldo original, aplica nuevo | ✅ Devuelve saldo a origen |
| Una cuenta eliminada | ❌ 403 — transacción de solo lectura | ❌ 400 — estados inconsistentes |
| Ambas cuentas eliminadas | ❌ 403 — transacción de solo lectura | ✅ Elimina sin revertir saldo |

### QKD Service — http://localhost:8001

| Método | Endpoint | Descripción |
|---|---|---|
| **POST** | **`/session-key`** | **Ejecutar BB84 y generar clave** |
| GET | `/session-key/{id}` | Metadatos de una sesión (sin clave) |
| GET | `/session-key/{id}/clave` | Recuperar clave almacenada |
| GET | `/sessions` | Listar todas las sesiones QKD |
| **POST** | **`/demo/eavesdrop-compare`** | **Demo: canal limpio vs espía** |

---

## Demos de conceptos cuánticos

Las demos son **scripts Python independientes**, no requieren Docker.
Corren directamente en tu máquina con Qiskit o Braket instalado.

### Con IBM Qiskit (recomendado — 100% gratis, sin cuenta)

```powershell
# Instalar (una sola vez)
pip install -r requirements_qiskit.txt

# Menú interactivo para presentación
py qiskit_demo/presentacion.py

# O demos individuales
py qiskit_demo/01_superposicion.py
py qiskit_demo/02_entrelazamiento.py
py qiskit_demo/03_interferencia.py
py qiskit_demo/04_grover.py
```

### Con AWS Braket (gratis con LocalSimulator)

> Requiere Python 3.12 (incompatible con 3.14+). Crear un venv separado.

```powershell
# Crear venv con Python 3.12 (una sola vez)
py -3.12 -m venv C:\braket_venv
C:\braket_venv\Scripts\pip install -r requirements_braket.txt

# Menú interactivo
C:\braket_venv\Scripts\python.exe braket_demo/presentacion.py
```

> **Sobre costos de AWS Braket:** El `LocalSimulator` es completamente gratis.
> Los simuladores en la nube (SV1, TN1) y el hardware cuántico real cobran por tarea.
> Este proyecto usa únicamente el LocalSimulator → **$0**.

### Contenido de las demos

| Demo | Concepto | Qué muestra |
|---|---|---|
| 01 | **Superposición** | Un qubit con compuerta H da ~50% de 0s y ~50% de 1s en 1000 mediciones |
| 02 | **Entrelazamiento** | Bell State `H·CNOT`: solo aparecen `\|00⟩` y `\|11⟩`, nunca `\|01⟩` ni `\|10⟩` |
| 03 | **Interferencia** | `H·H = Identidad`: aplicar Hadamard dos veces cancela la superposición |
| 04 | **Algoritmo de Grover** | Encuentra `\|101⟩` en 8 estados con ~97% de probabilidad en 2 iteraciones |

---

## Stack tecnológico

### Sistema bancario

| Capa | Tecnología | Versión |
|---|---|---|
| Interfaz gráfica | React + Vite + Tailwind CSS | React 18 |
| API REST | FastAPI + Uvicorn | 0.115 |
| ORM | SQLAlchemy | 2.0 |
| Base de datos transacciones | PostgreSQL | 16 |
| Base de datos sesiones QKD | SQLite | (embebido) |
| Validación de datos | Pydantic | v2 |
| Motor cuántico | **IBM Qiskit + Qiskit Aer** | 1.3 + 0.15 |
| Cifrado de payload | AES-256-GCM | cryptography 43 |
| Cliente HTTP entre servicios | httpx | 0.27 |
| Contenerización | Docker + Docker Compose | v2 |

### Demos de conceptos

| Framework | Empresa | Simulador usado |
|---|---|---|
| **IBM Qiskit** | IBM Quantum | AerSimulator (método stabilizer — Clifford) |
| **AWS Braket** | Amazon Web Services | LocalSimulator |

---

## Por qué IBM Qiskit como motor principal

1. **Gratis y local** — no requiere cuenta, no hay costos, funciona sin internet.
2. **AerSimulator stabilizer** — simula circuitos de Clifford (compuertas H, X, CNOT)
   usando tablas de estabilizadores. Permite simular **cientos de qubits en milisegundos**
   en lugar de requerir memoria exponencial como el modo statevector.
3. **Académicamente estándar** — es el framework más usado en universidades e investigación.
4. **Mismo protocolo que hardware real** — el circuito BB84 que corre en AerSimulator
   es idéntico al que correría en un procesador cuántico real de IBM.

---
