"""
HTTP client for the QKD Service.

The Transaction Service uses this to:
1. Request a new BB84 session key before encrypting a transaction.
2. Retrieve the stored key later when decrypting a transaction payload.
"""

import os

import httpx

QKD_SERVICE_URL = os.getenv("QKD_SERVICE_URL", "http://qkd_service:8001")
_TIMEOUT = 60.0  # BB84 simulation can take a few seconds


class QKDServiceError(RuntimeError):
    pass


def solicitar_clave(client_id: str = "transaction_service", n_bits: int = 128) -> dict:
    """
    Requests a new BB84 session key from the QKD service.

    Returns the full SesionQKDResponse dict (includes clave_hex).
    Raises QKDServiceError if the key was rejected (eavesdropper detected or service down).
    """
    try:
        resp = httpx.post(
            f"{QKD_SERVICE_URL}/session-key",
            json={"client_id": client_id, "n_bits": n_bits, "simular_espia": False},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise QKDServiceError(f"QKD service unreachable: {e}") from e

    data = resp.json()
    if not data.get("seguro") or not data.get("clave_hex"):
        raise QKDServiceError(
            f"QKD key rejected — QBER={data.get('qber', '?')}: {data.get('mensaje', '')}"
        )
    return data


def recuperar_clave(session_id: str) -> str:
    """
    Retrieves the clave_hex of an existing QKD session.
    Used when decrypting a transaction payload on GET /transacciones/{id}/descifrar.
    """
    try:
        resp = httpx.get(
            f"{QKD_SERVICE_URL}/session-key/{session_id}/clave",
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise QKDServiceError(f"QKD service unreachable: {e}") from e

    return resp.json()["clave_hex"]
