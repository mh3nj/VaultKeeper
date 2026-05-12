"""
database.py - Complete SQLite database operations with CRUD
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    """Manages the SQLite database for the vault"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create entries table if not exists
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT DEFAULT 'login',
                title TEXT NOT NULL,
                username TEXT,
                password TEXT NOT NULL,
                url TEXT,
                totp_secret TEXT,
                notes TEXT,
                folder_id INTEGER DEFAULT NULL,
                icon_emoji TEXT DEFAULT '🔐',
                is_favorite INTEGER DEFAULT 0,
                expiry_date INTEGER DEFAULT NULL,
                last_used INTEGER,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                password_strength INTEGER DEFAULT 0,
                custom_fields TEXT,
                tags TEXT,
                attachments TEXT
            )
        """)
        
        # Password history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                old_password TEXT NOT NULL,
                changed_at INTEGER NOT NULL,
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """)
        
        # Check and add missing columns for existing databases
        self._ensure_columns()
        
        self.conn.commit()
    
    def _ensure_columns(self):
        """Add any missing columns to existing table"""
        cursor = self.conn.execute("PRAGMA table_info(entries)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Define required columns with defaults
        required_columns = {
            'attachments': 'TEXT',
            'custom_fields': 'TEXT',
            'tags': 'TEXT',
            'expiry_date': 'INTEGER',
            'password_strength': 'INTEGER DEFAULT 0',
            'folder_id': 'INTEGER DEFAULT NULL'
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                try:
                    self.conn.execute(f"ALTER TABLE entries ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Added missing column: {col_name}")
                except Exception as e:
                    print(f"⚠️ Could not add {col_name}: {e}")
        
        self.conn.commit()
    
    # ========== CRUD Operations ==========
    
    def add_entry(self, entry: Dict) -> int:
        """Add a new entry"""
        now = int(datetime.now().timestamp())
        
        cursor = self.conn.execute("""
            INSERT INTO entries (
                type, title, username, password, url, totp_secret, notes,
                folder_id, icon_emoji, is_favorite, expiry_date,
                created_at, updated_at, password_strength, custom_fields, tags, attachments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.get('type', 'login'),
            entry['title'],
            entry.get('username', ''),
            entry['password'],
            entry.get('url', ''),
            entry.get('totp_secret'),
            entry.get('notes', ''),
            entry.get('folder_id'),
            entry.get('icon_emoji', '🔐'),
            1 if entry.get('is_favorite') else 0,
            entry.get('expiry_date'),
            now,
            now,
            entry.get('password_strength', 0),
            json.dumps(entry.get('custom_fields', {})),
            json.dumps(entry.get('tags', [])),
            json.dumps(entry.get('attachments', []))
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_entry(self, entry_id: int, entry: Dict):
        """Update an existing entry"""
        now = int(datetime.now().timestamp())
        
        # Save old password to history if changed
        if 'password' in entry:
            old = self.get_entry(entry_id)
            if old and old.get('password') != entry['password']:
                self.conn.execute("""
                    INSERT INTO password_history (entry_id, old_password, changed_at)
                    VALUES (?, ?, ?)
                """, (entry_id, old['password'], now))
        
        self.conn.execute("""
            UPDATE entries SET
                type = ?, title = ?, username = ?, password = ?, url = ?,
                totp_secret = ?, notes = ?, folder_id = ?, icon_emoji = ?,
                is_favorite = ?, expiry_date = ?, updated_at = ?,
                password_strength = ?, custom_fields = ?, tags = ?, attachments = ?
            WHERE id = ?
        """, (
            entry.get('type', 'login'),
            entry['title'],
            entry.get('username', ''),
            entry['password'],
            entry.get('url', ''),
            entry.get('totp_secret'),
            entry.get('notes', ''),
            entry.get('folder_id'),
            entry.get('icon_emoji', '🔐'),
            1 if entry.get('is_favorite') else 0,
            entry.get('expiry_date'),
            now,
            entry.get('password_strength', 0),
            json.dumps(entry.get('custom_fields', {})),
            json.dumps(entry.get('tags', [])),
            json.dumps(entry.get('attachments', [])),
            entry_id
        ))
        self.conn.commit()
    
    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Get a single entry by ID"""
        cursor = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_entries(self) -> List[Dict]:
        """Get all entries"""
        cursor = self.conn.execute("SELECT * FROM entries ORDER BY title ASC")
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def search_entries(self, query: str) -> List[Dict]:
        """Search entries by title, username, or URL"""
        search_term = f"%{query}%"
        cursor = self.conn.execute("""
            SELECT * FROM entries 
            WHERE title LIKE ? OR username LIKE ? OR url LIKE ? OR notes LIKE ?
            ORDER BY title ASC
        """, (search_term, search_term, search_term, search_term))
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def delete_entry(self, entry_id: int):
        """Delete an entry"""
        self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()
    
    def toggle_favorite(self, entry_id: int):
        """Toggle favorite status"""
        current = self.conn.execute(
            "SELECT is_favorite FROM entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if current:
            new_value = 0 if current[0] else 1
            self.conn.execute(
                "UPDATE entries SET is_favorite = ? WHERE id = ?",
                (new_value, entry_id)
            )
            self.conn.commit()
    
    def update_last_used(self, entry_id: int):
        """Update last_used timestamp"""
        now = int(datetime.now().timestamp())
        self.conn.execute(
            "UPDATE entries SET last_used = ? WHERE id = ?",
            (now, entry_id)
        )
        self.conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get vault statistics"""
        total = self.conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        weak = self.conn.execute(
            "SELECT COUNT(*) FROM entries WHERE password_strength < 3"
        ).fetchone()[0]
        favorites = self.conn.execute(
            "SELECT COUNT(*) FROM entries WHERE is_favorite = 1"
        ).fetchone()[0]
        
        return {
            'total_entries': total,
            'weak_passwords': weak,
            'favorites': favorites,
            'reused_passwords': 0
        }
    
    def add_tag(self, entry_id, tag):
        """Add tag to entry"""
        entry = self.get_entry(entry_id)
        if entry:
            tags = entry.get('tags', [])
            if tag not in tags:
                tags.append(tag)
                self.update_entry(entry_id, {'tags': tags})

    def remove_tag(self, entry_id, tag):
        """Remove tag from entry"""
        entry = self.get_entry(entry_id)
        if entry:
            tags = entry.get('tags', [])
            if tag in tags:
                tags.remove(tag)
                self.update_entry(entry_id, {'tags': tags})

    def get_entries_by_tag(self, tag):
        """Get all entries with specific tag"""
        tag_search = f'%"{tag}"%'
        cursor = self.conn.execute(
            "SELECT * FROM entries WHERE tags LIKE ? ORDER BY title ASC",
            (tag_search,)
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def _row_to_dict(self, row) -> Dict:
        """Convert SQLite row to dictionary"""
        # Handle different row lengths (for backward compatibility)
        row_dict = {
            'id': row[0],
            'type': row[1] if len(row) > 1 else 'login',
            'title': row[2] if len(row) > 2 else '',
            'username': row[3] if len(row) > 3 else '',
            'password': row[4] if len(row) > 4 else '',
            'url': row[5] if len(row) > 5 else '',
            'totp_secret': row[6] if len(row) > 6 else None,
            'notes': row[7] if len(row) > 7 else '',
            'folder_id': row[8] if len(row) > 8 else None,
            'icon_emoji': row[9] if len(row) > 9 else '🔐',
            'is_favorite': bool(row[10]) if len(row) > 10 else False,
            'expiry_date': row[11] if len(row) > 11 else None,
            'last_used': row[12] if len(row) > 12 else None,
            'created_at': row[13] if len(row) > 13 else 0,
            'updated_at': row[14] if len(row) > 14 else 0,
            'password_strength': row[15] if len(row) > 15 else 0,
            'custom_fields': {},
            'tags': [],
            'attachments': []
        }
        
        # Parse JSON fields if they exist and have values
        if len(row) > 16 and row[16]:
            try:
                row_dict['custom_fields'] = json.loads(row[16])
            except:
                pass
        
        if len(row) > 17 and row[17]:
            try:
                row_dict['tags'] = json.loads(row[17])
            except:
                pass
        
        if len(row) > 18 and row[18]:
            try:
                row_dict['attachments'] = json.loads(row[18])
            except:
                pass
        
        return row_dict
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
