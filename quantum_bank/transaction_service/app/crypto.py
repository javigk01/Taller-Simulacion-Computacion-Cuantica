"""
AES-256-GCM encryption layer for the Transaction Service.

The quantum role (BB84 QKD) is to securely exchange the symmetric key.
AES-GCM then does the actual payload encryption — this separation is exactly
how real-world QKD is deployed (e.g., Toshiba/BT trials on fiber-optic links).

Format: nonce (12 bytes) ‖ ciphertext ‖ GCM tag (16 bytes) — packed as hex string.
"""

import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _key_from_hex(clave_hex: str) -> bytes:
    """Derive a 32-byte AES-256 key from the QKD session key hex."""
    raw = bytes.fromhex(clave_hex)
    # Use first 32 bytes; if key < 256 bits, pad with SHA-256 of itself
    if len(raw) >= 32:
        return raw[:32]
    from hashlib import sha256
    return sha256(raw).digest()


def cifrar_aes_gcm(datos: dict, clave_hex: str) -> str:
    """
    Encrypts a dict as JSON using AES-256-GCM.

    Returns a hex string: nonce (12 B) + ciphertext + tag (16 B).
    """
    key = _key_from_hex(clave_hex)
    nonce = os.urandom(12)
    plaintext = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    ciphertext_tag = AESGCM(key).encrypt(nonce, plaintext, None)
    return (nonce + ciphertext_tag).hex()


def descifrar_aes_gcm(cifrado_hex: str, clave_hex: str) -> dict:
    """
    Decrypts an AES-256-GCM payload.

    Raises InvalidTag if the ciphertext was tampered with (GCM integrity check).
    """
    key = _key_from_hex(clave_hex)
    raw = bytes.fromhex(cifrado_hex)
    nonce = raw[:12]
    ciphertext_tag = raw[12:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext_tag, None)
    return json.loads(plaintext.decode("utf-8"))
