# Science Expo Deployment Instructions

## System Status: READY ✅

Your face recognition attendance system is **production-ready for Science Expo**. All components are configured, tested, and working.

## What It Does

Your system automatically:
1. **Recognizes** 7 pre-registered students using AI
2. **Marks Attendance** when they appear before camera
3. **Detects Unknown Persons** (visitors, guests, unauthorized)
4. **Sends Email Alerts** to Class Advisor AND HOD with photos
5. **Logs Everything** to database for records

## Quick Deployment (5 minutes)

### Step 1: Ensure Python is installed
```bash
python --version
```
Should show Python 3.8 or higher.

### Step 2: Install dependencies (if not already installed)
```bash
pip install opencv-python numpy scipy scikit-learn pillow
```

### Step 3: Start the system
```bash
python run_monitoring.py
```

That's it! System is now running and monitoring.

## What Happens When Running

The system will:
1. Load the trained AI model (takes ~10-15 seconds)
2. Initialize camera
3. Start monitoring faces
4. Log all activities to console

```
✅ System starts
✅ Camera ready  
✅ 7 students registered
✅ Email alerts enabled
✅ Now monitoring...

When faces detected:
- Known student → Marked present automatically
- Unknown person → Email alert sent immediately with photo
```

## During the Event

### Monitor Setup
1. Position camera at entry/exit point
2. **Height:** Eye level (mounting bracket optional)
3. **Distance:** 1-2 meters from subjects
4. **Lighting:** Good natural/artificial light (no backlighting)
5. **Background:** Simple background preferred

### Let it Run
- Script keeps running automatically
- No manual operation needed
- Just observe the console for activity

### Email Notifications
- Unknown persons trigger immediate email
- Both Class Advisor and HOD receive emails with photos
- Check email to verify system is working
- Photos saved to `captured_alerts/` folder

## Testing Before Event

### Quick Test (5 minutes)
```bash
python science_expo_ready.py
```

This verifies:
- Model loaded ✓
- Camera working ✓
- 7 students registered ✓
- Email configured ✓
- Database ready ✓

### Full Test (15 minutes)
```bash
python run_monitoring.py
```

1. Stand in front of camera
2. Move your face around
3. Check console for face detection
4. Bring unknown person (if possible)
5. Verify email alert received

## Email Configuration

**Already configured - nothing to do!**

- Sender: `thirumalairaman0807@gmail.com`
- Class Advisor: `sousukeaizen0099@gmail.com`
- HOD: `skharishraj11@gmail.com`

Configuration file: `.env` (if you need to change it)

## File Structure

```
face id/
├── run_monitoring.py         ← START HERE
├── START.py                  ← Or use interactive menu
├── attendance.db             ← Database (auto-created)
├── trainer/
│   └── trainer.yml           ← AI model (pre-trained)
├── dataset/                  ← Training images (reference)
├── captured_alerts/          ← Unknown person photos
├── logs/                     ← System logs
└── attendance_logs/          ← Attendance records
```

## Database Access

View today's attendance:
```bash
python
>>> import sqlite3
>>> conn = sqlite3.connect('attendance.db')
>>> cursor = conn.cursor()
>>> cursor.execute('SELECT * FROM attendance WHERE DATE(date) = DATE("now")')
>>> for row in cursor.fetchall(): print(row)
```

## Troubleshooting

### Camera shows error
- Unplug/replug USB camera
- Try different USB port
- Use laptop's built-in camera as backup
- System continues (falls back to demo mode)

### Emails not arriving
- Check internet connection is active
- Verify email address in .env correct
- Check spam/junk folder
- Verify Gmail "Less secure apps" is enabled

### Face not recognized
- Come closer (1-2 meters optimal)
- Ensure face is clearly visible
- Good lighting (not backlit)
- Can detect multiple faces at once

### System slows down
- Reduce frame size in config
- Close other applications
- Ensure good computer performance
- Disable screen display if not needed

### Attendance not marking
- Check camera is getting frames
- Try manually testing face recognition
- Verify student name in database matches training data
- Check database permissions

## Deployment at Different Locations

### Scenario 1: Lab Computer (Today)
```bash
cd "C:\Users\thiru\OneDrive\Desktop\open code\face id"
python run_monitoring.py
```

### Scenario 2: School Computer
1. Copy folder to school computer
2. Open terminal/command prompt in that folder
3. Run: `python run_monitoring.py`
4. Done! (No reconfiguration needed)

### Scenario 3: Network Computer
1. Copy to shared network drive
2. Open terminal from that location
3. Run: `python run_monitoring.py`
4. System works with same config

### Scenario 4: USB Drive (Portable)
1. Copy entire folder to USB
2. Plug into any Windows PC with Python
3. Open terminal in folder
4. Run: `python run_monitoring.py`
5. Works immediately!

### Scenario 5: Laptop at Science Expo
1. Copy folder to laptop
2. Ensure camera connected
3. Ensure internet connection (for emails)
4. Start monitoring: `python run_monitoring.py`

## Before You Start

Checklist:
- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install opencv-python`
- [ ] Camera connected and working
- [ ] Internet connection active (for emails)
- [ ] `.env` file exists with email config
- [ ] `attendance.db` exists
- [ ] `trainer/trainer.yml` exists (AI model)

## Command Reference

```bash
# Start monitoring (MAIN COMMAND)
python run_monitoring.py

# Interactive menu
python START.py

# Test system
python science_expo_ready.py

# Test camera only
python test_camera_attendance.py

# View today's attendance
sqlite3 attendance.db "SELECT * FROM attendance WHERE DATE(date) = DATE('now');"
```

## Estimated Workflow for Science Expo

**Setup (Morning):**
1. Set up laptop/computer at display
2. Connect camera
3. Position camera at key viewing point
4. Open terminal: `python run_monitoring.py`
5. Verify system shows "Monitoring is running"

**During Event:**
1. Visitors/students stand in front of camera
2. System automatically detects and marks attendance
3. Unknown persons trigger email alerts
4. Event staff see emails on phone/tablet

**Cleanup (Evening):**
1. Press CTRL+C to stop system
2. Check `attendance_logs/` for day's records
3. Review emails received
4. Done! All data saved

## Important Notes

- System runs continuously until you press CTRL+C
- All data automatically saved to database
- Photos of unknown persons saved to `captured_alerts/`
- Emails sent automatically (requires internet)
- Works with multiple faces at once
- Can be deployed to any Windows PC with Python

## Success Indicators

When everything is working:
- ✅ Console shows "Monitoring is running"
- ✅ Console shows "[PREDICT]" logs when faces detected
- ✅ Console shows "[OK] Attendance marked" for known students
- ✅ Unknown person photos appear in `captured_alerts/`
- ✅ Emails received by Class Advisor and HOD

---

**Your system is ready for Science Expo. Deploy with confidence! 🎉**

Questions? Check QUICK_START.md or SCIENCE_EXPO_READY.md
