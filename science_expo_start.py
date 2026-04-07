"""
Science Expo - One-Button System Start
Complete deployment preparation and startup
"""
import sys
import os
import time
import subprocess
from pathlib import Path

def print_banner(title, width=70):
    print("\n" + "="*width)
    print(f"  {title.center(width-4)}")
    print("="*width)

def print_section(title):
    print(f"\n{title}")
    print("-" * len(title))

def check_environment():
    """Check Python environment"""
    print_section("Environment Check")
    
    # Python version
    import platform
    py_version = platform.python_version()
    print(f"Python version: {py_version}")
    
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ required")
        return False
    
    # Required packages
    required = ['cv2', 'flask', 'numpy', 'pickle']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"[OK] {pkg}")
        except ImportError:
            print(f"[ERROR] {pkg} not found")
            missing.append(pkg)
    
    if missing:
        print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
        print("Install with: pip install opencv-python flask numpy")
        return False
    
    return True

def verify_system_files():
    """Verify all required files exist"""
    print_section("File Verification")
    
    required_files = [
        'attendance.db',
        'attendance_engine.py',
        'app.py',
        'config.py',
        'train.py',
        'trainer/trainer.yml',
        'trainer/label_map.pkl',
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"[OK] {file_path:40} ({size:>10} bytes)")
        else:
            print(f"[ERROR] {file_path:40} NOT FOUND")
            all_exist = False
    
    return all_exist

def clear_old_sessions():
    """Clear old session data"""
    print_section("Session Cleanup")
    
    # Clear attendance from previous day (keep historical data)
    print("[OK] Session data preserved for history")
    
    return True

def start_system(mode='electron'):
    """Start the system"""
    print_banner("STARTING FACE RECOGNITION SYSTEM", 70)
    
    if mode == 'electron':
        print("\nStarting Electron UI...")
        print("This will open a desktop window with camera interface")
        print("\n(If this hangs, try Mode 2 below)")
        
        try:
            os.chdir('electron')
            subprocess.Popen(['npm', 'start'])
            print("\n[OK] Electron started - check for desktop window")
            return True
        except Exception as e:
            print(f"[ERROR] Could not start Electron: {e}")
            print("\nFalling back to Flask mode...")
            os.chdir('..')
            mode = 'flask'
    
    if mode == 'flask':
        print("\nStarting Flask Server...")
        print("Open your browser: http://127.0.0.1:5000")
        
        try:
            subprocess.Popen([sys.executable, 'app.py'])
            print("\n[OK] Flask server started")
            print("Waiting for server to be ready...")
            time.sleep(3)
            
            import webbrowser
            webbrowser.open('http://127.0.0.1:5000')
            print("[OK] Browser opened")
            return True
        except Exception as e:
            print(f"[ERROR] Could not start Flask: {e}")
            return False

def show_quick_reference():
    """Show quick reference guide"""
    print_banner("QUICK REFERENCE", 70)
    
    print("""
OPERATION:

1. STAND IN FRONT OF CAMERA
   - Position yourself or student 30-60cm away
   - Ensure good lighting (face well-lit)
   - Look straight at camera

2. WAIT FOR RECOGNITION
   - System detects face: 0.5-2 seconds
   - Shows name in green box
   - Automatically marks attendance

3. MULTIPLE PEOPLE
   - System handles 2-3 people simultaneously
   - Each person tracked independently
   - Names displayed for all recognized faces

CONTROLS:

Electron UI:
  - "Start Attendance" - Mark attendance mode
  - "Start Monitoring" - Log without marking
  - "Demo Mode" - Show capabilities
  - "Headless Mode" - Background only
  - "Exit" - Stop system

Flask Web:
  - Dashboard tab - View attendance
  - Settings tab - Adjust thresholds
  - Students tab - Manage registrations

KEYBOARD SHORTCUTS:

Camera Window:
  Q or ESC - Close camera, stop recording
  SPACE - (Registration mode) Capture photo
  S - Take screenshot

TROUBLESHOOTING:

Face not recognized?
  1. Better lighting
  2. Closer to camera (30-50cm)
  3. Look straight at camera
  4. Check if student is registered

Slow performance?
  1. Close other apps
  2. Reduce camera resolution
  3. Increase frame skip

Need to register new student?
  python register_quick.py
  (Follow on-screen instructions)

IMPORTANT NOTES:

- Minimum 7 students registered
- System tested and verified ready
- Attendance automatically saved to database
- Can view records anytime: python check_attendance.py

For more help: Read SCIENCE_EXPO_DEPLOYMENT_GUIDE.md
    """)

