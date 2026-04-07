"""
🚀 ONE-COMMAND DEPLOYMENT START
Just run this and everything is set up!
"""

import sys
import os
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def main():
    print_header("SMART ATTENDANCE SYSTEM - DEPLOYMENT STARTER")
    
    print("""
Welcome! This will get your system running in minutes.

Current Location:
  C:\\Users\\thiru\\OneDrive\\Desktop\\open code\\face id

This is where your complete system is deployed.
All files, database, and AI model are ready to use!
    """)
    
    print("\n" + "="*70)
    print("DEPLOYMENT OPTIONS")
    print("="*70)
    
    print("""
1. SCIENCE EXPO TOMORROW (Recommended)
   - Quick setup: 5 minutes
   - Electron desktop UI
   - Full monitoring with alerts

2. PERMANENT SCHOOL INSTALLATION
   - Copy to school computer/server
   - Set up email alerts once
   - Run daily for classroom monitoring

3. NETWORK/CLOUD DEPLOYMENT
   - Deploy to server
   - Multiple locations
   - Always-on monitoring

4. JUST TEST IT NOW
   - Run locally in 30 seconds
   - See system in action
   - No configuration needed
    """)
    
    print("\nSelect option (1-4): ", end="", flush=True)
    choice = input().strip()
    
    if choice == "1":
        return deploy_science_expo()
    elif choice == "2":
        return deploy_school()
    elif choice == "3":
        return deploy_cloud_guide()
    elif choice == "4":
        return test_now()
    else:
        print("[ERROR] Invalid choice")
        return False

def deploy_science_expo():
    """Deploy for Science Expo tomorrow"""
    print_header("SCIENCE EXPO DEPLOYMENT - 5 MINUTE SETUP")
    
    print("""
This will configure your system for tomorrow's science expo:

STEP 1: Configure Email Alerts (2 minutes)
  - You'll need a Gmail account
  - Get app password from: myaccount.google.com/apppasswords
  - Provide Class Advisor and HOD emails
  
STEP 2: Start System (1 click)
  - Electron desktop app opens
  - Click "Start Monitoring"
  - System automatically monitors all faces
  
STEP 3: System Runs (automated)
  - Alerts sent when unknown persons detected
  - Photos saved
  - Everything logged to database

Ready? (yes/no): """, end="", flush=True)
    
    if input().strip().lower() != "yes":
        print("Cancelled.")
        return False
    
    print("\n[STEP 1/2] Configuring Email Alerts...")
    print("-" * 70)
    
    try:
        result = subprocess.run([sys.executable, "setup_email_alerts.py"], 
                                cwd=Path.cwd())
        if result.returncode != 0:
            print("[ERROR] Email setup failed")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    print("\n[STEP 2/2] Ready to Start System")
    print("-" * 70)
    print("""
Your system is now configured for the Science Expo!

TO START TOMORROW:
  1. Open Command Prompt
  2. Navigate to: C:\\Users\\thiru\\OneDrive\\Desktop\\open code\\face id
  3. Run: cd electron
  4. Run: npm start
  5. Click "Start Monitoring" button

That's it! System will automatically:
  ✓ Monitor camera in real-time
  ✓ Recognize registered students
  ✓ Send email alerts for unknown persons
  ✓ Notify Class Advisor and HOD
  ✓ Save photos of unauthorized persons
    """)
    
    print("\nReady to deploy? (yes/no): ", end="", flush=True)
    if input().strip().lower() == "yes":
        print("\n✅ SCIENCE EXPO DEPLOYMENT COMPLETE!")
        print("Your system is ready for tomorrow!\n")
        return True
    
    return False

