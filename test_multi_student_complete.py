"""
Test Multi-Student Recognition and Attendance
Tests recognition with multiple faces simultaneously
"""
import cv2
import sys
from attendance_engine import AttendanceEngine

def main():
    print("\n" + "="*60)
    print("MULTI-STUDENT RECOGNITION TEST")
    print("="*60)
    print("\nThis test will:")
    print("  - Detect multiple faces simultaneously")
    print("  - Recognize and track each face")
    print("  - Mark attendance for recognized students")
    print("  - Display names on camera feed")
    print("\nPress Q to stop the test\n")
    
    # Initialize engine
    engine = AttendanceEngine(mode='LIVE')
    if not engine.load_resources():
        print("[ERROR] Failed to load resources")
        return False
    
    print(f"Loaded {len(engine.label_map)} registered students:")
    for label, name in engine.label_map.items():
        print(f"  Label {label}: {name}")
    
    print("\nStarting multi-student recognition (30 seconds)...")
    print("="*60 + "\n")
    
    # Start camera in attendance mode
    engine.start_camera(mode='ATTENDANCE', duration=30)
    
    # Show results
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    # Check attendance
    import sqlite3
    from datetime import date
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('''
        SELECT p.name, p.roll_number, a.time, a.confidence
        FROM attendance a
        JOIN people p ON a.person_id = p.id
        WHERE DATE(a.date) = ?
        ORDER BY a.time DESC
    ''', (today,))
    
    attendance = cursor.fetchall()
    conn.close()
    
    print(f"\nAttendance marked today ({today}):")
    if attendance:
        for name, roll, time, conf in attendance:
            print(f"  {name:15} ({roll}) - {time:8} - Conf: {conf:.2f}")
        print(f"\nTotal: {len(set([a[0] for a in attendance]))} unique students")
    else:
        print("  No attendance recorded")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
