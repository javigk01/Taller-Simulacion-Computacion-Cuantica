"""
Demo 3 — Interferencia Cuántica (AWS Braket)
============================================
Ejecutar: C:\\braket_venv\\Scripts\\python.exe braket_demo/03_interferencia.py
"""

from braket.circuits import Circuit
from braket.devices import LocalSimulator

print("=" * 55)
print("  DEMO 3 — INTERFERENCIA CUÁNTICA (AWS Braket)")
print("=" * 55)
print()

device = LocalSimulator()

configs = [
    ("1 Hadamard (superposición)", Circuit().h(0).measure(0)),
    ("2 Hadamard (H·H = identidad)", Circuit().h(0).h(0).measure(0)),
    ("3 Hadamard", Circuit().h(0).h(0).h(0).measure(0)),
]

for label, circ in configs:
    result = device.run(circ, shots=1000).result()
    counts = result.measurement_counts
    c0 = counts.get("0", 0)
    c1 = counts.get("1", 0)
    print(f"  {label}:")
    print(f"    |0⟩: {c0:4d}  {'█' * (c0 // 25)}")
    print(f"    |1⟩: {c1:4d}  {'█' * (c1 // 25)}")
    print()

print("★ 2× Hadamard: interferencia destructiva elimina |1⟩ por completo.")
