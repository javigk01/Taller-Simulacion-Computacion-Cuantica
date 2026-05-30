"""
BB84 Quantum Key Distribution (QKD) Protocol — IBM Qiskit implementation.

Protocol flow:
  1. Alice prepares N qubits, each encoded in a random bit (0/1) and random basis (Z or X).
  2. Qubits are "sent" to Bob through the quantum channel (simulated here).
  3. Bob measures each qubit in his own randomly chosen basis.
  4. Sifting: Alice and Bob reveal their bases publicly; discard bits where bases differ.
  5. The remaining bits form the shared secret key.
  6. A random sample is checked for errors (QBER) to detect eavesdropping.

Security: If QBER < 11%, the channel is considered secure (Bennett & Brassard 1984).
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def generar_clave_bb84(n_bits: int = 128) -> dict:
    """
    Simulates BB84 QKD and returns a shared quantum-random secret key.

    Args:
        n_bits: Desired key length in bits (rounded down to nearest multiple of 8).

    Returns:
        dict with keys:
            clave_hex       — hex string of the final key
            key_bits        — list of ints (0/1)
            n_bits          — actual key length used
            protocolo       — "BB84"
            qber            — Quantum Bit Error Rate (0.0 in ideal simulation)
            sifted_ratio    — fraction of qubits kept after sifting (~0.5)
            entropia_shannon — Shannon entropy of the key (ideal = 1.0 bit/bit)
            n_qubits_usados — total qubits in the circuit
            seguro          — True if QBER < 0.11 (BB84 security threshold)
    """
    n_bits = (n_bits // 8) * 8  # align to byte boundary
    # Generate ~3x qubits to compensate for ~50% sifting loss
    n_qubits = n_bits * 3

    rng = np.random.default_rng()

    # ── Alice prepares random bits and random bases ──────────────────────────
    alice_bits = rng.integers(0, 2, n_qubits)   # bits to encode
    alice_bases = rng.integers(0, 2, n_qubits)  # 0 = Z (rectilinear), 1 = X (diagonal)

    # ── Bob chooses random measurement bases ────────────────────────────────
    bob_bases = rng.integers(0, 2, n_qubits)

    # ── Build quantum circuit ────────────────────────────────────────────────
    qc = QuantumCircuit(n_qubits, n_qubits)

    for i in range(n_qubits):
        # Alice encodes her bit in the chosen basis
        if alice_bits[i] == 1:
            qc.x(i)          # |0⟩ → |1⟩  (bit flip)
        if alice_bases[i] == 1:
            qc.h(i)          # rotate to X basis:  |0⟩ → |+⟩,  |1⟩ → |−⟩

        # Bob rotates back if measuring in X basis
        if bob_bases[i] == 1:
            qc.h(i)

        qc.measure(i, i)

    # ── Execute on AerSimulator (stabilizer method handles Clifford circuits
    #    with hundreds of qubits in microseconds) ────────────────────────────
    sim = AerSimulator(method="stabilizer")
    qc_t = transpile(qc, sim, optimization_level=0)
    job = sim.run(qc_t, shots=1)
    result = job.result()
    counts = result.get_counts()

    # Qiskit returns bits in reversed order (MSB = highest qubit index first)
    bits_str = list(counts.keys())[0].replace(" ", "")
    bob_results = np.array([int(b) for b in reversed(bits_str)])

    # ── Sifting ─────────────────────────────────────────────────────────────
    matching_mask = alice_bases == bob_bases
    sifted_alice = alice_bits[matching_mask]
    sifted_bob = bob_results[matching_mask]
    n_sifted = len(sifted_alice)

    # ── QBER check (use bits beyond the key for error estimation) ────────────
    check_n = min(20, max(0, n_sifted - n_bits))
    qber = 0.0
    if check_n > 0:
        errors = np.sum(
            sifted_alice[n_bits: n_bits + check_n]
            != sifted_bob[n_bits: n_bits + check_n]
        )
        qber = float(errors / check_n)

    # ── Final key ────────────────────────────────────────────────────────────
    final_key_bits = sifted_alice[:n_bits].tolist()

    key_bytes = bytes([
        int("".join(map(str, final_key_bits[i: i + 8])), 2)
        for i in range(0, n_bits, 8)
    ])

    # ── Shannon entropy ──────────────────────────────────────────────────────
    p1 = sum(final_key_bits) / n_bits if n_bits > 0 else 0.5
    p0 = 1.0 - p1
    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * float(np.log2(p0))
    if p1 > 0:
        entropy -= p1 * float(np.log2(p1))

    return {
        "clave_hex": key_bytes.hex(),
        "key_bits": final_key_bits,
        "n_bits": n_bits,
        "protocolo": "BB84",
        "qber": round(qber, 4),
        "sifted_ratio": round(n_sifted / n_qubits, 4),
        "entropia_shannon": round(entropy, 6),
        "n_qubits_usados": n_qubits,
        "seguro": qber < 0.11,
    }
