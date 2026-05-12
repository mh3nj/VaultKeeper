"""
crypto.py - Encryption utilities for VaultKeeper
"""

import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class VaultCrypto:
    """Handles all encryption/decryption operations"""
    
    def __init__(self, master_password: str, salt: bytes = None):
        self.backend = default_backend()
        
        if salt is None:
            self.salt = os.urandom(32)
        else:
            self.salt = salt
        
        # Key derivation using PBKDF2
        self.key = hashlib.pbkdf2_hmac(
            'sha256',
            master_password.encode('utf-8'),
            self.salt,
            100000,
            dklen=32
        )
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext string using AES-256-CBC"""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # PKCS7 padding
        data = plaintext.encode('utf-8')
        pad_len = 16 - (len(data) % 16)
        padded = data + bytes([pad_len] * pad_len)
        
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return iv + ciphertext
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted data back to plaintext"""
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        pad_len = padded[-1]
        plaintext = padded[:-pad_len]
        
        return plaintext.decode('utf-8')
    
    def get_salt(self) -> bytes:
        return self.salt
