"""
analytics.py - Vault analytics dashboard
"""

from datetime import datetime
from typing import List, Dict
import json

class VaultAnalytics:
    """Generate analytics and reports for the vault"""
    
    def __init__(self, database):
        self.db = database
    
    def get_password_strength_distribution(self) -> Dict:
        """Get distribution of password strengths"""
        entries = self.db.get_all_entries()
        
        distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for entry in entries:
            strength = entry.get('password_strength', 0)
            distribution[strength] = distribution.get(strength, 0) + 1
        
        return {
            'weak': distribution[0] + distribution[1],
            'fair': distribution[2],
            'strong': distribution[3],
            'excellent': distribution[4],
            'total': len(entries)
        }
    
    def get_top_categories(self, limit: int = 5) -> List[Dict]:
        """Get most used categories/folders"""
        entries = self.db.get_all_entries()
        folder_counts = {}
        
        for entry in entries:
            folder_id = entry.get('folder_id')
            if folder_id:
                folder_counts[folder_id] = folder_counts.get(folder_id, 0) + 1
        
        # Get folder names
        folders = {f['id']: f['name'] for f in self.db.get_folders()}
        
        result = []
        for folder_id, count in sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
            result.append({
                'name': folders.get(folder_id, 'Unknown'),
                'count': count
            })
        
        return result
    
    def get_activity_timeline(self, days: int = 30) -> List[Dict]:
        """Get activity timeline (created/modified entries)"""
        entries = self.db.get_all_entries()
        now = datetime.now().timestamp()
        cutoff = now - (days * 86400)
        
        # Group by day
        timeline = {}
        for entry in entries:
            created = entry.get('created_at', 0)
            if created >= cutoff:
                day = datetime.fromtimestamp(created).strftime('%Y-%m-%d')
                timeline[day] = timeline.get(day, 0) + 1
        
        return [{'date': k, 'count': v} for k, v in sorted(timeline.items())]
    
    def get_security_score(self) -> Dict:
        """Calculate overall security score (0-100)"""
        entries = self.db.get_all_entries()
        
        if not entries:
            return {'score': 100, 'issues': []}
        
        issues = []
        score = 100
        
        # Check weak passwords
        weak_count = sum(1 for e in entries if e.get('password_strength', 0) < 2)
        if weak_count > 0:
            penalty = min(30, weak_count * 5)
            score -= penalty
            issues.append(f"{weak_count} weak passwords found")
        
        # Check reused passwords
        passwords = [e.get('password') for e in entries if e.get('password')]
        reused = len(passwords) - len(set(passwords))
        if reused > 0:
            penalty = min(20, reused * 4)
            score -= penalty
            issues.append(f"{reused} passwords are reused")
        
        # Check expiring passwords
        expiring = self.db.get_expiring_passwords(7)
        if expiring:
            penalty = min(15, len(expiring) * 3)
            score -= penalty
            issues.append(f"{len(expiring)} passwords expiring soon")
        
        return {
            'score': max(0, score),
            'issues': issues,
            'grade': self._get_grade(max(0, score))
        }
    
    def _get_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