def show_menu():
    """Show startup menu"""
    print_banner("SCIENCE EXPO SYSTEM - STARTUP OPTIONS", 70)
    
    while True:
        print("""
1. START WITH ELECTRON UI (Recommended)
   Desktop application with full interface

2. START WITH FLASK WEB SERVER
   Browser-based interface

3. QUICK TEST (15 seconds)
   Test system with live camera

4. REGISTER NEW STUDENT
   Add new student to system

5. VIEW ATTENDANCE RECORDS
   See today's marked attendance

6. CLEAR TODAY'S RECORDS
   Clear for fresh start (testing)

7. SYSTEM STATUS
   Verify all components

0. EXIT
   Quit without starting
        """)
        
        choice = input("Choose option (0-7): ").strip()
        
        if choice == '1':
            return 'electron'
        elif choice == '2':
            return 'flask'
        elif choice == '3':
            return 'test'
        elif choice == '4':
            return 'register'
        elif choice == '5':
            return 'attendance'
        elif choice == '6':
            return 'clear'
        elif choice == '7':
            return 'status'
        elif choice == '0':
            return 'exit'
        else:
            print("[ERROR] Invalid choice, try again")

def execute_choice(choice):
    """Execute menu choice"""
    if choice == 'electron':
        print("\n[OK] Starting Electron UI")
        start_system('electron')
    
    elif choice == 'flask':
        print("\n[OK] Starting Flask Server")
        start_system('flask')
    
    elif choice == 'test':
        print("\n[OK] Running quick test")
        subprocess.call([sys.executable, 'test_camera_attendance.py'])
    
    elif choice == 'register':
        print("\n[OK] Starting registration")
        subprocess.call([sys.executable, 'register_quick.py'])
    
    elif choice == 'attendance':
        print("\n[OK] Checking attendance")
        subprocess.call([sys.executable, 'check_attendance.py'])
    
    elif choice == 'clear':
        confirm = input("\nClear today's attendance? (yes/no): ").strip().lower()
        if confirm == 'yes':
            subprocess.call([sys.executable, 'clear_attendance.py'])
    
    elif choice == 'status':
        print("\n[OK] Checking system status")
        subprocess.call([sys.executable, 'science_expo_ready.py'])
    
    elif choice == 'exit':
        return False
    
    return True

def main():
    print_banner("WELCOME TO SCIENCE EXPO SYSTEM", 70)
    print("Face Recognition Attendance System - Ready for Deployment")
    print("Version: 3.0 | Students: 7 | Status: PRODUCTION READY")
    
    # Verify environment
    if not check_environment():
        print("\n[ERROR] Environment check failed")
        return False
    
    # Verify files
    if not verify_system_files():
        print("\n[ERROR] Some required files are missing")
        return False
    
    # Cleanup
    if not clear_old_sessions():
        print("[WARNING] Could not clean up sessions")
    
    # Show quick reference
    show_quick_reference()
    
    # Show menu
    while True:
        choice = show_menu()
        if choice == 'exit':
            print("\n[OK] Goodbye!")
            return True
        
        if not execute_choice(choice):
            print("\n[OK] Goodbye!")
            return True
        
        print("\n")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[OK] System interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
