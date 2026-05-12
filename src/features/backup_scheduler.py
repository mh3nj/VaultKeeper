"""
backup_scheduler.py - Automatic backup scheduler
"""

import threading
import time
import json
import os
import shutil
from datetime import datetime

class BackupScheduler:
    """Schedule automatic backups"""
    
    def __init__(self, vault_manager):
        self.vault = vault_manager
        self.running = False
        self.thread = None
        self.settings_path = os.path.expanduser("~/Documents/VaultKeeper/backup_schedule.json")
        self.load_settings()
    
    def load_settings(self):
        """Load backup settings"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {'enabled': False, 'frequency': 'weekly', 'last_backup': None}
        except:
            self.settings = {'enabled': False, 'frequency': 'weekly', 'last_backup': None}
    
    def save_settings(self):
        """Save backup settings"""
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f)
    
    def create_backup(self):
        """Create a backup"""
        backup_dir = os.path.expanduser("~/Documents/VaultKeeper/Backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"auto_backup_{timestamp}.vaultbackup")
        
        try:
            shutil.copy2(self.vault.db_path, backup_path)
            self.settings['last_backup'] = timestamp
            self.save_settings()
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
    
    def should_backup(self):
        """Check if backup is needed"""
        if not self.settings['enabled']:
            return False
        
        if not self.settings['last_backup']:
            return True
        
        last = datetime.strptime(self.settings['last_backup'], "%Y%m%d_%H%M%S")
        now = datetime.now()
        
        if self.settings['frequency'] == 'daily':
            return (now - last).days >= 1
        elif self.settings['frequency'] == 'weekly':
            return (now - last).days >= 7
        elif self.settings['frequency'] == 'monthly':
            return (now - last).days >= 30
        
        return False
    
    def run(self):
        """Run scheduler loop"""
        while self.running:
            if self.should_backup():
                self.create_backup()
            time.sleep(3600)  # Check every hour
    
    def start(self):
        """Start the scheduler"""
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