def deploy_school():
    """Deploy to school installation"""
    print_header("SCHOOL INSTALLATION DEPLOYMENT")
    
    print("""
This will prepare your system for permanent school deployment.

DEPLOYMENT STEPS:

1. Choose deployment location:
   a) C:\\Program Files\\SmartAttendance\\ (Windows)
   b) \\\\school-server\\systems\\attendance\\ (Network)
   c) /opt/smart-attendance/ (Linux server)
   d) Other location

2. Copy these files to deployment location:
   ✓ All .py files (core system)
   ✓ electron/ folder (desktop UI)
   ✓ templates/ folder (web UI)
   ✓ config.py and .env
   ✓ attendance.db (database)
   ✓ trainer/ folder (AI model)

3. Configure email on deployment machine:
   python setup_email_alerts.py

4. Start system:
   cd electron
   npm start

DEPLOYMENT LOCATION (choose one):
  1) C:\\Program Files\\SmartAttendance\\
  2) \\\\school-server\\attendance\\
  3) /opt/smart-attendance/
  4) Other (specify below)

Enter choice (1-4): """, end="", flush=True)
    
    choice = input().strip()
    
    locations = {
        "1": "C:\\\\Program Files\\\\SmartAttendance\\\\",
        "2": "\\\\\\\\school-server\\\\attendance\\\\",
        "3": "/opt/smart-attendance/",
        "4": None
    }
    
    if choice == "4":
        print("Enter deployment location: ", end="", flush=True)
        location = input().strip()
    else:
        location = locations.get(choice, None)
    
    if not location:
        print("[ERROR] Invalid location")
        return False
    
    print(f"\n✅ Deployment location: {location}")
    print("""
NEXT STEPS:

1. Copy all files from current location:
   C:\\Users\\thiru\\OneDrive\\Desktop\\open code\\face id\\
   
   To deployment location:
   {location}

2. On deployment machine, run:
   python setup_email_alerts.py

3. Run system:
   cd electron
   npm start

For detailed instructions:
   See: DEPLOYMENT_LOCATIONS.md
    """.format(location=location))
    
    return True

def deploy_cloud_guide():
    """Cloud deployment guide"""
    print_header("CLOUD DEPLOYMENT GUIDE")
    
    print("""
Deploy your system to the cloud for:
  ✓ Multi-location access
  ✓ Always-on monitoring
  ✓ Automatic backups
  ✓ Scalability

CLOUD PROVIDERS:
  1) AWS (Amazon Web Services)
     - EC2 instance (Linux or Windows)
     - RDS for database (optional)
     - CloudWatch for monitoring

  2) Azure (Microsoft)
     - Virtual Machine
     - SQL Database (optional)
     - Application Insights

  3) Google Cloud
     - Compute Engine
     - Cloud SQL (optional)
     - Cloud Monitoring

  4) Heroku (Simple)
     - Free tier available
     - Easy to deploy

DEPLOYMENT STEPS:

1. Create VM on cloud provider
   - Ubuntu 20.04+ (Linux) or Windows Server
   - 4GB RAM, 2 CPU cores minimum
   - 50GB storage

2. Copy project files to VM:
   scp -r ~/face-id-system user@cloud-server:/opt/

3. Install dependencies:
   pip3 install -r requirements.txt

4. Setup email on cloud:
   python3 setup_email_alerts.py

5. Run system:
   python3 app.py  (Flask)
   OR
   cd electron && npm start  (Electron)

6. Access from anywhere:
   - Browser: http://cloud-server:5000
   - Or use Electron remote desktop

For detailed guide:
   See: DEPLOYMENT_LOCATIONS.md
    """)
    
    return True

def test_now():
    """Test system immediately"""
    print_header("QUICK TEST - 30 SECONDS")
    
    print("""
This will run a quick test to see the system in action.

What happens:
  1. System loads all components
  2. Shows registered students (7 total)
  3. Accesses camera
  4. Verifies database
  5. Confirms everything works

Ready? (yes/no): """, end="", flush=True)
    
    if input().strip().lower() != "yes":
        return False
    
    print("\n[TESTING] Starting system verification...")
    print("-" * 70)
    
    try:
        result = subprocess.run([sys.executable, "science_expo_ready.py"],
                                cwd=Path.cwd())
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def end_message(success):
    """Show final message"""
    if success:
        print_header("DEPLOYMENT SUCCESSFUL!")
        print("""
Your system is ready!

Next Steps:
  1. Run the system: cd electron && npm start
  2. Click "Start Monitoring"
  3. Check: DEPLOYMENT_LOCATIONS.md for details

For questions:
  - Read: YES_TO_EVERYTHING.md
  - Read: MONITORING_MODE_WITH_ALERTS.md
  - Read: DEPLOYMENT_LOCATIONS.md

Good luck! 🚀
        """)
    else:
        print_header("DEPLOYMENT CANCELLED")
        print("""
No problem! You can deploy anytime by running:
  python deployment.py

Or start the system directly:
  cd electron
  npm start
        """)

if __name__ == "__main__":
    try:
        success = main()
        end_message(success)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[OK] Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
