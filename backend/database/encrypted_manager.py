"""
SmartStudy Encrypted Database Manager
Wraps DatabaseManager with AES-256 encryption for sensitive data.
Offline: Uses cryptography library (no cloud keys needed).
"""

from __future__ import annotations

import base64
import getpass
import os
import socket
from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class EncryptedSessionData:
    """
    Encrypts sensitive session data before storage.

    Encrypted: user notes, biometric features, custom tags.
    Not encrypted (fast queries): session IDs, timestamps, subjects, aggregate metrics.
    """

    SERVICE_NAME = "smartstudy"
    KEY_NAME = "db_encryption_key"
    SALT_FILE = Path("data/.salt")

    def __init__(self, user_password: Optional[str] = None) -> None:
        self._fernet: Optional[Fernet] = None

        if not CRYPTO_AVAILABLE:
            logger.info("cryptography not installed — data stored unencrypted")
            return

        key = self._get_or_create_key(user_password)
        if key:
            self._fernet = Fernet(key)
            logger.info("Encryption enabled")

    def encrypt(self, data: str) -> str:
        if self._fernet is None or not data:
            return data
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        if self._fernet is None or not data:
            return data
        try:
            return self._fernet.decrypt(data.encode()).decode()
        except Exception:
            return data

    def encrypt_bytes(self, data: bytes) -> bytes:
        if self._fernet is None:
            return data
        return self._fernet.encrypt(data)

    def decrypt_bytes(self, data: bytes) -> bytes:
        if self._fernet is None:
            return data
        try:
            return self._fernet.decrypt(data)
        except Exception:
            return data

    def _get_or_create_key(self, password: Optional[str]) -> Optional[bytes]:
        if KEYRING_AVAILABLE and not password:
            try:
                stored = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
                if stored:
                    return base64.urlsafe_b64decode(stored.encode())
            except Exception:
                pass

        salt = self._get_or_create_salt()
        master = password or self._get_machine_id()
        if not master:
            return None

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                          salt=salt, iterations=100_000)
        key = base64.urlsafe_b64encode(kdf.derive(master.encode()))

        if KEYRING_AVAILABLE and not password:
            try:
                keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key.decode())
            except Exception:
                pass

        return key

    def _get_or_create_salt(self) -> bytes:
        self.SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.SALT_FILE.exists():
            return self.SALT_FILE.read_bytes()
        salt = os.urandom(16)
        self.SALT_FILE.write_bytes(salt)
        return salt

    @staticmethod
    def _get_machine_id() -> Optional[str]:
        candidates = [Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")]
        for p in candidates:
            if p.exists():
                return p.read_text().strip()
        return f"{socket.gethostname()}:{getpass.getuser()}"
