"""
Remove Raj from database
"""
import sqlite3
import config

def remove_raj():
    conn = sqlite3.connect(str(config.DB_PATH))
    c = conn.cursor()
    
    try:
        # Delete Raj from people table
        c.execute("DELETE FROM people WHERE name = ?", ("Raj",))
        conn.commit()
        print("[OK] Raj removed from database")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to remove Raj: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    remove_raj()
