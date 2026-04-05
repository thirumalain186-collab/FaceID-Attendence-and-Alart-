"""
Reset Script - Remove all data from Smart Attendance System
"""

import os
import shutil
from pathlib import Path

def reset_system():
    """Remove all data and reset system"""
    
    print("=" * 50)
    print("  RESET SMART ATTENDANCE SYSTEM")
    print("=" * 50)
    
    confirm = input("\nThis will DELETE all data:\n- Registered faces\n- Trained model\n- Attendance records\n- Database\n\nAre you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\nRemoving data...")
    
    # Remove files
    files_to_remove = [
        'attendance.db',
        'attendance.csv',
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"  Removed: {file}")
    
    # Remove directories (ignore errors for locked files)
    dirs_to_remove = [
        'dataset',
        'trainer',
        'known_faces',
        'attendance_logs',
        'unknown_faces'
    ]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                print(f"  Removed: {dir_name}/")
            except:
                print(f"  Skipped (locked): {dir_name}/")
    
    # Recreate empty directories
    for dir_name in dirs_to_remove:
        os.makedirs(dir_name, exist_ok=True)
        print(f"  Created: {dir_name}/")
    
    print("\n" + "=" * 50)
    print("  ALL DATA REMOVED!")
    print("=" * 50)
    print("\nSystem is now fresh. Run:")
    print("  python register_faces.py  - to register new people")
    print("  python train.py          - to train the model")
    print("  python recognize.py      - to start attendance")

if __name__ == "__main__":
    reset_system()
