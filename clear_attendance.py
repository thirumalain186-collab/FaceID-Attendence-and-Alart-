"""
Clear today's attendance for fresh test
"""
import sqlite3
import config
from datetime import date

conn = sqlite3.connect(str(config.DB_PATH))
c = conn.cursor()

today = date.today().isoformat()
c.execute("DELETE FROM attendance WHERE date = ?", (today,))
conn.commit()

print(f"Cleared attendance for {today}")
conn.close()
