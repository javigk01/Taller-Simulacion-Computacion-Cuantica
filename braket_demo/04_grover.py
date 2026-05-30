"""
Demo 4 — Algoritmo de Grover (AWS Braket)
==========================================
Busca |101⟩ en 8 estados usando 2 iteraciones de Grover.
Ejecutar: C:\\braket_venv\\Scripts\\python.exe braket_demo/04_grover.py
"""

import math
from braket.circuits import Circuit
from braket.devices import LocalSimulator

TARGET = "101"
N_QUBITS = 3
N_STATES = 2 ** N_QUBITS
N_ITER = round(math.pi / 4 * math.sqrt(N_STATES))

print("=" * 55)
print("  DEMO 4 — ALGORITMO DE GROVER (AWS Braket)")
print("=" * 55)
print(f"  Buscando: |{TARGET}⟩ = {int(TARGET, 2)} en {N_STATES} estados")
print(f"  Iteraciones: {N_ITER}")
print()


def oracle_braket(circ: Circuit, target: str) -> Circuit:
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            circ.x(i)
    # Multi-controlled-Z via CCZ (Toffoli + H)
    circ.h(N_QUBITS - 1)
    circ.ccnot(0, 1, N_QUBITS - 1)
    circ.h(N_QUBITS - 1)
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            circ.x(i)
    return circ


def diffuser_braket(circ: Circuit) -> Circuit:
    circ.h([0, 1, 2])
    circ.x([0, 1, 2])
    circ.h(2)
    circ.ccnot(0, 1, 2)
    circ.h(2)
    circ.x([0, 1, 2])
    circ.h([0, 1, 2])
    return circ


circ = Circuit().h([0, 1, 2])
for _ in range(N_ITER):
    circ = oracle_braket(circ, TARGET)
    circ = diffuser_braket(circ)
circ.measure([0, 1, 2])

device = LocalSimulator()
result = device.run(circ, shots=1000).result()
counts = result.measurement_counts

print("─" * 55)
print("Resultados de 1000 ejecuciones:")
for estado, n in sorted(counts.items(), key=lambda x: -x[1]):
    bar = "█" * (n // 20)
    marca = " ← OBJETIVO" if estado == TARGET else ""
    print(f"  |{estado}⟩ ({int(estado, 2)}): {n:4d}  {bar}{marca}")

prob = counts.get(TARGET, 0) / 1000
print()
print(f"★ Probabilidad de |{TARGET}⟩: {prob:.1%}  (clásico: {1/N_STATES:.1%})")
