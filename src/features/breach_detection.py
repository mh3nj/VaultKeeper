"""
breach_detection.py - Offline breach detection
Checks passwords against local breach database
"""

import hashlib
import sqlite3
import os
from typing import List, Dict, Set

class BreachDetector:
    """Offline breach detection using local database"""
    
    # Sample breached password hashes (first 5 chars of SHA1)
    # In production, this would be a full database of known breaches
    BREACHED_PASSWORDS = {
        'password', '123456', '123456789', 'qwerty', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'master',
        'hello', 'freedom', 'whatever', 'trustno1', 'princess', 'sunshine'
    }
    
    def __init__(self, vault_manager=None):
        self.vault = vault_manager
        self._init_db()
    
    def _init_db(self):
        """Initialize local breach database"""
        pass  # Simple in-memory for now
    
    def check_password(self, password: str) -> Dict:
        """Check if a password has been breached"""
        if not password:
            return {'is_breached': False, 'breach_count': 0, 'message': 'No password to check'}
        
        # Simple check against known breached passwords
        # In production, you'd check against a real breached password database
        is_breached = password.lower() in self.BREACHED_PASSWORDS
        
        if is_breached:
            return {
                'is_breached': True,
                'breach_count': 1,
                'hash_prefix': hashlib.sha1(password.encode()).hexdigest()[:5].upper(),
                'message': 'This password appears in known data breaches!'
            }
        else:
            return {
                'is_breached': False,
                'breach_count': 0,
                'hash_prefix': hashlib.sha1(password.encode()).hexdigest()[:5].upper(),
                'message': 'Not found in known breaches'
            }
    
    def check_entries(self, entries: List[Dict]) -> List[Dict]:
        """Check multiple entries for breaches"""
        breached = []
        for entry in entries:
            password = entry.get('password', '')
            if password:
                result = self.check_password(password)
                if result['is_breached']:
                    breached.append({
                        'id': entry.get('id'),
                        'title': entry.get('title', 'Unknown'),
                        'username': entry.get('username', ''),
                        'breach_count': result['breach_count'],
                        'message': result['message'],
                        'hash_prefix': result['hash_prefix']
                    })
        return breached
    
    def get_statistics(self, entries: List[Dict]) -> Dict:
        """Get breach statistics for vault"""
        total = len(entries)
        breached_count = 0
        
        for entry in entries:
            if entry.get('password'):
                result = self.check_password(entry['password'])
                if result['is_breached']:
                    breached_count += 1
        
        return {
            'total_checked': total,
            'breached_count': breached_count,
            'breached_percentage': (breached_count / total * 100) if total > 0 else 0,
            'is_secure': breached_count == 0,
            'status': 'Excellent' if breached_count == 0 else 'Warning' if breached_count < 5 else 'Critical'
        }


class BreachMonitor:
    """Monitor and alert for breached passwords"""
    
    def __init__(self, vault_manager=None):
        self.vault = vault_manager
        self.detector = BreachDetector(vault_manager)
    
    def scan_vault(self) -> List[Dict]:
        """Scan entire vault for breaches using real data"""
        if not self.vault or not self.vault.db:
            return []
        
        entries = self.vault.db.get_all_entries()
        return self.detector.check_entries(entries)
    
    def get_high_risk_entries(self, threshold: int = 1) -> List[Dict]:
        """Get entries with breach count above threshold"""
        breached = self.scan_vault()
        return [b for b in breached if b.get('breach_count', 0) >= threshold]
    
    def generate_alert_report(self) -> str:
        """Generate human-readable alert report"""
        breached = self.scan_vault()
        
        if not breached:
            return "✅ No breached passwords found in your vault!"
        
        report = f"⚠️ Found {len(breached)} breached passwords:\n\n"
        for b in breached[:10]:  # Show top 10
            report += f"  • {b['title']} ({b['username']})\n"
            report += f"    {b['message']}\n\n"
        
        if len(breached) > 10:
            report += f"\n... and {len(breached) - 10} more.\n"
        
        report += "\n💡 Recommendation: Change these passwords immediately!"
        return report
    
    def get_statistics(self) -> Dict:
        """Get breach statistics for the vault"""
        if not self.vault or not self.vault.db:
            return {'total_checked': 0, 'breached_count': 0, 'is_secure': True}
        
        entries = self.vault.db.get_all_entries()
        return self.detector.get_statistics(entries)
