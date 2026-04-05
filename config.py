"""
Configuration Settings for Smart Attendance System v2
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Directories
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
UNKNOWN_DIR = BASE_DIR / "captured_alerts"
ATTENDANCE_DIR = BASE_DIR / "attendance_logs"
KNOWN_FACES_DIR = BASE_DIR / "known_faces"
REPORTS_DIR = BASE_DIR / "reports"
ATTENDANCE_PHOTOS_DIR = ATTENDANCE_DIR / "photos"

# Create directories
for directory in [DATASET_DIR, TRAINER_DIR, UNKNOWN_DIR, ATTENDANCE_DIR, KNOWN_FACES_DIR, REPORTS_DIR, ATTENDANCE_PHOTOS_DIR]:
    directory.mkdir(exist_ok=True)

# Haar Cascade
HAAR_CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
TRAINER_FILE = TRAINER_DIR / "trainer.yml"
ATTENDANCE_FILE = ATTENDANCE_DIR / "attendance.csv"

# Database
DB_PATH = BASE_DIR / "attendance.db"

# Email Configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "thirumalairaman0807@gmail.com",
    "sender_password": "tgkt oeti upjk vohg",
    "class_advisor_email": "5115252ai026@ptleecncet.com",
    "hod_email": "sousukeaizen0099@gmail.com",
    "enabled": True
}

# Attendance Settings
ATTENDANCE_CONFIG = {
    "confidence_threshold": 80,
    "unknown_alert_cooldown": 60,
    "frame_skip": 3,
    "camera_index": 0,
    "class_name": "PTLE - Classroom",
    "college_name": "PTLE College",
    "samples_per_person": 30,
    "image_size": (200, 200),
    "scale_factor": 1.3,
    "min_neighbors": 5,
    "min_face_size": (30, 30),
    "face_tolerance": 0.5
}

# Schedule Times
SCHEDULE_CONFIG = {
    "attendance_start": "09:00",
    "attendance_stop": "09:30",
    "day_end": "16:30",
    "batch_days": 30
}

# Flask Settings
FLASK_SECRET_KEY = "smart-attendance-v2-secret-2024"
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
