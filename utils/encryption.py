"""Encryption utilities for AES-256 data at rest encryption."""

import os
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
import hashlib


class EncryptionManager:
    """Manages AES-256 encryption/decryption operations."""

    def __init__(self, key: str | None = None):
        """Initialize encryption manager with key.
        
        Args:
            key: 32-byte hex-encoded key. If None, uses ENCRYPTION_KEY env var.
        """
        self.key = key or os.getenv("ENCRYPTION_KEY")
        if not self.key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self.cipher = Fernet(self._derive_key(self.key).encode())

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()

    @staticmethod
    def _derive_key(key: str) -> str:
        """Derive a Fernet-compatible key from input key."""
        hashed = hashlib.sha256(key.encode()).digest()
        return urlsafe_b64encode(hashed).decode()

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext data.
        
        Args:
            plaintext: Data to encrypt.
            
        Returns:
            Encrypted data (base64-encoded).
        """
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext data.
        
        Args:
            ciphertext: Encrypted data (base64-encoded).
            
        Returns:
            Decrypted plaintext.
        """
        return self.cipher.decrypt(ciphertext.encode()).decode()


# Singleton instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create encryption manager singleton."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
