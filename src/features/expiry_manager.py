"""
expiry_manager.py - Password expiry tracking and reminders
Automatically tracks password age and sends reminders
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

class ExpiryManager:
    """Manages password expiry tracking"""
    
    # Default expiry periods in days
    DEFAULT_PERIODS = {
        'critical': 30,      # High security (banking, email)
        'important': 60,     # Medium security (social media, work)
        'normal': 90,        # Low security (forums, newsletters)
        'archive': 180       # Rarely used
    }
    
    def __init__(self, vault_manager=None):
        self.vault = vault_manager
        self.settings_path = os.path.expanduser("~/Documents/VaultKeeper/expiry_settings.json")
        self.expiry_settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """Load expiry settings from file"""
        default_settings = {
            'enabled': True,
            'notification_days': [7, 3, 1],  # Notify 7, 3, and 1 day before
            'default_period': 90,
            'auto_check_on_unlock': True,
            'last_check': None
        }
        
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
        except:
            pass
        
        return default_settings
    
    def _save_settings(self):
        """Save expiry settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(self.expiry_settings, f, indent=2)
        except:
            pass
    
    def set_password_age(self, entry_id: int, last_changed: datetime):
        """Set the last changed date for a password"""
        if self.vault and self.vault.db:
            try:
                self.vault.db.update_entry(entry_id, {
                    'password_last_changed': int(last_changed.timestamp())
                })
            except:
                pass
    
    def get_password_age(self, entry: Dict) -> Optional[int]:
        """Get password age in days"""
        last_changed = entry.get('password_last_changed') or entry.get('created_at')
        if last_changed:
            last_date = datetime.fromtimestamp(last_changed)
            age = (datetime.now() - last_date).days
            return age
        return None
    
    def is_expiring(self, entry: Dict, days_threshold: int = None) -> Dict:
        """
        Check if password is expiring soon
        
        Returns:
            dict with keys: is_expiring, days_left, severity, message
        """
        age = self.get_password_age(entry)
        if age is None:
            return {'is_expiring': False, 'days_left': None, 'severity': None, 'message': None}
        
        # Get expiry period for this entry
        period = entry.get('expiry_period', self.expiry_settings.get('default_period', 90))
        days_left = period - age
        
        if days_left <= 0:
            return {
                'is_expiring': True,
                'days_left': days_left,
                'severity': 'critical',
                'message': f'Password expired {abs(days_left)} days ago! Change immediately.'
            }
        elif days_left <= 7:
            return {
                'is_expiring': True,
                'days_left': days_left,
                'severity': 'high',
                'message': f'Password expires in {days_left} days!'
            }
        elif days_left <= 30:
            return {
                'is_expiring': True,
                'days_left': days_left,
                'severity': 'medium',
                'message': f'Password will expire in {days_left} days'
            }
        else:
            return {
                'is_expiring': False,
                'days_left': days_left,
                'severity': None,
                'message': None
            }
    
    def get_expiring_entries(self, threshold_days: int = 30) -> List[Dict]:
        """Get all entries with passwords expiring within threshold days"""
        if not self.vault or not self.vault.db:
            return []
        
        try:
            entries = self.vault.db.get_all_entries()
        except:
            return []
        
        expiring = []
        for entry in entries:
            result = self.is_expiring(entry, threshold_days)
            if result['is_expiring']:
                expiring.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'username': entry.get('username'),
                    'days_left': result['days_left'],
                    'severity': result['severity'],
                    'message': result['message']
                })
        
        # Sort by days left (most urgent first)
        expiring.sort(key=lambda x: x['days_left'])
        return expiring
    
    def get_statistics(self) -> Dict:
        """Get expiry statistics for the vault"""
        expiring = self.get_expiring_entries(90)
        
        return {
            'total_expiring': len(expiring),
            'critical': sum(1 for e in expiring if e['severity'] == 'critical'),
            'high': sum(1 for e in expiring if e['severity'] == 'high'),
            'medium': sum(1 for e in expiring if e['severity'] == 'medium'),
            'expiring_list': expiring[:10]  # Top 10 most urgent
        }
    
    def update_password_changed(self, entry_id: int):
        """Call this when a password is changed/updated"""
        now = int(datetime.now().timestamp())
        if self.vault and self.vault.db:
            try:
                self.vault.db.update_entry(entry_id, {
                    'password_last_changed': now,
                    'password_changed_at': now
                })
            except:
                pass
    
    def set_expiry_period(self, entry_id: int, days: int):
        """Set custom expiry period for an entry"""
        if self.vault and self.vault.db:
            try:
                self.vault.db.update_entry(entry_id, {
                    'expiry_period': days
                })
            except:
                pass


class ExpiryNotifier:
    """Handles expiry notifications and reminders"""
    
    def __init__(self, expiry_manager: ExpiryManager):
        self.expiry_manager = expiry_manager
        self.notification_history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load notification history to avoid duplicate alerts"""
        history_path = os.path.expanduser("~/Documents/VaultKeeper/expiry_notifications.json")
        try:
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'last_notified': {}, 'dismissed': []}
    
    def _save_history(self):
        """Save notification history"""
        history_path = os.path.expanduser("~/Documents/VaultKeeper/expiry_notifications.json")
        try:
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            with open(history_path, 'w') as f:
                json.dump(self.notification_history, f, indent=2)
        except:
            pass
    
    def get_pending_notifications(self) -> List[Dict]:
        """Get notifications that need to be shown"""
        expiring = self.expiry_manager.get_expiring_entries(30)
        pending = []
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for entry in expiring:
            entry_key = f"{entry['id']}_{entry['days_left']}"
            
            # Skip if already notified today
            if entry_key in self.notification_history.get('last_notified', {}):
                if self.notification_history['last_notified'][entry_key] == today:
                    continue
            
            # Skip if dismissed
            if entry['id'] in self.notification_history.get('dismissed', []):
                continue
            
            pending.append(entry)
        
        return pending
    
    def mark_notified(self, entry_id: int, days_left: int):
        """Mark a notification as sent"""
        today = datetime.now().strftime('%Y-%m-%d')
        entry_key = f"{entry_id}_{days_left}"
        
        if 'last_notified' not in self.notification_history:
            self.notification_history['last_notified'] = {}
        
        self.notification_history['last_notified'][entry_key] = today
        self._save_history()
    
    def dismiss_entry(self, entry_id: int):
        """Dismiss notifications for an entry"""
        if entry_id not in self.notification_history.get('dismissed', []):
            self.notification_history.setdefault('dismissed', []).append(entry_id)
            self._save_history()
    
    def reset_dismissed(self, entry_id: int = None):
        """Reset dismissed notifications"""
        if entry_id:
            if entry_id in self.notification_history.get('dismissed', []):
                self.notification_history['dismissed'].remove(entry_id)
        else:
            self.notification_history['dismissed'] = []
        self._save_history()
