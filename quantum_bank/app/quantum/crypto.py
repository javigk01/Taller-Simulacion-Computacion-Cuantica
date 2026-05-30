"""
Quantum-key-based encryption using XOR (One-Time Pad style).

The quantum BB84 key is used directly to XOR-encrypt the transaction payload.
XOR with a truly random key is information-theoretically secure (OTP).
Here the key is reused in a rolling fashion for payloads longer than the key,
which is secure enough for demo purposes but would need HKDF + AES in production.
"""

import json
from decimal import Decimal


def _xor_bytes(data: bytes, key_bytes: bytes) -> bytes:
    key_len = len(key_bytes)
    return bytes(data[i] ^ key_bytes[i % key_len] for i in range(len(data)))


def cifrar_payload(datos: dict, clave_hex: str) -> str:
    """
    Encrypts a dict payload (JSON) with the quantum key.

    Returns a hex string of the encrypted bytes.
    """
    plaintext = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    clave_bytes = bytes.fromhex(clave_hex)
    cifrado = _xor_bytes(plaintext, clave_bytes)
    return cifrado.hex()


def descifrar_payload(cifrado_hex: str, clave_hex: str) -> dict:
    """
    Decrypts a hex-encoded ciphertext back to the original dict.
    """
    cifrado_bytes = bytes.fromhex(cifrado_hex)
    clave_bytes = bytes.fromhex(clave_hex)
    plaintext = _xor_bytes(cifrado_bytes, clave_bytes)
    return json.loads(plaintext.decode("utf-8"))
