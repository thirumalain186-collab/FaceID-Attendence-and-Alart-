"""
Configuration Settings for Smart Attendance System v2
Loads configuration from environment variables for security
"""

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

for directory in [DATASET_DIR, TRAINER_DIR, UNKNOWN_DIR, ATTENDANCE_DIR, KNOWN_FACES_DIR, REPORTS_DIR, ATTENDANCE_PHOTOS_DIR, LOGS_DIR]:
    try:
        directory.mkdir(exist_ok=True)
    except OSError as e:
        import sys
        print(f"Warning: Could not create directory {directory}: {e}", file=sys.stderr)

HAAR_CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
TRAINER_FILE = TRAINER_DIR / "trainer.yml"
ATTENDANCE_FILE = ATTENDANCE_DIR / "attendance.csv"

DB_PATH = BASE_DIR / os.getenv("DB_PATH", "attendance.db")


def _validate_int(value, default, min_val=None, max_val=None):
    """Safely parse and validate integer from environment."""
    try:
        parsed = int(value)
        if min_val is not None and parsed < min_val:
            return min_val
        if max_val is not None and parsed > max_val:
            return max_val
        return parsed
    except (ValueError, TypeError):
        return default


def _get_env_or_fail(key, default, fallback_key=None):
    """Get env var, use fallback key, or return default. Fails gracefully."""
    value = os.getenv(key, os.getenv(fallback_key or key.upper(), default))
    return value


def _get_bool(value):
    """Safely parse boolean from environment."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return False


env_smtp_port = os.getenv("SMTP_PORT", "")
env_flask_port = os.getenv("FLASK_PORT", "")
env_confidence = os.getenv("CONFIDENCE_THRESHOLD", "")
env_cooldown = os.getenv("ALERT_COOLDOWN", "")
env_frame_skip = os.getenv("FRAME_SKIP", "")
env_camera_idx = os.getenv("CAMERA_INDEX", "")
env_samples = os.getenv("SAMPLES_PER_PERSON", "")
env_batch_days = os.getenv("BATCH_DAYS", "")
env_log_max_size = os.getenv("LOG_MAX_SIZE", "")

_email_enabled = os.getenv("EMAIL_ENABLED", "false")
_email_sender = os.getenv("SENDER_EMAIL", "")
_secret_key = os.getenv("SECRET_KEY", "")

EMAIL_CONFIG = {
    "smtp_server": _get_env_or_fail("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": _validate_int(env_smtp_port, 587, 1, 65535),
    "sender_email": _email_sender,
    "sender_password": os.getenv("SENDER_PASSWORD", ""),
    "class_advisor_email": os.getenv("CLASS_ADVISOR_EMAIL", ""),
    "hod_email": os.getenv("HOD_EMAIL", ""),
    "enabled": _get_bool(_email_enabled),
    "smtp_timeout": _validate_int(os.getenv("SMTP_TIMEOUT", ""), 30, 5, 120),
    "smtp_retry_count": _validate_int(os.getenv("SMTP_RETRY_COUNT", ""), 3, 1, 5),
}

if _email_sender and _email_sender not in ("", "your_email@gmail.com"):
    EMAIL_CONFIG["sender_email"] = _email_sender

ATTENDANCE_CONFIG = {
    "confidence_threshold": _validate_int(env_confidence, 80, 1, 100),
    "unknown_alert_cooldown": _validate_int(env_cooldown, 60, 10, 3600),
    "frame_skip": _validate_int(env_frame_skip, 3, 1, 30),
    "camera_index": _validate_int(env_camera_idx, 0, 0, 9),
    "class_name": _get_env_or_fail("CLASS_NAME", "PTLE - Classroom"),
    "college_name": _get_env_or_fail("COLLEGE_NAME", "PTLE College"),
    "samples_per_person": _validate_int(env_samples, 30, 5, 100),
    "image_size": (200, 200),
    "scale_factor": 1.3,
    "min_neighbors": 5,
    "min_face_size": (30, 30),
    "face_tolerance": 0.5,
    "movement_gap_seconds": _validate_int(os.getenv("MOVEMENT_GAP", ""), 5, 1, 300),
}

SCHEDULE_CONFIG = {
    "attendance_start": os.getenv("ATTENDANCE_START", "09:00"),
    "attendance_stop": os.getenv("ATTENDANCE_STOP", "09:30"),
    "day_end": os.getenv("DAY_END", "16:30"),
    "batch_days": _validate_int(env_batch_days, 30, 1, 365),
}

FLASK_SECRET_KEY = _secret_key if _secret_key and _secret_key != "change-this-to-a-random-secret-key" else secrets.token_hex(32)
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = _validate_int(env_flask_port, 5000, 1, 65535)
FLASK_DEBUG = _get_bool(os.getenv("FLASK_DEBUG", "false"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "attendance.log"
LOG_MAX_SIZE = _validate_int(env_log_max_size, 5242880, 1024, 104857600)
LOG_BACKUP_COUNT = _validate_int(os.getenv("LOG_BACKUP_COUNT", ""), 5, 1, 50)
