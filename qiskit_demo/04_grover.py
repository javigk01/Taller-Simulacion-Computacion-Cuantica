"""
Demo 4 — Algoritmo de Grover (IBM Qiskit)
==========================================
Búsqueda cuántica: encuentra un elemento en N ítems en O(√N) pasos.
  Clásico: O(N/2) en promedio.  Cuántico: O(√N) → ventaja cuadrática.

Ejemplo: buscar el estado |101⟩ (= 5) en un espacio de 8 estados (3 qubits).
  Grover amplifica la probabilidad de |101⟩ con ~√8 ≈ 2.83 iteraciones.
  Usamos 2 iteraciones → probabilidad de éxito ≈ 97%.
"""

import math
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

TARGET = "101"  # estado buscado (5 en binario)
N_QUBITS = 3
N_STATES = 2 ** N_QUBITS
N_ITER = round(math.pi / 4 * math.sqrt(N_STATES))  # fórmula óptima de Grover

print("=" * 55)
print("  DEMO 4 — ALGORITMO DE GROVER (Qiskit)")
print("=" * 55)
print(f"  Buscando: |{TARGET}⟩ = {int(TARGET, 2)} en {N_STATES} estados")
print(f"  Iteraciones cuánticas: {N_ITER}  (clásico necesitaría ~{N_STATES//2})")
print()


def oracle(qc: QuantumCircuit, target: str) -> None:
    """Flips the phase of the target state."""
    # Apply X to qubits that are '0' in target so the CZ sees all-|1⟩
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            qc.x(i)
    # Multi-controlled Z (phase flip on |111⟩)
    qc.h(N_QUBITS - 1)
    qc.mcx(list(range(N_QUBITS - 1)), N_QUBITS - 1)
    qc.h(N_QUBITS - 1)
    # Undo X gates
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            qc.x(i)


def diffuser(qc: QuantumCircuit) -> None:
    """Grover diffuser (reflection about the average)."""
    qc.h(range(N_QUBITS))
    qc.x(range(N_QUBITS))
    qc.h(N_QUBITS - 1)
    qc.mcx(list(range(N_QUBITS - 1)), N_QUBITS - 1)
    qc.h(N_QUBITS - 1)
    qc.x(range(N_QUBITS))
    qc.h(range(N_QUBITS))


# Build Grover circuit
qc = QuantumCircuit(N_QUBITS, N_QUBITS)
qc.h(range(N_QUBITS))           # Uniform superposition
qc.barrier()

for _ in range(N_ITER):
    oracle(qc, TARGET)           # Mark the target
    qc.barrier()
    diffuser(qc)                 # Amplify the marked state
    qc.barrier()

qc.measure(range(N_QUBITS), range(N_QUBITS))

print("Circuito (comprimido):")
print(qc.draw(output="text", fold=80))
print()

sim = AerSimulator()
job = sim.run(transpile(qc, sim), shots=1000)
counts = job.result().get_counts()

print("─" * 55)
print("Resultados de 1000 ejecuciones:")
for estado, n in sorted(counts.items(), key=lambda x: -x[1]):
    bar = "█" * (n // 20)
    marca = " ← OBJETIVO" if estado == TARGET else ""
    print(f"  |{estado}⟩ ({int(estado, 2)}): {n:4d}  {bar}{marca}")

prob_objetivo = counts.get(TARGET, 0) / 1000
print()
print(f"★ Probabilidad de encontrar |{TARGET}⟩: {prob_objetivo:.1%}")
print(f"  Sin Grover (búsqueda clásica): {1/N_STATES:.1%} por intento")
print(f"  Ventaja cuántica: {prob_objetivo/(1/N_STATES):.0f}× más probable")
