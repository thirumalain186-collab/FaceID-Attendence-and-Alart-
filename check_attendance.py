import database
from datetime import date

today = date.today()
attendance = database.get_attendance_by_date_range(today.isoformat(), today.isoformat())
print(f'Attendance records for {today}: {len(attendance)}')
for rec in attendance:
    print(f'  - {rec.get("name")} ({rec.get("roll_number")}): {rec.get("time_in")}')
