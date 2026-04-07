import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

print("\n" + "="*60)
print("DELETING ALL REGISTERED STUDENTS")
print("="*60 + "\n")

# Delete all people
cursor.execute("DELETE FROM people")
deleted = cursor.rowcount

conn.commit()

print(f"Deleted {deleted} students\n")

# Verify
cursor.execute("SELECT COUNT(*) FROM people")
remaining = cursor.fetchone()[0]

if remaining == 0:
    print("[SUCCESS] All students deleted! Database clean.\n")
else:
    print(f"[ERROR] {remaining} students still exist!\n")

conn.close()
