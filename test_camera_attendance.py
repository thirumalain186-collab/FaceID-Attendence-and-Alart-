"""
Test live camera with attendance marking
"""
import cv2
import numpy as np
from attendance_engine import AttendanceEngine, get_engine
import database
import time

print("="*60)
print("TESTING LIVE CAMERA WITH ATTENDANCE")
print("="*60)

# Get singleton engine
engine = get_engine()

print(f"\nStarting camera in ATTENDANCE mode...")
print(f"Stand in front of camera for 15 seconds")
print(f"Press CTRL+C to stop")

# Clear marked_today to allow re-marking
engine.marked_today.clear()

try:
    # Start camera in attendance mode
    engine.start_camera(mode="attendance", demo_mode=False, headless=False)
    
    # Let it run for 15 seconds
    for i in range(15):
        print(f"[{i+1}/15] Running... marked_today={list(engine.marked_today)}")
        time.sleep(1)
    
    # Stop camera
    engine.stop_camera()
    print(f"\nCamera stopped")
    
    # Check attendance
    print(f"\nChecking attendance records...")
    today_attendance = database.get_attendance_today()
    print(f"Today's attendance ({len(today_attendance)} records):")
    for record in today_attendance:
        print(f"  - {record.get('name')} ({record.get('roll_number')}): {record.get('time_in')}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
except KeyboardInterrupt:
    print("\nStopped by user")
    engine.stop_camera()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    engine.stop_camera()
