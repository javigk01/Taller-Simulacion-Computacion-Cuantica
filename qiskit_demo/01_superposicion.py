"""
Demo 1 — Superposición Cuántica (IBM Qiskit)
=============================================
Un qubit clásico es 0 ó 1. Un qubit en superposición es AMBOS a la vez hasta medirlo.
La compuerta Hadamard (H) crea superposición: |0⟩ → (|0⟩ + |1⟩)/√2

Al medir 1000 veces esperamos ~500 ceros y ~500 unos.
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

print("=" * 55)
print("  DEMO 1 — SUPERPOSICIÓN CUÁNTICA (Qiskit)")
print("=" * 55)
print()
print("Circuito:")
print("  q: ─[H]─[M]─")
print("     estado   medición")
print()

# --- Circuito sin superposición (estado clásico) ---
qc_clasico = QuantumCircuit(1, 1)
qc_clasico.measure(0, 0)

# --- Circuito con superposición ---
qc_super = QuantumCircuit(1, 1)
qc_super.h(0)          # Hadamard: coloca el qubit en superposición
qc_super.measure(0, 0)

print("Circuito con compuerta H:")
print(qc_super.draw(output="text"))
print()

sim = AerSimulator()

# Medir estado clásico |0⟩
job_c = sim.run(transpile(qc_clasico, sim), shots=1000)
counts_c = job_c.result().get_counts()

# Medir estado en superposición
job_s = sim.run(transpile(qc_super, sim), shots=1000)
counts_s = job_s.result().get_counts()

print("─" * 55)
print("Sin H (estado clásico |0⟩) — 1000 mediciones:")
for bit, n in sorted(counts_c.items()):
    bar = "█" * (n // 20)
    print(f"  |{bit}⟩ : {n:4d}  {bar}")

print()
print("Con H (superposición) — 1000 mediciones:")
for bit, n in sorted(counts_s.items()):
    bar = "█" * (n // 20)
    print(f"  |{bit}⟩ : {n:4d}  {bar}")

print()
print("★ El qubit en superposición colapsa al azar con ~50% de probabilidad")
print("  de obtener 0 ó 1. Esto es imposible en cómputo clásico.")
