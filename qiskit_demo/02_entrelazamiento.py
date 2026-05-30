"""
Demo 2 — Entrelazamiento Cuántico (IBM Qiskit)
===============================================
El entrelazamiento (entanglement) correlaciona dos qubits instantáneamente,
sin importar la distancia física entre ellos (Einstein: "acción fantasmal a distancia").

Circuito Bell State |Φ+⟩ = (|00⟩ + |11⟩)/√2
  q0: ─[H]─[●]─[M]─
  q1: ──────[X]─[M]─

Resultado esperado: solo |00⟩ o |11⟩, NUNCA |01⟩ o |10⟩.
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

print("=" * 55)
print("  DEMO 2 — ENTRELAZAMIENTO CUÁNTICO (Qiskit)")
print("=" * 55)
print()

# Bell State: H en q0, luego CNOT (q0 controla q1)
qc = QuantumCircuit(2, 2)
qc.h(0)       # Superposición en q0
qc.cx(0, 1)   # CNOT: si q0=|1⟩ → flip q1
qc.measure([0, 1], [0, 1])

print("Circuito Bell State |Φ+⟩:")
print(qc.draw(output="text"))
print()

sim = AerSimulator()
job = sim.run(transpile(qc, sim), shots=1000)
counts = job.result().get_counts()

print("─" * 55)
print("Resultados de 1000 mediciones:")
for estado, n in sorted(counts.items(), key=lambda x: -x[1]):
    bar = "█" * (n // 20)
    print(f"  |{estado}⟩ : {n:4d}  {bar}")

print()
print("★ Solo aparecen |00⟩ y |11⟩ — los qubits están PERFECTAMENTE correlacionados.")
print("  Si q0=0, entonces q1=0. Si q0=1, entonces q1=1.")
print("  Medir uno colapsa instantáneamente el otro.")
print()
print("  Aplicación: Criptografía cuántica BB84 usa este principio")
print("  para detectar espías: medir perturba los qubits.")
