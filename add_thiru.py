"""
Add Thiru to database
"""
import sqlite3
import config
from datetime import datetime

def add_thiru():
    conn = sqlite3.connect(str(config.DB_PATH))
    c = conn.cursor()
    
    try:
        # Add Thiru to people table
        c.execute("""
            INSERT INTO people (name, role, roll_number, registered_at)
            VALUES (?, ?, ?, ?)
        """, ("Thiru", "student", "02", datetime.now().isoformat()))
        
        conn.commit()
        print("[OK] Thiru added to database")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to add Thiru: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    add_thiru()
