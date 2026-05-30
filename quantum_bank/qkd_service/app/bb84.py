"""
BB84 Quantum Key Distribution protocol — IBM Qiskit + AerSimulator.

Includes eavesdropper (Eve) simulation via the intercept-and-resend attack.

Physical reality:
  Real QKD uses photon polarization over optical fiber. Here we simulate the
  quantum circuit on a classical computer to demonstrate the concepts.

Eavesdropper model (intercept-and-resend):
  Eve intercepts each qubit with probability `intercept_prob`.
  - If Eve measures in Alice's basis  → qubit undisturbed, no error introduced.
  - If Eve measures in wrong basis    → qubit state collapsed, Bob gets a
    random bit when Alice-Bob bases match → expected QBER ≈ 25% (intercept_prob=1).

Security threshold (Bennett & Brassard 1984):
  QBER < 11%  → channel is considered secure, key accepted.
  QBER ≥ 11%  → eavesdropper likely detected, key discarded.
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def bb84_protocol(n_bits: int = 128, intercept_prob: float = 0.0) -> dict:
    """
    Simulate BB84 and return a shared quantum-random key.

    Args:
        n_bits: Desired key length (rounded to nearest multiple of 8). Max 512.
        intercept_prob: Fraction of qubits Eve intercepts (0.0 = none, 1.0 = all).

    Returns dict with:
        clave_hex         — shared key (hex), None if QBER ≥ 11%
        n_bits            — actual key length
        protocolo         — "BB84"
        qber              — Quantum Bit Error Rate
        sifted_ratio      — fraction of qubits kept after sifting (~0.50)
        entropia_shannon  — Shannon entropy of key bits (ideal = 1.0)
        n_qubits_usados   — total qubits in the circuit
        seguro            — True if QBER < 0.11
        espia_detectado   — True if not seguro AND intercept_prob > 0
        intercept_prob    — the value passed in (for reporting)
    """
    n_bits = max(8, (n_bits // 8) * 8)
    n_qubits = n_bits * 3  # 3× overhead for sifting loss

    rng = np.random.default_rng()

    # ── Alice's preparation ──────────────────────────────────────────────────
    alice_bits = rng.integers(0, 2, n_qubits)   # bits to encode
    alice_bases = rng.integers(0, 2, n_qubits)  # 0 = Z-basis, 1 = X-basis

    # ── Bob's measurement setup ───────────────────────────────────────────────
    bob_bases = rng.integers(0, 2, n_qubits)

    # ── Eve's setup (only relevant if intercept_prob > 0) ─────────────────────
    eve_bases = rng.integers(0, 2, n_qubits)
    eve_intercepts = rng.random(n_qubits) < intercept_prob

    # ── Quantum circuit (Alice → Bob, ideal channel) ──────────────────────────
    # Eve's physical interception is modeled classically below because
    # her effect is a known probabilistic disturbance (no quantum advantage
    # gained by simulating the interception circuit itself).
    qc = QuantumCircuit(n_qubits, n_qubits)
    for i in range(n_qubits):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)
        if bob_bases[i] == 1:
            qc.h(i)
        qc.measure(i, i)

    sim = AerSimulator(method="stabilizer")  # Clifford circuit → ultra-fast
    qc_t = transpile(qc, sim, optimization_level=0)
    counts = sim.run(qc_t, shots=1).result().get_counts()
    bits_str = list(counts.keys())[0].replace(" ", "")
    # Qiskit returns MSB first → reverse to get qubit-index order
    bob_ideal = np.array([int(b) for b in reversed(bits_str)])

    # ── Apply Eve's disturbance (intercept-and-resend) ────────────────────────
    # After sifting, only qubits where alice_bases == bob_bases matter.
    # When Eve intercepts in the wrong basis, those sifted bits are randomized.
    bob_results = bob_ideal.copy()
    for i in range(n_qubits):
        if (
            eve_intercepts[i]
            and eve_bases[i] != alice_bases[i]
            and alice_bases[i] == bob_bases[i]  # would survive sifting
        ):
            # Eve's wrong-basis measurement randomizes Bob's result
            bob_results[i] = int(rng.integers(0, 2))

    # ── Sifting ────────────────────────────────────────────────────────────────
    matching = alice_bases == bob_bases
    sifted_alice = alice_bits[matching]
    sifted_bob = bob_results[matching]
    n_sifted = int(np.sum(matching))

    # ── QBER estimation (use bits beyond the key as a check sample) ───────────
    check_n = min(40, max(0, n_sifted - n_bits))
    qber = 0.0
    if check_n > 0:
        errors = np.sum(
            sifted_alice[n_bits: n_bits + check_n]
            != sifted_bob[n_bits: n_bits + check_n]
        )
        qber = float(errors / check_n)

    seguro = qber < 0.11

    # ── Final key extraction ───────────────────────────────────────────────────
    final_bits = sifted_alice[:n_bits].tolist()
    clave_hex: str | None = None
    if seguro:
        key_bytes = bytes([
            int("".join(map(str, final_bits[i: i + 8])), 2)
            for i in range(0, n_bits, 8)
        ])
        clave_hex = key_bytes.hex()

    # ── Shannon entropy ────────────────────────────────────────────────────────
    p1 = sum(final_bits) / n_bits if n_bits > 0 else 0.5
    p0 = 1.0 - p1
    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * float(np.log2(p0))
    if p1 > 0:
        entropy -= p1 * float(np.log2(p1))

    return {
        "clave_hex": clave_hex,
        "n_bits": n_bits,
        "protocolo": "BB84",
        "qber": round(qber, 4),
        "sifted_ratio": round(n_sifted / n_qubits, 4),
        "entropia_shannon": round(entropy, 6),
        "n_qubits_usados": n_qubits,
        "seguro": seguro,
        "espia_detectado": (not seguro) and (intercept_prob > 0),
        "intercept_prob": intercept_prob,
    }
