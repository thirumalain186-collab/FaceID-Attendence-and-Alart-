# Troubleshooting Guide

## Common Issues and Solutions

### 1. Camera Not Detected

**Symptoms:**
- "Cannot open camera" error
- Black screen in preview
- Camera index out of range

**Solutions:**
```python
# Try different camera index (0, 1, 2...)
# Edit config.py:
ATTENDANCE_CONFIG["camera_index"] = 1
```

```bash
# Verify camera works with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL'); cap.release()"
```

**Additional checks:**
- [ ] Camera is not in use by another application
- [ ] USB camera is properly connected
- [ ] Camera drivers are up to date
- [ ] Try running as administrator

---

### 2. Poor Recognition Accuracy

**Symptoms:**
- Low confidence scores
- False recognitions
- Missing detections

**Solutions:**

1. **Improve Training Data:**
```bash
# Capture more images with varied conditions
python register_faces.py
# Capture 50-100 images per person
```

2. **Adjust Configuration:**
```python
# Edit config.py - lower threshold = stricter recognition
ATTENDANCE_CONFIG["confidence_threshold"] = 70  # Default: 80
```

3. **Improve Image Quality:**
- Use better lighting (avoid backlighting)
- Position face 30-60cm from camera
- Capture multiple angles and expressions
- Keep background simple

4. **Retrain Model:**
```bash
python train.py
```

---

### 3. Email Not Sending

**Symptoms:**
- Email functions fail silently
- "Authentication failed" error
- "Connection refused" error

**Solutions:**

1. **Verify App Password (Gmail):**
   - Enable 2-Factor Authentication on Google Account
   - Go to: myaccount.google.com → Security → App passwords
   - Create new app password for "Mail"
   - Use the 16-character password in `.env`

2. **Check SMTP Settings:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ENABLED=true
```

3. **Test Email:**
```bash
python -c "from email_sender import test_email; test_email()"
```

4. **Check Firewall/Antivirus:**
   - Temporarily disable firewall to test
   - Allow Python through firewall

---

### 4. Database Errors

**Symptoms:**
- "Database locked" error
- "Table not found" error
- Corrupted data

**Solutions:**

1. **Reset Database:**
```bash
del attendance.db
python -c "import database; database.init_database()"
```

2. **Fix Permissions:**
```bash
# Windows
icacls attendance.db /grant Everyone:F

# Linux
chmod 666 attendance.db
```

3. **Close Connections:**
   - Ensure no other processes are using the database
   - Restart the application

---

### 5. Training Failures

**Symptoms:**
- "No images found" error
- Empty trainer file
- Crash during training

**Solutions:**

1. **Check Dataset:**
```bash
# Verify folder structure
ls dataset/
# Should contain: Name_RollNumber_Role/
# Example: john_doe_cs001_student/
```

2. **Verify Images:**
```python
from PIL import Image
import os

for folder in os.listdir('dataset'):
    for img in os.listdir(f'dataset/{folder}'):
        try:
            Image.open(f'dataset/{folder}/{img}').verify()
        except:
            print(f"Corrupted: {folder}/{img}")
```

3. **Re-register Person:**
```bash
# Delete person
python delete_person.py

# Re-register
python register_faces.py
```

---

### 6. OpenCV Installation Issues

**Symptoms:**
- "Import cv2 error"
- Missing DLL files
- OpenCV contrib modules not found

**Solutions:**

```bash
# Uninstall existing OpenCV
pip uninstall opencv-python opencv-contrib-python

# Install correct version
pip install opencv-contrib-python==4.8.0.74
```

---

### 7. Scheduler Not Working

**Symptoms:**
- Tasks not running at scheduled time
- "Scheduler already running" error

**Solutions:**

1. **Check System Time:**
   - Ensure system clock is accurate
   - Check timezone settings

2. **Restart Scheduler:**
```python
import scheduler
scheduler.stop_scheduler()
scheduler.init_scheduler()
```

3. **Check Logs:**
```bash
# View logs for scheduler errors
type logs\attendance.log | findstr /i scheduler
```

---

### 8. PDF Generation Fails

**Symptoms:**
- Empty or corrupted PDF
- ReportLab import error

**Solutions:**
```bash
# Reinstall ReportLab
pip uninstall reportlab
pip install reportlab==4.0.7
```

---

### 9. Flask App Not Starting

**Symptoms:**
- "Address already in use"
- Module import errors
- Template not found

**Solutions:**

1. **Check Port:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process
taskkill /PID <pid> /F
```

2. **Reinstall Flask:**
```bash
pip install flask==3.0.0
```

---

### 10. Face Detection Issues

**Symptoms:**
- Face not detected
- Multiple faces detected
- Detection too slow

**Solutions:**
```python
# Adjust detection parameters in config.py
ATTENDANCE_CONFIG = {
    "scale_factor": 1.1,      # Smaller = slower but more accurate
    "min_neighbors": 5,       # Higher = fewer false positives
    "min_face_size": (30, 30)  # Minimum face size to detect
}
```

---

## Getting Help

If issues persist:

1. Check `logs/attendance.log` for detailed errors
2. Run with debug mode enabled
3. Create an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - System information
   - Log file contents

---

## Emergency Reset

To completely reset the system:
```bash
# Stop all running processes
taskkill /IM python.exe /F

# Delete database and data
del attendance.db
del trainer\trainer.yml
rmdir /s /q dataset
rmdir /s /q logs
rmdir /s /q reports

# Recreate directories
mkdir dataset trainer logs reports

# Reinstall if needed
pip install -r requirements.txt
```
