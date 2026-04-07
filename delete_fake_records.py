import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

print("\nDeleting fake attendance records...\n")

# Delete all attendance records
cursor.execute("DELETE FROM attendance")
deleted = cursor.rowcount

conn.commit()

print(f"Deleted {deleted} fake records")
print("\nVerifying deletion...")

cursor.execute("SELECT COUNT(*) FROM attendance")
remaining = cursor.fetchone()[0]

print(f"Records remaining: {remaining}")

if remaining == 0:
    print("\n[SUCCESS] All fake records deleted! Database is clean.\n")
else:
    print(f"\n[ERROR] {remaining} records still exist!\n")

conn.close()
