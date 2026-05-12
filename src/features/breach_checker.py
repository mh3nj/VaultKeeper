"""
breach_checker.py - Offline breach detection
"""

import sqlite3
import hashlib
import os
from typing import List, Set

class BreachChecker:
    """Check passwords against known breaches (offline)"""
    
    def __init__(self, db_path: str = None):
        """Initialize breach checker with local database"""
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'breached_passwords.db'
        )
        self.breached_passwords = self._load_breached_passwords()
    
    def _load_breached_passwords(self) -> Set[str]:
        """Load breached passwords from local database"""
        # For demo, returns a small set
        # In production, this would be a compressed database of SHA1 prefixes
        return {
            'password', '123456', '123456789', 'qwerty', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', 'dragon'
        }
    
    def is_breached(self, password: str) -> bool:
        """Check if password has been in a known breach"""
        # Simple check - in production, use SHA1 prefix
        return password.lower() in self.breached_passwords
    
    def check_entries(self, entries: List[dict]) -> List[dict]:
        """Check multiple entries for breaches"""
        breached_entries = []
        for entry in entries:
            if self.is_breached(entry.get('password', '')):
                breached_entries.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'username': entry.get('username', ''),
                    'reason': 'Found in data breach'
                })
        return breached_entries
    
    def get_statistics(self, entries: List[dict]) -> dict:
        """Get breach statistics for vault"""
        total = len(entries)
        breached = sum(1 for e in entries if self.is_breached(e.get('password', '')))
        
        return {
            'total_checked': total,
            'breached_count': breached,
            'breached_percentage': (breached / total * 100) if total > 0 else 0,
            'is_secure': breached == 0
        }
