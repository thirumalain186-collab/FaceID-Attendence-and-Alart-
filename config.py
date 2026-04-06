"""
Configuration Settings for Smart Attendance System v2
Loads configuration from environment variables for security
"""

import os
import re
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

# Create directories with error handling
for directory in [DATASET_DIR, TRAINER_DIR, UNKNOWN_DIR, ATTENDANCE_DIR, KNOWN_FACES_DIR, REPORTS_DIR, ATTENDANCE_PHOTOS_DIR, LOGS_DIR]:
    try:
        directory.mkdir(exist_ok=True)
    except OSError as e:
        import sys
        print(f"Warning: Could not create directory {directory}: {e}", file=sys.stderr)

HAAR_CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
TRAINER_FILE = TRAINER_DIR / "trainer.yml"
ATTENDANCE_FILE = ATTENDANCE_DIR / "attendance.csv"

# Safe path handling - prevent path traversal
_db_path_env = os.getenv("DB_PATH", "attendance.db")
if os.path.isabs(_db_path_env):
    DB_PATH = Path(_db_path_env)
else:
    DB_PATH = BASE_DIR / _db_path_env


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


def _validate_time_format(value, default):
    """Validate time format (HH:MM). Returns default if invalid."""
    if not value:
        return default
    pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    if re.match(pattern, str(value)):
        return str(value)
    return default


def _get_env_or_fail(key, default, fallback_key=None):
    """Get env var, use fallback key, or return default."""
    value = os.getenv(key, os.getenv(fallback_key or key.upper(), default))
    return value


def _get_bool(value):
    """Safely parse boolean from environment."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return False


def _sanitize_string(value, max_length=200):
    """Sanitize string input - remove dangerous characters."""
    if not value:
        return ""
    return str(value)[:max_length].strip()


# Environment variable parsing
env_smtp_port = os.getenv("SMTP_PORT", "")
env_flask_port = os.getenv("FLASK_PORT", "")
env_confidence = os.getenv("CONFIDENCE_THRESHOLD", "")
env_cooldown = os.getenv("ALERT_COOLDOWN", "")
env_frame_skip = os.getenv("FRAME_SKIP", "")
env_camera_idx = os.getenv("CAMERA_INDEX", "")
env_samples = os.getenv("SAMPLES_PER_PERSON", "")
env_batch_days = os.getenv("BATCH_DAYS", "")
env_log_max_size = os.getenv("LOG_MAX_SIZE", "")

_email_enabled = _get_bool(os.getenv("EMAIL_ENABLED", "false"))
_email_sender = _sanitize_string(os.getenv("SENDER_EMAIL", ""), 100)
_email_password = os.getenv("SENDER_PASSWORD", "")
_secret_key = os.getenv("SECRET_KEY", "")

EMAIL_CONFIG = {
    "smtp_server": _sanitize_string(os.getenv("SMTP_SERVER", "smtp.gmail.com"), 100),
    "smtp_port": _validate_int(env_smtp_port, 587, 1, 65535),
    "sender_email": _email_sender,
    "sender_password": _email_password,
    "class_advisor_email": _sanitize_string(os.getenv("CLASS_ADVISOR_EMAIL", ""), 100),
    "hod_email": _sanitize_string(os.getenv("HOD_EMAIL", ""), 100),
    "enabled": _email_enabled,
    "smtp_timeout": _validate_int(os.getenv("SMTP_TIMEOUT", ""), 30, 5, 120),
    "smtp_retry_count": _validate_int(os.getenv("SMTP_RETRY_COUNT", ""), 3, 1, 5),
}

# Validate email addresses if provided
if _email_sender and "@" not in _email_sender:
    EMAIL_CONFIG["sender_email"] = ""

if EMAIL_CONFIG.get("class_advisor_email") and "@" not in EMAIL_CONFIG["class_advisor_email"]:
    EMAIL_CONFIG["class_advisor_email"] = ""

if EMAIL_CONFIG.get("hod_email") and "@" not in EMAIL_CONFIG["hod_email"]:
    EMAIL_CONFIG["hod_email"] = ""

ATTENDANCE_CONFIG = {
    "confidence_threshold": _validate_int(env_confidence, 65, 1, 100),
    "unknown_alert_cooldown": _validate_int(env_cooldown, 30, 10, 3600),
    "frame_skip": _validate_int(env_frame_skip, 3, 1, 30),
    "camera_index": _validate_int(env_camera_idx, 0, 0, 9),
    "class_name": _sanitize_string(os.getenv("CLASS_NAME", "PTLE - Classroom"), 50),
    "college_name": _sanitize_string(os.getenv("COLLEGE_NAME", "PTLE College"), 100),
    "samples_per_person": _validate_int(env_samples, 30, 5, 100),
    "image_size": (200, 200),
    "scale_factor": 1.1,
    "min_neighbors": 5,
    "min_face_size": (30, 30),
    "face_tolerance": 0.5,
    "movement_gap_seconds": _validate_int(os.getenv("MOVEMENT_GAP", ""), 5, 1, 300),
}

SCHEDULE_CONFIG = {
    "attendance_start": _validate_time_format(os.getenv("ATTENDANCE_START", "09:00"), "09:00"),
    "attendance_stop": _validate_time_format(os.getenv("ATTENDANCE_STOP", "09:30"), "09:30"),
    "day_end": _validate_time_format(os.getenv("DAY_END", "16:30"), "16:30"),
    "batch_days": _validate_int(env_batch_days, 30, 1, 365),
}

# Secure secret key - generate if not set or using default
_default_secret = "change-this-to-a-random-secret-key"
if _secret_key and _secret_key != _default_secret and len(_secret_key) >= 32:
    FLASK_SECRET_KEY = _secret_key
else:
    FLASK_SECRET_KEY = secrets.token_hex(32)

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = _validate_int(env_flask_port, 5000, 1, 65535)
FLASK_DEBUG = _get_bool(os.getenv("FLASK_DEBUG", "false"))

# Warn if debug mode is enabled
if FLASK_DEBUG:
    import sys
    print("WARNING: Flask debug mode is ENABLED. Do not use in production!", file=sys.stderr)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    LOG_LEVEL = "INFO"

LOG_FILE = LOGS_DIR / "attendance.log"
LOG_MAX_SIZE = _validate_int(env_log_max_size, 5242880, 1024, 104857600)
LOG_BACKUP_COUNT = _validate_int(os.getenv("LOG_BACKUP_COUNT", ""), 5, 1, 50)
