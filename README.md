# Smart Attendance System with Face Recognition

A complete college project demonstrating face recognition-based attendance management using **OpenCV LBPH Face Recognizer only** (NO dlib, NO face_recognition library).

**Status:** ✅ **PRODUCTION READY FOR SCIENCE EXPO**

## 🚀 Quick Start (60 seconds)

```bash
# Start monitoring with email alerts
python run_monitoring.py

# Or use interactive menu
python START.py

# Or verify system first
python science_expo_ready.py
```

## Features

- **Face Registration**: Capture multiple face angles from webcam
- **LBPH Training**: Train using OpenCV's Local Binary Pattern Histogram
- **Real-time Recognition**: Live face detection and identification
- **Automatic Attendance**: Mark presence with timestamp
- **Unknown Detection**: Detect and alert unauthorized persons
- **Email Alerts**: Send alerts to Class Advisor and HOD
- **PDF Reports**: Daily, monthly, and security alert PDFs
- **30-Day Batch System**: Auto-renewal with reminders
- **Scheduled Tasks**: 9AM-4:30PM automated operation
- **SQLite Database**: Persistent storage with indexes
- **Structured Logging**: Centralized logging with rotation
- **Environment Variables**: Secure credential management
- **Web Dashboard**: Optional Flask-based web interface

## ✨ NEW: Monitoring Mode with Email Alerts (Science Expo Ready)

**Perfect for Science Expo deployment!**

- ✅ Continuous monitoring without manual interaction
- ✅ Automatic email alerts when unknown persons detected
- ✅ Photos of unauthorized persons attached to emails
- ✅ Sent to BOTH Class Advisor and HOD simultaneously
- ✅ Complete logging to database
- ✅ Works on any Windows PC with Python
- ✅ Ready for immediate deployment
- ✅ No configuration needed (pre-configured with email credentials)

## IMPORTANT: Constraints Met

- **NO dlib library**
- **NO face_recognition library**
- **ONLY OpenCV (LBPH Face Recognizer)**
- **Python 3.10+ compatible**

## Project Structure

```
smart_attendance/
│
├── config.py              # Configuration settings
├── main.py                # Main menu application
├── register_faces.py      # Face registration module
├── train.py               # Model training module
├── attendance_engine.py   # Core recognition engine
├── database.py            # SQLite database operations
├── scheduler.py           # APScheduler automated tasks
├── pdf_generator.py       # PDF report generation
├── email_sender.py        # Email notification system
├── logger.py              # Structured logging
│
├── dataset/               # Captured face images
├── trainer/               # Trained model files
├── unknown_faces/         # Unknown person snapshots
├── reports/               # Generated PDF reports
├── logs/                  # Application logs
│
├── attendance.db          # SQLite database
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── .gitignore             # Git exclusions
└── README.md              # Documentation
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup (SECURITY)

Copy the example environment file and configure your credentials:

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your credentials
```

Configure in `.env`:
```env
# Email Configuration
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
ADVISOR_EMAIL=advisor@college.edu
HOD_EMAIL=hod@college.edu

# Application Settings
CLASS_NAME=CS-A
COLLEGE_NAME=Your College Name
```

**Gmail App Password Setup:**
1. Enable 2-Factor Authentication on your Google account
2. Go to myaccount.google.com → Security → App passwords
3. Create a new app password for "Mail"
4. Use the 16-character password (with spaces)

### 3. Download Haar Cascade

Download `haarcascade_frontalface_default.xml` from:
```
https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
```

Or use the pre-downloaded file if available.

## Usage

### Quick Start

```bash
# Run the main application (with scheduler)
python main.py

# Or run individual modules
python register_faces.py   # Register new people
python train.py            # Train the model
python app.py              # Start web dashboard
```

### Step-by-Step Guide

#### Step 1: Register People
```bash
python main.py
# Choose option 4
# Enter name, roll number, role (student/teacher)
# Capture face images from different angles
```

#### Step 2: Train Model
```bash
python main.py
# Choose option 5
# Model saved to trainer/trainer.yml
```

#### Step 3: Start Attendance System
```bash
python main.py
# Scheduler starts automatically (9AM-4:30PM)
# Choose mode: Attendance (9AM-9:30AM) or Monitoring
```

### Automated Schedule

The scheduler runs these tasks automatically:

| Time | Task |
|------|------|
| 8:00 AM | Check batch expiry |
| 8:30 AM | Check batch reminders |
| 9:00 AM | Start attendance mode |
| 9:30 AM | Stop attendance, send daily report |
| 4:30 PM | End of day, stop camera |

### Controls

- **Q** - Quit
- **SPACE** - Capture face (during registration)
- **R** - Reload face database

## Menu Options

