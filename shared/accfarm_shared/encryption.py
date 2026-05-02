"""Password encryption utilities using AES-GCM."""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Global key - set via environment variable ACCFARM_AES_KEY
_aes_key: Optional[bytes] = None


def get_aes_key() -> bytes:
    """Get the AES key from environment or generate a warning."""
    global _aes_key
    if _aes_key is not None:
        return _aes_key

    key_b64 = os.environ.get("ACCFARM_AES_KEY")
    if not key_b64:
        # Generate a random key for development (not secure for production!)
        _aes_key = AESGCM.generate_key(bit_length=256)
        return _aes_key

    try:
        _aes_key = base64.b64decode(key_b64)
        if len(_aes_key) != 32:
            raise ValueError("Key must be 32 bytes (256 bits)")
        return _aes_key
    except Exception as e:
        raise ValueError(f"Invalid ACCFARM_AES_KEY: {e}")


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using AES-GCM.

    Args:
        password: Plain text password

    Returns:
        Base64-encoded ciphertext with nonce prepended
    """
    key = get_aes_key()
    aesgcm = AESGCM(key)

    # Generate random nonce
    nonce = os.urandom(12)  # 96-bit nonce for GCM

    # Encrypt
    ciphertext = aesgcm.encrypt(nonce, password.encode("utf-8"), None)

    # Prepend nonce to ciphertext and base64 encode
    encrypted = base64.b64encode(nonce + ciphertext).decode("ascii")
    return encrypted


def decrypt_password(encrypted: str) -> str:
    """
    Decrypt an AES-GCM encrypted password.

    Args:
        encrypted: Base64-encoded ciphertext with nonce prepended

    Returns:
        Plain text password
    """
    key = get_aes_key()
    aesgcm = AESGCM(key)

    # Decode and split nonce from ciphertext
    data = base64.b64decode(encrypted)
    nonce = data[:12]
    ciphertext = data[12:]

    # Decrypt
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
