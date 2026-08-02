from __future__ import annotations

from cryptography.fernet import Fernet

from .config import settings

_fernet = Fernet(settings.secret_key.encode())


def encrypt(plaintext: str | None) -> str:
    if not plaintext:
        return ""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str | None) -> str:
    if not ciphertext:
        return ""
    return _fernet.decrypt(ciphertext.encode()).decode()
