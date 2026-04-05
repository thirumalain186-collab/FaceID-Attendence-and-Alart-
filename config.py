"""
Configuration Settings for Smart Attendance System v2
Loads configuration from environment variables for security
"""

import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use os.getenv directly

BASE_DIR = Path(__file__).parent

# Directories
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
UNKNOWN_DIR = BASE_DIR / "captured_alerts"
ATTENDANCE_DIR = BASE_DIR / "attendance_logs"
KNOWN_FACES_DIR = BASE_DIR / "known_faces"
REPORTS_DIR = BASE_DIR / "reports"
ATTENDANCE_PHOTOS_DIR = ATTENDANCE_DIR / "photos"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
for directory in [DATASET_DIR, TRAINER_DIR, UNKNOWN_DIR, ATTENDANCE_DIR, KNOWN_FACES_DIR, REPORTS_DIR, ATTENDANCE_PHOTOS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Haar Cascade
HAAR_CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
TRAINER_FILE = TRAINER_DIR / "trainer.yml"
ATTENDANCE_FILE = ATTENDANCE_DIR / "attendance.csv"

# Database
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "attendance.db")

# Email Configuration - FROM ENVIRONMENT VARIABLES
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "sender_email": os.getenv("SENDER_EMAIL", ""),
    "sender_password": os.getenv("SENDER_PASSWORD", ""),
    "class_advisor_email": os.getenv("CLASS_ADVISOR_EMAIL", ""),
    "hod_email": os.getenv("HOD_EMAIL", ""),
    "enabled": bool(os.getenv("EMAIL_ENABLED", "false").lower() == "true")
}

# Attendance Settings
ATTENDANCE_CONFIG = {
    "confidence_threshold": int(os.getenv("CONFIDENCE_THRESHOLD", "80")),
    "unknown_alert_cooldown": int(os.getenv("ALERT_COOLDOWN", "60")),
    "frame_skip": int(os.getenv("FRAME_SKIP", "3")),
    "camera_index": int(os.getenv("CAMERA_INDEX", "0")),
    "class_name": os.getenv("CLASS_NAME", "PTLE - Classroom"),
    "college_name": os.getenv("COLLEGE_NAME", "PTLE College"),
    "samples_per_person": int(os.getenv("SAMPLES_PER_PERSON", "30")),
    "image_size": (200, 200),
    "scale_factor": 1.3,
    "min_neighbors": 5,
    "min_face_size": (30, 30),
    "face_tolerance": 0.5
}

# Schedule Times
SCHEDULE_CONFIG = {
    "attendance_start": os.getenv("ATTENDANCE_START", "09:00"),
    "attendance_stop": os.getenv("ATTENDANCE_STOP", "09:30"),
    "day_end": os.getenv("DAY_END", "16:30"),
    "batch_days": int(os.getenv("BATCH_DAYS", "30"))
}

# Flask Settings
FLASK_SECRET_KEY = os.getenv("SECRET_KEY", "smart-attendance-v2-secret-key-2024")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Logging Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "attendance.log"
LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "5242880"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
