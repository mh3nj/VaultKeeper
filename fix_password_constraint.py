"""
fix_password_constraint.py - Fix NOT NULL constraint on password column
"""

import sqlite3
import json

def fix_database():
    db_path = "vaultkeeper.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(entries)")
        columns = cursor.fetchall()
        print("Current schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) notnull={col[3]}")
        
        # Create new table with modified password column (allow NULL)
        cursor.execute("""
            CREATE TABLE entries_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT DEFAULT 'login',
                title TEXT NOT NULL,
                username TEXT,
                password TEXT DEFAULT '',
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
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO entries_new (
                id, type, title, username, password, url, totp_secret, notes,
                folder_id, icon_emoji, is_favorite, expiry_date, last_used,
                created_at, updated_at, password_strength, custom_fields, tags, attachments
            )
            SELECT 
                id, type, title, username, 
                COALESCE(password, '') as password,
                url, totp_secret, notes, folder_id, icon_emoji, is_favorite,
                expiry_date, last_used, created_at, updated_at, password_strength,
                custom_fields, tags, attachments
            FROM entries
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE entries")
        cursor.execute("ALTER TABLE entries_new RENAME TO entries")
        
        # Recreate password history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                old_password TEXT NOT NULL,
                changed_at INTEGER NOT NULL,
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        
        # Verify fix
        cursor.execute("SELECT COUNT(*) FROM entries WHERE password IS NULL OR password = ''")
        empty_count = cursor.fetchone()[0]
        
        print(f"\n✅ Database fixed!")
        print(f"   Entries with empty passwords: {empty_count}")
        
        # Show all entries
        cursor.execute("SELECT id, title, password FROM entries LIMIT 10")
        print("\n📋 Sample entries:")
        for row in cursor.fetchall():
            pwd_display = "***" if row[2] else "(empty)"
            print(f"   {row[0]}: {row[1]} - password: {pwd_display}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()
