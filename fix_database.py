"""
fix_database.py - Add missing columns to existing database
Run this once to fix the database schema
"""

import sqlite3

def fix_database():
    db_path = "vaultkeeper.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Existing columns: {columns}")
        
        # Add missing columns
        missing_columns = []
        
        if 'attachments' not in columns:
            missing_columns.append("attachments TEXT")
            cursor.execute("ALTER TABLE entries ADD COLUMN attachments TEXT")
            print("✓ Added 'attachments' column")
        
        if 'custom_fields' not in columns:
            missing_columns.append("custom_fields TEXT")
            cursor.execute("ALTER TABLE entries ADD COLUMN custom_fields TEXT")
            print("✓ Added 'custom_fields' column")
        
        if 'tags' not in columns:
            missing_columns.append("tags TEXT")
            cursor.execute("ALTER TABLE entries ADD COLUMN tags TEXT")
            print("✓ Added 'tags' column")
        
        if 'expiry_date' not in columns:
            missing_columns.append("expiry_date INTEGER")
            cursor.execute("ALTER TABLE entries ADD COLUMN expiry_date INTEGER")
            print("✓ Added 'expiry_date' column")
        
        if 'password_strength' not in columns:
            missing_columns.append("password_strength INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE entries ADD COLUMN password_strength INTEGER DEFAULT 0")
            print("✓ Added 'password_strength' column")
        
        if 'folder_id' not in columns:
            missing_columns.append("folder_id INTEGER DEFAULT NULL")
            cursor.execute("ALTER TABLE entries ADD COLUMN folder_id INTEGER DEFAULT NULL")
            print("✓ Added 'folder_id' column")
        
        conn.commit()
        
        if missing_columns:
            print(f"\n✅ Database fixed! Added: {missing_columns}")
        else:
            print("\n✅ Database already has all columns!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_database()
