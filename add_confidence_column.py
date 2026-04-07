"""
Add confidence column to attendance table if it doesn't exist
"""
import sqlite3
import config

conn = sqlite3.connect(str(config.DB_PATH))
c = conn.cursor()

# Get table info
c.execute("PRAGMA table_info(attendance)")
columns = [row[1] for row in c.fetchall()]

print(f"Attendance table columns: {columns}")

if 'confidence' not in columns:
    print("Adding confidence column...")
    c.execute("ALTER TABLE attendance ADD COLUMN confidence REAL")
    conn.commit()
    print("Done!")
else:
    print("Confidence column already exists")

conn.close()
