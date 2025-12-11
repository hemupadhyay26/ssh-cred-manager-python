"""Encryption utilities for securing passwords."""

import base64
import os
from cryptography.fernet import Fernet
from pathlib import Path


class EncryptionManager:
    """Handles encryption and decryption of sensitive data."""
    
    def __init__(self, key_file: Path):
        """Initialize with a key file path."""
        self.key_file = key_file
        self._fernet = None
    
    def _load_or_create_key(self) -> bytes:
        """Load existing key or create a new one."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate a new key
            key = Fernet.generate_key()
            # Save it securely
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.key_file, 0o600)
            return key
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance."""
        if self._fernet is None:
            key = self._load_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        if not plaintext:
            return None
        fernet = self._get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string."""
        if not encrypted_text:
            return None
        try:
            fernet = self._get_fernet()
            encrypted = base64.b64decode(encrypted_text.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")

