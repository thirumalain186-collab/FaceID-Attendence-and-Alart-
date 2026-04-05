"""
Reset Script - Remove all data from Smart Attendance System
"""

import os
import shutil
from pathlib import Path
from logger import get_logger

logger = get_logger()


def reset_system():
    """Remove all data and reset system"""
    
    logger.warning("Starting system reset")
    print("=" * 50)
    print("  RESET SMART ATTENDANCE SYSTEM")
    print("=" * 50)
    
    confirm = input("\nThis will DELETE all data:\n- Registered faces\n- Trained model\n- Attendance records\n- Database\n\nAre you sure? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        logger.info("Reset cancelled by user")
        return
    
    logger.info("Removing data...")
    
    files_to_remove = [
        'attendance.db',
        'attendance.csv',
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            logger.info(f"Removed: {file}")
    
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
                logger.info(f"Removed: {dir_name}/")
            except Exception as e:
                logger.warning(f"Skipped (locked): {dir_name}/ - {e}")
    
    for dir_name in dirs_to_remove:
        os.makedirs(dir_name, exist_ok=True)
        logger.info(f"Created: {dir_name}/")
    
    logger.info("System reset complete")
    print("\n" + "=" * 50)
    print("  ALL DATA REMOVED!")
    print("=" * 50)

if __name__ == "__main__":
    reset_system()