| Option | Description |
|--------|-------------|
| 1 | Start Attendance Mode |
| 2 | Start Monitoring Mode |
| 3 | Stop Camera |
| 4 | Register New Person |
| 5 | Train Model |
| 6 | Send Daily Report |
| 7 | Send Monthly Report |
| 8 | View Today's Attendance |
| 9 | View Alerts |
| 10 | Test Email |
| 11 | Exit |

## How It Works

### Face Registration
1. Captures 30 face images from webcam
2. Varies angles (straight, left, right, up, down)
3. Saves to `dataset/{name}_{role}/`
4. Registers in SQLite database

### Model Training
1. Loads all images from dataset
2. Extracts LBPH features
3. Trains SVM-based recognizer
4. Saves model to `trainer/trainer.yml`

### Recognition
1. Detects faces using Haar Cascade
2. Extracts LBPH features
3. Compares with trained model
4. Marks attendance if confidence > threshold

### Alert System
1. Unknown person detected
2. Captures and saves image
3. Sends email to Advisor and HOD
4. Logs alert in database

## Email Notifications

### Unknown Person Alert
- Sent when unrecognized person detected
- Includes captured image
- Addressed to Class Advisor and HOD

### Daily Report
- Sent on demand or end of session
- Includes attendance statistics
- Lists all present students/teachers

## Database Schema

### people
```sql
CREATE TABLE people (
    id INTEGER PRIMARY KEY,
    name TEXT,
    role TEXT,
    roll_number TEXT,
    email TEXT,
    class_name TEXT,
    registered_at TEXT
);
```

### attendance
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    person_id INTEGER,
    name TEXT,
    role TEXT,
    class_name TEXT,
    date TEXT,
    time_in TEXT,
    time_out TEXT,
    status TEXT,
    confidence REAL
);
```

### alerts
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    image_path TEXT,
    location TEXT,
    alert_sent INTEGER,
    notes TEXT
);
```

## Configuration Options

Edit `.env` for credentials (SECURE):

```env
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
ADVISOR_EMAIL=advisor@college.edu
HOD_EMAIL=hod@college.edu
CLASS_NAME=CS-A
COLLEGE_NAME=Your College Name
```

Edit `config.py` for system settings:

```python
# Recognition settings
ATTENDANCE_CONFIG = {
    "confidence_threshold": 70,  # Lower = stricter
    "unknown_alert_cooldown": 120,  # Seconds between alerts
    "frame_skip": 3,  # Process every Nth frame
    "camera_index": 0,  # Camera device
    "samples_per_person": 30,  # Images to capture
    "image_size": (150, 150),  # Face image size
    "min_face_size": (80, 80),  # Minimum detected face
    "class_name": "CS-A"  # Your class name
}

# Schedule settings
SCHEDULE_CONFIG = {
    "attendance_start": "9:00",
    "attendance_stop": "9:30",
    "day_end": "16:30"
}

# Logging settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 3
```

## Troubleshooting

### Camera not detected
```python
# Try different camera index in config.py
ATTENDANCE_CONFIG["camera_index"] = 1  # or 2
```

### Poor recognition
- Capture more images (30-50)
- Vary lighting and angles
- Ensure good lighting
- Lower confidence_threshold to 60

### Email not sending
- Use Gmail App Password (not regular password)
- Enable 2FA on Google account
- Check spam folder
- Run `python email_sender.py` to test

### Training fails
- Ensure at least one person registered
- Check images are valid JPG files
- Verify Haar cascade is present
- Run `python train.py` directly to see error

### Scheduler not working
- Check system time is correct
- Ensure APScheduler is installed
- Check logs/attendance.log for errors

### Database issues
- Delete attendance.db to reset
- Run `python database.py` to reinitialize

## Security Best Practices

1. **Never commit credentials**: Use `.env` file, not config.py
2. **Rotate App Passwords**: Change Gmail app password periodically
3. **Review logs**: Check logs/attendance.log for suspicious activity
4. **Update dependencies**: Keep packages updated

## Dependencies

This project uses ONLY these libraries:
- `opencv-contrib-python` - LBPH face recognition
- `numpy` - Numerical operations
- `Pillow` - Image processing
- `reportlab` - PDF generation
- `APScheduler` - Scheduled tasks
- `Flask` - Web dashboard
- `python-dotenv` - Environment variables

**NO dlib or face_recognition library!**

## Database Schema

The system uses SQLite with the following tables:
- `batches` - 30-day registration batches
- `people` - Registered students/teachers
- `attendance` - Daily attendance records
- `movement_log` - Entry/exit tracking
- `alerts` - Security alert history
- `settings` - Application settings

## License

MIT License - Free for educational use.

## Author

College Project - Smart Attendance System

---

**Built with OpenCV LBPH Face Recognizer** (NO dlib required)
