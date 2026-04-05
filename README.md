# Smart Attendance System with Face Recognition

A complete college project demonstrating face recognition-based attendance management using **OpenCV LBPH Face Recognizer only** (NO dlib, NO face_recognition library).

## Features

- **Face Registration**: Capture multiple face angles from webcam
- **LBPH Training**: Train using OpenCV's Local Binary Pattern Histogram
- **Real-time Recognition**: Live face detection and identification
- **Automatic Attendance**: Mark presence with timestamp
- **Unknown Detection**: Detect and alert unauthorized persons
- **Email Alerts**: Send alerts to Class Advisor and HOD
- **Daily Reports**: Email attendance summary to stakeholders
- **SQLite Database**: Persistent storage of people and attendance
- **Web Dashboard**: Optional Flask-based web interface

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
├── email_alert.py         # Email notification system
│
├── dataset/               # Captured face images
├── trainer/               # Trained model files
├── unknown_faces/         # Unknown person snapshots
├── attendance_logs/       # CSV backup logs
├── known_faces/           # Reference images
│
├── attendance.db          # SQLite database
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── setup.bat              # Quick setup script
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Haar Cascade

Download `haarcascade_frontalface_default.xml` from:
```
https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
```

Or use the pre-downloaded file if available.

### 3. Configure Email (Optional)

Edit `config.py` or use the menu option:
```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",  # Gmail App Password
    "class_advisor_email": "advisor@college.edu",
    "hod_email": "hod@college.edu",
    "enabled": True
}
```

**Gmail App Password Setup:**
1. Enable 2-Factor Authentication on your Google account
2. Go to myaccount.google.com → Security → App passwords
3. Create a new app password for "Mail"
4. Use the 16-character password (with spaces)

## Usage

### Quick Start

```bash
# Run the main menu
python main.py

# Or run individual modules
python register_faces.py   # Register new people
python train.py            # Train the model
python main.py             # Start attendance
```

### Step-by-Step Guide

#### Step 1: Register People
```bash
python main.py
# Choose option 2
# Enter name, role (student/teacher/staff)
# Capture 30 face images from different angles
```

#### Step 2: Train Model
```bash
python main.py
# Choose option 3
# Model saved to trainer/trainer.yml
```

#### Step 3: Start Attendance
```bash
python main.py
# Choose option 1
# System starts live camera tracking
```

### Controls

- **Q** - Quit
- **R** - Reload face database
- **S** - Take screenshot

## Menu Options

| Option | Description |
|--------|-------------|
| 1 | Start Attendance Tracking |
| 2 | Register New Person |
| 3 | Train Face Model |
| 4 | View Today's Attendance |
| 5 | Send Daily Report |
| 6 | Configure Email |
| 7 | List Registered People |
| 8 | Test Camera |
| 9 | Exit |

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

Edit `config.py`:

```python
# Recognition settings
ATTENDANCE_CONFIG = {
    "confidence_threshold": 70,  # Lower = stricter
    "unknown_alert_cooldown": 120,  # Seconds between alerts
    "frame_skip": 3,  # Process every Nth frame
    "camera_index": 0,  # Camera device
    "samples_per_person": 30,  # Images to capture
    "class_name": "CS-A"  # Your class name
}

# LBPH parameters
LBPH_CONFIG = {
    "radius": 1,
    "neighbors": 8,
    "grid_x": 8,
    "grid_y": 8,
    "threshold": 100.0
}
```

## Troubleshooting

### Camera not detected
```python
# Try different camera index
ATTENDANCE_CONFIG["camera_index"] = 1  # or 2
```

### Poor recognition
- Capture more images (50-100)
- Vary lighting and angles
- Ensure good lighting
- Lower confidence_threshold to 60

### Email not sending
- Use Gmail App Password (not regular password)
- Enable 2FA on Google account
- Check spam folder

### Training fails
- Ensure at least one person registered
- Check images are valid JPG files
- Verify Haar cascade is present

## Tips for Best Results

1. **Lighting**: Use consistent, good lighting
2. **Angles**: Capture multiple face angles
3. **Expressions**: Vary expressions during registration
4. **Background**: Use simple, consistent background
5. **Distance**: Keep face 30-60cm from camera
6. **Glasses**: Include images with/without glasses

## Dependencies Only

This project uses ONLY these libraries:
- `opencv-python` - Face detection and recognition
- `numpy` - Numerical operations
- `Pillow` - Image processing
- `pandas` - Data analysis (optional)
- `flask` - Web dashboard (optional)

**NO dlib or face_recognition library!**

## License

MIT License - Free for educational use.

## Author

College Project - Smart Attendance System

---

**Built with OpenCV LBPH Face Recognizer** (NO dlib required)
