"""
Menú interactivo para la presentación de demos de Qiskit.
Ejecutar: py qiskit_demo/presentacion.py
"""

import importlib
import sys

DEMOS = {
    "1": ("Superposición Cuántica",  "qiskit_demo.01_superposicion"),
    "2": ("Entrelazamiento Cuántico", "qiskit_demo.02_entrelazamiento"),
    "3": ("Interferencia Cuántica",   "qiskit_demo.03_interferencia"),
    "4": ("Algoritmo de Grover",      "qiskit_demo.04_grover"),
}


def menu():
    print()
    print("╔" + "═" * 53 + "╗")
    print("║   COMPUTACIÓN CUÁNTICA — IBM Qiskit + AerSimulator  ║")
    print("║          Arquitectura de Software — Javeriana        ║")
    print("╠" + "═" * 53 + "╣")
    for k, (nombre, _) in DEMOS.items():
        print(f"║  [{k}] {nombre:<47}║")
    print("║  [0] Salir" + " " * 43 + "║")
    print("╚" + "═" * 53 + "╝")
    print()


def run_demo(module_path: str):
    # Remove cached module so it re-runs cleanly
    if module_path in sys.modules:
        del sys.modules[module_path]
    try:
        importlib.import_module(module_path)
    except Exception as e:
        print(f"\n[ERROR] {e}")
    print()
    input("  Presiona ENTER para continuar...")


if __name__ == "__main__":
    while True:
        menu()
        opcion = input("  Selecciona una demo: ").strip()
        if opcion == "0":
            print("\n  ¡Hasta luego!\n")
            break
        if opcion in DEMOS:
            nombre, mod = DEMOS[opcion]
            print(f"\n  Ejecutando: {nombre}...\n")
            run_demo(mod)
        else:
            print("  Opción inválida. Intenta de nuevo.")
