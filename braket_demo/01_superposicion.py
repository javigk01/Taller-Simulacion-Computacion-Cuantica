"""
Demo 1 — Superposición Cuántica (AWS Braket)
=============================================
Ejecutar: C:\\braket_venv\\Scripts\\python.exe braket_demo/01_superposicion.py
"""

from braket.circuits import Circuit
from braket.devices import LocalSimulator

print("=" * 55)
print("  DEMO 1 — SUPERPOSICIÓN CUÁNTICA (AWS Braket)")
print("=" * 55)
print()

device = LocalSimulator()

# Sin superposición
circ_clasico = Circuit().measure(0)

# Con Hadamard
circ_super = Circuit().h(0).measure(0)

print("Circuito con Hadamard:")
print(circ_super)
print()

result_c = device.run(circ_clasico, shots=1000).result()
result_s = device.run(circ_super, shots=1000).result()

print("─" * 55)
print("Sin H (estado |0⟩) — 1000 mediciones:")
for estado, n in sorted(result_c.measurement_counts.items()):
    bar = "█" * (n // 20)
    print(f"  |{estado}⟩ : {n:4d}  {bar}")

print()
print("Con H (superposición) — 1000 mediciones:")
for estado, n in sorted(result_s.measurement_counts.items()):
    bar = "█" * (n // 20)
    print(f"  |{estado}⟩ : {n:4d}  {bar}")

print()
print("★ ~50% / 50% → superposición cuántica real.")
