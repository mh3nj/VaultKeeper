"""
vault_manager.py - Manages the vault lifecycle with real password
"""

import os
import json
import time
import hashlib
from getpass import getpass
from .crypto import VaultCrypto
from .database import Database

class VaultManager:
    """Manages the vault lifecycle"""
    
    def __init__(self, db_path: str = "vaultkeeper.db"):
        self.db_path = db_path
        self.db = None
        self.crypto = None
        self.master_password = None
        self.salt = None
        self.config_path = "vaultkeeper.config"
        self.failed_attempts = 0
        self.max_attempts = 5
        print(f"🔧 VaultManager initialized with db_path: {db_path}")
    
    def initialize(self):
        """Initialize or load existing vault"""
        print(f"🔧 Checking for existing vault...")
        print(f"   Config exists: {os.path.exists(self.config_path)}")
        print(f"   DB exists: {os.path.exists(self.db_path)}")
        
        if os.path.exists(self.config_path) and os.path.exists(self.db_path):
            print("📂 Existing vault found, unlocking...")
            return self.unlock_vault()
        else:
            print("🆕 No existing vault found, creating new...")
            return self.create_vault()
    
    def create_vault(self):
        """Create a new vault with REAL master password"""
        print("\n" + "="*50)
        print("  VaultKeeper - Create New Vault")
        print("="*50)
        print("\n⚠️  IMPORTANT: This password CANNOT be recovered if lost!\n")
        
        while True:
            password = getpass("Master Password: ")
            confirm = getpass("Confirm Password: ")
            
            if password == confirm and len(password) >= 8:
                # Check password strength
                strength = self._check_password_strength(password)
                if strength < 2:
                    print(f"⚠️  Warning: Weak password ({strength}/4). Consider a stronger one.")
                    if not input("Continue anyway? (y/n): ").lower().startswith('y'):
                        continue
                break
            elif len(password) < 8:
                print("Password must be at least 8 characters")
            else:
                print("Passwords do not match")
        
        print("\n🔧 Generating encryption keys...")
        # Generate salt and initialize crypto
        self.crypto = VaultCrypto(password)
        self.master_password = password
        self.salt = self.crypto.get_salt()
        
        print("🔧 Creating database...")
        # Initialize database (creates empty vault)
        self.db = Database(self.db_path)
        
        # Save config (salt only, never password)
        config = {
            'salt': self.salt.hex(),
            'version': 1,
            'created_at': time.time(),
            'failed_attempts': 0
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        print("\n✅ Vault created successfully!")
        print(f"✅ Database initialized at: {self.db_path}")
        
        # Verify database is working
        try:
            count = len(self.db.get_all_entries())
            print(f"✅ Initial entry count: {count}")
        except Exception as e:
            print(f"⚠️ Warning: Could not verify database: {e}")
        
        return True
    
    def _check_password_strength(self, password: str) -> int:
        """Check password strength (0-4)"""
        score = 0
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        return min(score, 4)
    
    def unlock_vault(self):
        """Unlock existing vault with REAL password verification"""
        print("\n" + "="*50)
        print("  VaultKeeper - Unlock Vault")
        print("="*50)
        
        # Load config
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        self.salt = bytes.fromhex(config['salt'])
        self.failed_attempts = config.get('failed_attempts', 0)
        
        if self.failed_attempts >= self.max_attempts:
            print("\n❌ Too many failed attempts. Vault is locked.")
            print("   Delete vaultkeeper.config to reset (data will be lost).")
            return False
        
        remaining = self.max_attempts - self.failed_attempts
        print(f"\n⚠️  {remaining} attempts remaining\n")
        
        while self.failed_attempts < self.max_attempts:
            password = getpass("Master Password: ")
            
            try:
                print("🔧 Verifying password...")
                self.crypto = VaultCrypto(password, self.salt)
                self.master_password = password
                
                print("🔧 Opening database...")
                # Open database
                self.db = Database(self.db_path)
                
                # Verify by getting count
                entries = self.db.get_all_entries()
                print(f"✅ Database connected. Found {len(entries)} entries.")
                print(f"\n✅ Vault unlocked successfully!")
                
                # Reset failed attempts on success
                self.failed_attempts = 0
                config['failed_attempts'] = 0
                with open(self.config_path, 'w') as f:
                    json.dump(config, f)
                
                return True
                
            except Exception as e:
                self.failed_attempts += 1
                remaining = self.max_attempts - self.failed_attempts
                print(f"❌ Wrong password. {remaining} attempts remaining.")
                
                # Save failed attempts
                config['failed_attempts'] = self.failed_attempts
                with open(self.config_path, 'w') as f:
                    json.dump(config, f)
        
        print("\n❌ Too many failed attempts. Vault is locked.")
        return False
    
    def get_master_password(self):
        """Get master password (for internal use)"""
        return self.master_password
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Change master password (requires old password)"""
        # Verify old password
        try:
            test_crypto = VaultCrypto(old_password, self.salt)
        except:
            return False
        
        # Create new encryption
        self.crypto = VaultCrypto(new_password)
        self.master_password = new_password
        self.salt = self.crypto.get_salt()
        
        # Update config
        config = {
            'salt': self.salt.hex(),
            'version': 1,
            'created_at': time.time(),
            'failed_attempts': 0
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        return True
    
    def add_entry(self, entry_data):
        """Add a new entry to the vault"""
        if self.db is None:
            print("❌ ERROR: Database not connected!")
            return None
        
        try:
            entry_id = self.db.add_entry(entry_data)
            print(f"✅ Added entry: {entry_data.get('title')} (ID: {entry_id})")
            return entry_id
        except Exception as e:
            print(f"❌ Error adding entry: {e}")
            return None
    
    def get_all_entries(self):
        """Get all entries"""
        if self.db is None:
            print("❌ ERROR: Database not connected!")
            return []
        return self.db.get_all_entries()
    
    def update_entry(self, entry_id, entry_data):
        """Update an entry"""
        if self.db is None:
            print("❌ ERROR: Database not connected!")
            return
        self.db.update_entry(entry_id, entry_data)
    
    def delete_entry(self, entry_id):
        """Delete an entry"""
        if self.db is None:
            print("❌ ERROR: Database not connected!")
            return
        self.db.delete_entry(entry_id)
    
    def lock(self):
        """Lock the vault"""
        if self.db:
            self.db.close()
        self.db = None
        self.crypto = None
        self.master_password = None
        print("🔒 Vault locked")
