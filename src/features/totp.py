"""
totp.py - Complete OTP (One-Time Password) generator
Supports TOTP, Steam, Yandex, mOTP with time drift correction
"""

import base64
import time
import hashlib
import hmac
import struct
import secrets
import qrcode
import re
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple, Dict, Any


class TOTP:
    """Generate and verify OTP codes with full parameter support and time drift"""
    
    def __init__(self, secret: str, digits: int = 6, interval: int = 30, 
                 algorithm: str = "SHA1", otp_type: str = "totp", 
                 time_offset: int = 0):
        """
        Initialize OTP generator
        
        Args:
            secret: Base32 encoded secret
            digits: Number of digits (6, 8, or 5 for Steam)
            interval: Time interval in seconds (30, 60, or 10 for mOTP)
            algorithm: Hash algorithm ("SHA1", "SHA256", "SHA512", "MD5")
            otp_type: Type ("totp", "steam", "yandex", "motp")
            time_offset: Time drift correction in seconds (positive = ahead)
        """
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm.upper()
        self.otp_type = otp_type.lower()
        self.time_offset = time_offset
        
        # Clean and decode secret
        self.secret = secret.upper().replace(' ', '').replace('-', '')
        self._validate_secret()
    
    def _validate_secret(self):
        """Validate the secret is proper base32"""
        # Add padding if needed
        padding = 8 - (len(self.secret) % 8)
        if padding != 8:
            self.secret += '=' * padding
        
        try:
            self.secret_bytes = base64.b32decode(self.secret)
        except Exception as e:
            raise ValueError(f"Invalid base32 secret: {self.secret[:20]}... Error: {e}")
    
    def _get_hash_function(self):
        """Get hash function based on algorithm"""
        algos = {
            "SHA1": hashlib.sha1,
            "SHA256": hashlib.sha256,
            "SHA512": hashlib.sha512,
            "MD5": hashlib.md5
        }
        return algos.get(self.algorithm, hashlib.sha1)
    
    def _get_current_time(self) -> int:
        """Get current time with offset applied"""
        return int(time.time()) + self.time_offset
    
    def get_current_code(self) -> str:
        """Get current OTP code based on type"""
        current_time = self._get_current_time()
        
        if self.otp_type == "steam":
            return self._generate_steam_code(current_time)
        elif self.otp_type == "yandex":
            return self._generate_yandex_code(current_time)
        elif self.otp_type == "motp":
            return self._generate_motp_code(current_time)
        else:
            return self._generate_totp_code(current_time)
    
    def get_code_at_time(self, timestamp: int) -> str:
        """Get OTP code at specific timestamp (for testing)"""
        if self.otp_type == "steam":
            return self._generate_steam_code(timestamp)
        elif self.otp_type == "yandex":
            return self._generate_yandex_code(timestamp)
        elif self.otp_type == "motp":
            return self._generate_motp_code(timestamp)
        else:
            return self._generate_totp_code(timestamp)
    
    def _generate_totp_code(self, current_time: int) -> str:
        """Generate standard TOTP code"""
        counter = current_time // self.interval
        counter_bytes = struct.pack('>Q', counter)
        hash_func = self._get_hash_function()
        hmac_obj = hmac.new(self.secret_bytes, counter_bytes, hash_func)
        hash_bytes = hmac_obj.digest()
        
        offset = hash_bytes[-1] & 0x0F
        code_bytes = hash_bytes[offset:offset + 4]
        code_int = struct.unpack('>I', code_bytes)[0] & 0x7FFFFFFF
        
        code = str(code_int % (10 ** self.digits))
        return code.zfill(self.digits)
    
    def _generate_steam_code(self, current_time: int) -> str:
        """
        Generate Steam Guard code
        Steam uses TOTP but converts to letters instead of digits
        """
        counter = current_time // self.interval
        counter_bytes = struct.pack('>Q', counter)
        hash_func = self._get_hash_function()
        hmac_obj = hmac.new(self.secret_bytes, counter_bytes, hash_func)
        hash_bytes = hmac_obj.digest()
        
        # Steam uses a specific character set (no vowels or ambiguous letters)
        steam_chars = "23456789BCDFGHJKMNPQRTVWXY"
        
        # Take 5 bytes and convert to Steam code
        code = ""
        for i in range(5):
            # Use 5 bits from the hash at position i*5
            byte_pos = i * 5 // 8
            bit_pos = (i * 5) % 8
            val = (hash_bytes[byte_pos] >> bit_pos) & 0x1F
            if bit_pos > 3 and byte_pos + 1 < len(hash_bytes):
                val |= (hash_bytes[byte_pos + 1] << (8 - bit_pos)) & 0x1F
            code += steam_chars[val % len(steam_chars)]
        
        return code
    
    def _generate_yandex_code(self, current_time: int) -> str:
        """Generate Yandex OTP code"""
        return self._generate_totp_code(current_time)
    
    def _generate_motp_code(self, current_time: int) -> str:
        """Generate mOTP (Mobile OTP) code"""
        return self._generate_totp_code(current_time)
    
    def get_time_remaining(self) -> int:
        """Get seconds remaining in current interval"""
        current_time = self._get_current_time()
        return self.interval - (current_time % self.interval)
    
    def verify(self, code: str, drift: int = 2) -> bool:
        """Verify a code with drift tolerance"""
        current_time = self._get_current_time()
        
        for delta in range(-drift, drift + 1):
            test_time = current_time + (delta * self.interval)
            
            if self.otp_type == "steam":
                test_code = self._generate_steam_code(test_time)
            else:
                test_code = self._generate_totp_code(test_time)
            
            if test_code == code:
                return True
        return False
    
    def get_uri(self, account_name: str, issuer: str = "VaultKeeper") -> str:
        """Generate otpauth:// URI for QR code generation"""
        base = f"otpauth://{self.otp_type}/{issuer}:{account_name}?secret={self.secret}&issuer={issuer}"
        
        if self.otp_type != "steam":
            base += f"&digits={self.digits}&period={self.interval}"
        
        if self.algorithm != "SHA1":
            base += f"&algorithm={self.algorithm}"
        
        return base
    
    def get_qr_code(self, account_name: str, issuer: str = "VaultKeeper") -> Image.Image:
        """Generate QR code image for scanning"""
        uri = self.get_uri(account_name, issuer)
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information for troubleshooting"""
        current_time = self._get_current_time()
        counter = current_time // self.interval
        remaining = self.interval - (current_time % self.interval)
        
        return {
            'type': self.otp_type,
            'algorithm': self.algorithm,
            'digits': self.digits,
            'interval': self.interval,
            'time_offset': self.time_offset,
            'current_time': current_time,
            'counter': counter,
            'time_remaining': remaining,
            'secret_preview': self.secret[:8] + "..." if len(self.secret) > 8 else self.secret
        }


# Helper function to generate a random secret
def generate_secret(length: int = 20) -> str:
    """Generate a random base32 secret for TOTP"""
    random_bytes = secrets.token_bytes(length)
    secret = base64.b32encode(random_bytes).decode('utf-8')
    return secret.replace('=', '')
