"""
Demo 2 — Entrelazamiento Cuántico (AWS Braket)
===============================================
Ejecutar: C:\\braket_venv\\Scripts\\python.exe braket_demo/02_entrelazamiento.py
"""

from braket.circuits import Circuit
from braket.devices import LocalSimulator

print("=" * 55)
print("  DEMO 2 — ENTRELAZAMIENTO CUÁNTICO (AWS Braket)")
print("=" * 55)
print()

device = LocalSimulator()

# Bell State |Φ+⟩
circ = Circuit().h(0).cnot(0, 1).measure([0, 1])

print("Circuito Bell State:")
print(circ)
print()

result = device.run(circ, shots=1000).result()

print("─" * 55)
print("Resultados de 1000 mediciones:")
for estado, n in sorted(result.measurement_counts.items(), key=lambda x: -x[1]):
    bar = "█" * (n // 20)
    print(f"  |{estado}⟩ : {n:4d}  {bar}")

print()
print("★ Solo |00⟩ y |11⟩ — correlación perfecta entre qubits entrelazados.")
