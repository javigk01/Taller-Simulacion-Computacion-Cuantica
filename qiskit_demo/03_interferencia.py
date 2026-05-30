"""
Demo 3 — Interferencia Cuántica (IBM Qiskit)
============================================
Las amplitudes cuánticas pueden sumarse (interferencia constructiva)
o cancelarse (interferencia destructiva), como las olas del mar.

Demostración: H·H = I (identidad)
  Aplicar Hadamard dos veces devuelve al estado original.
  Esto ocurre porque las amplitudes interfieren destructivamente.

  H|0⟩ = |+⟩ = (|0⟩+|1⟩)/√2
  H|+⟩ = |0⟩  ← interferencia destructiva cancela |1⟩
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

print("=" * 55)
print("  DEMO 3 — INTERFERENCIA CUÁNTICA (Qiskit)")
print("=" * 55)
print()

sim = AerSimulator()

configs = [
    ("Solo H   (1 Hadamard)", 1),
    ("H·H      (2 Hadamard — interferencia)", 2),
    ("H·H·H    (3 Hadamard)", 3),
]

for label, n_h in configs:
    qc = QuantumCircuit(1, 1)
    for _ in range(n_h):
        qc.h(0)
    qc.measure(0, 0)

    job = sim.run(transpile(qc, sim), shots=1000)
    counts = job.result().get_counts()
    c0 = counts.get("0", 0)
    c1 = counts.get("1", 0)

    print(f"  {label}:")
    bar0 = "█" * (c0 // 25)
    bar1 = "█" * (c1 // 25)
    print(f"    |0⟩: {c0:4d}  {bar0}")
    print(f"    |1⟩: {c1:4d}  {bar1}")
    print()

print("★ Con 2 Hadamard: la interferencia destructiva cancela |1⟩ → siempre |0⟩.")
print("  Los algoritmos cuánticos (Grover, Shor) explotan esto para amplificar")
print("  la probabilidad de la respuesta correcta y suprimir las incorrectas.")
