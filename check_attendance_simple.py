import sqlite3
from datetime import datetime

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

print("\n" + "="*70)
print("ATTENDANCE DATA CHECK")
print("="*70 + "\n")

# Check attendance records
print("RECENT ATTENDANCE RECORDS:")
print("-" * 70)
cursor.execute("SELECT id, person_id, name, date, time_in, status FROM attendance ORDER BY id DESC LIMIT 10")
records = cursor.fetchall()

if records:
    print(f"{'ID':3} {'PersonID':8} {'Name':15} {'Date':12} {'Time':8} {'Status':10}")
    print("-" * 70)
    for rec in records:
        print(f"{rec[0]:3} {rec[1]:8} {rec[2]:15} {rec[3]:12} {rec[4]:8} {rec[5]:10}")
else:
    print("NO RECORDS FOUND")

# Check today's records
print("\n\nTODAY'S ATTENDANCE:")
print("-" * 70)
today = datetime.now().strftime("%Y-%m-%d")
cursor.execute("SELECT person_id, name, COUNT(*) FROM attendance WHERE date = ? GROUP BY person_id", (today,))
today_records = cursor.fetchall()

if today_records:
    print(f"Date: {today}")
    for rec in today_records:
        print(f"  Person {rec[0]} ({rec[1]}): {rec[2]} records")
else:
    print(f"No records for today ({today})")

# Check all dates with records
print("\n\nDATES WITH ATTENDANCE:")
print("-" * 70)
cursor.execute("SELECT DISTINCT date FROM attendance ORDER BY date DESC LIMIT 10")
dates = cursor.fetchall()
if dates:
    for date in dates:
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (date[0],))
        count = cursor.fetchone()[0]
        print(f"  {date[0]}: {count} records")
else:
    print("No attendance records found")

print("\n" + "="*70 + "\n")
conn.close()
