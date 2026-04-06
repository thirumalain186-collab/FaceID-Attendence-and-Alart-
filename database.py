"""
Database Module for Smart Attendance System v2
All SQLite database operations
"""

import sqlite3
import threading
from datetime import datetime, date, timedelta
from pathlib import Path
import config
from logger import get_logger

logger = get_logger()

_thread_local = threading.local()

# Constants
STATUS_ACTIVE = 'active'
STATUS_CLOSED = 'closed'
STATUS_PRESENT = 'present'
STATUS_ABSENT = 'absent'
STATUS_LATE = 'late'
ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'
EVENT_ENTRY = 'entry'
EVENT_EXIT = 'exit'


def _open_conn(conn):
    """Configure connection with proper settings."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_connection():
    """Get thread-local database connection."""
    if not hasattr(_thread_local, 'conn') or _thread_local.conn is None:
        conn = sqlite3.connect(
            str(config.DB_PATH),
            check_same_thread=False,
            timeout=30.0,
            isolation_level='DEFERRED',
        )
        _thread_local.conn = _open_conn(conn)
    return _thread_local.conn


def close_connection():
    """Close thread-local database connection."""
    if hasattr(_thread_local, 'conn') and _thread_local.conn:
        try:
            _thread_local.conn.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
        finally:
            _thread_local.conn = None


def _safe_name(name):
    """Sanitize name input - prevent SQL injection and invalid data."""
    if not name or not isinstance(name, str):
        return None
    return str(name).strip()[:100]


def _validate_date(date_str, fmt="%Y-%m-%d"):
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, fmt).date()
    except (ValueError, TypeError):
        return None


def init_database():
    """Initialize database with schema."""
    conn = sqlite3.connect(str(config.DB_PATH), timeout=30.0)
    conn = _open_conn(conn)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            class_name TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed'))
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher')),
            roll_number TEXT COLLATE NOCASE,
            email TEXT,
            class_name TEXT,
            batch_id INTEGER,
            active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
            registered_at TEXT,
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            UNIQUE(name, batch_id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT NOT NULL COLLATE NOCASE,
            roll_number TEXT COLLATE NOCASE,
            date TEXT NOT NULL,
            time_in TEXT NOT NULL,
            status TEXT DEFAULT 'present' CHECK(status IN ('present', 'absent', 'late')),
            batch_id INTEGER,
            confidence REAL,
            FOREIGN KEY (person_id) REFERENCES people(id),
            UNIQUE(person_id, date)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS movement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT NOT NULL COLLATE NOCASE,
            role TEXT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('entry', 'exit')),
            batch_id INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            image_path TEXT,
            pdf_path TEXT,
            location TEXT,
            alert_sent INTEGER DEFAULT 0 CHECK(alert_sent IN (0, 1)),
            alert_id TEXT UNIQUE
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_person_date ON attendance(person_id, date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_movement_timestamp ON movement_log(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_movement_person ON movement_log(person_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_people_active ON people(active)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_people_batch ON people(batch_id)")
    
    conn.commit()
    conn.close()
    logger.info("Database initialized with indexes and constraints")


def _get_person_id_by_name(name):
    """Get person ID by name (case-insensitive). Returns None if not found."""
    safe_name = _safe_name(name)
    if not safe_name:
        return None
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM people WHERE name=? COLLATE NOCASE AND active=1", (safe_name,))
    row = c.fetchone()
    return row['id'] if row else None


def create_batch():
    """Create a new batch. Returns batch_id or None on failure."""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        start_date = date.today()
        batch_days = config.SCHEDULE_CONFIG.get("batch_days", 30)
        end_date = start_date + timedelta(days=batch_days)
        
        c.execute("""
            INSERT INTO batches (start_date, end_date, class_name, status)
            VALUES (?, ?, ?, ?)
        """, (start_date.isoformat(), end_date.isoformat(), 
              config.ATTENDANCE_CONFIG.get("class_name", ""), STATUS_ACTIVE))
        
        batch_id = c.lastrowid
        conn.commit()
        logger.info(f"Created new batch: {batch_id}")
        return batch_id
    except Exception as e:
        logger.error(f"Failed to create batch: {e}")
        return None


def get_active_batch():
    """Get the currently active batch. Returns dict or None."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM batches WHERE status=? ORDER BY id DESC LIMIT 1", (STATUS_ACTIVE,))
    batch = c.fetchone()
    return dict(batch) if batch else None


def get_batch_progress():
    """Get progress info for active batch. Returns dict or None."""
    batch = get_active_batch()
    if not batch:
        return None
    
    start = _validate_date(batch.get('start_date', ''))
    end = _validate_date(batch.get('end_date', ''))
    today = date.today()
    
    if start is None or end is None:
        logger.warning(f"Invalid batch dates: {batch}")
        return None
    
    days_total = (end - start).days
    days_elapsed = (today - start).days + 1
    days_remaining = (end - today).days
    
    return {
        'id': batch.get('id'),
        'start_date': batch.get('start_date'),
        'end_date': batch.get('end_date'),
        'days_total': max(1, days_total),
        'days_elapsed': max(1, days_elapsed),
        'days_remaining': max(0, days_remaining),
        'is_last_day': days_remaining <= 1,
        'is_expired': days_remaining < 0
    }


def close_batch(batch_id):
    """Close a batch. Returns True on success."""
    if not batch_id:
        return False
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE batches SET status=? WHERE id=?", (STATUS_CLOSED, batch_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to close batch: {e}")
        return False


def add_person(name, role, roll_number="", email="", batch_id=None):
    """Add a new person. Returns person_id or None on failure."""
    safe_name = _safe_name(name)
    if not safe_name:
        logger.warning("Invalid name provided")
        return None
    
    if role not in (ROLE_STUDENT, ROLE_TEACHER):
        logger.warning(f"Invalid role: {role}")
        return None
    
    try:
        conn = get_connection()
        c = conn.cursor()
        
        if batch_id is None:
            batch = get_active_batch()
            batch_id = batch.get('id') if batch else None
        
        c.execute("""
            INSERT INTO people (name, role, roll_number, email, class_name, batch_id, active, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (safe_name, role, _safe_name(roll_number) or "", 
              _safe_name(email) or "", config.ATTENDANCE_CONFIG.get("class_name", ""),
              batch_id, datetime.now().isoformat()))
        
        person_id = c.lastrowid
        conn.commit()
        logger.info(f"Added person: {safe_name} (ID: {person_id})")
        return person_id
    except sqlite3.IntegrityError as e:
        logger.warning(f"Person already exists: {safe_name}")
        return None
    except Exception as e:
        logger.error(f"Failed to add person: {e}")
        return None


def get_active_people():
    """Get all active people. Returns list of dicts."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, role, roll_number, email, class_name, registered_at 
        FROM people WHERE active=1 ORDER BY name
    """)
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_person_by_name(name):
    """Get person by name (case-insensitive). Returns dict or None."""
    safe_name = _safe_name(name)
    if not safe_name:
        return None
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM people WHERE name=? COLLATE NOCASE AND active=1", (safe_name,))
    row = c.fetchone()
    return dict(row) if row else None


def remove_person(name):
    """Mark person as inactive (soft delete). Returns True on success."""
    safe_name = _safe_name(name)
    if not safe_name:
        return False
    
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE people SET active=0 WHERE name=? COLLATE NOCASE", (safe_name,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to remove person: {e}")
        return False


def mark_attendance(name, roll_number="", batch_id=None, confidence=None):
    """Mark attendance for a person. Returns True if marked, False if already marked."""
    safe_name = _safe_name(name)
    if not safe_name:
        return False
    
    conn = get_connection()
    c = conn.cursor()
    
    today = date.today().isoformat()
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch.get('id') if batch else None
    
    person_id = _get_person_id_by_name(safe_name)
    
    try:
        c.execute("""
            INSERT INTO attendance (person_id, name, roll_number, date, time_in, status, batch_id, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (person_id, safe_name, _safe_name(roll_number) or "", today, 
              current_time, STATUS_PRESENT, batch_id, confidence))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Failed to mark attendance: {e}")
        conn.rollback()
        return False


def get_today_attendance(limit=None, offset=0):
    """Get today's attendance records. Optional pagination."""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    
    if limit:
        c.execute("""
            SELECT * FROM attendance WHERE date=? ORDER BY time_in LIMIT ? OFFSET ?
        """, (today, limit, offset))
    else:
        c.execute("SELECT * FROM attendance WHERE date=? ORDER BY time_in", (today,))
    
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_attendance_by_date_range(start_date, end_date, limit=None, offset=0):
    """Get attendance records by date range. Optional pagination."""
    start = _validate_date(start_date)
    end = _validate_date(end_date)
    
    if not start or not end:
        logger.warning(f"Invalid date range: {start_date} to {end_date}")
        return []
    
    conn = get_connection()
    c = conn.cursor()
    
    if limit:
        c.execute("""
            SELECT * FROM attendance 
            WHERE date >= ? AND date <= ?
            ORDER BY date, time_in
            LIMIT ? OFFSET ?
        """, (start.isoformat(), end.isoformat(), limit, offset))
    else:
        c.execute("""
            SELECT * FROM attendance 
            WHERE date >= ? AND date <= ?
            ORDER BY date, time_in
        """, (start.isoformat(), end.isoformat()))
    
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_attendance_summary(start_date, end_date):
    """Get attendance summary per student."""
    start = _validate_date(start_date)
    end = _validate_date(end_date)
    
    if not start or not end:
        return []
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, roll_number, COUNT(*) as days_present,
               SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present_days
        FROM attendance 
        WHERE date >= ? AND date <= ?
        GROUP BY name COLLATE NOCASE
    """, (start.isoformat(), end.isoformat()))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def log_movement(name, role, event_type, batch_id=None):
    """Log entry/exit movement. Returns True on success."""
    valid_events = {EVENT_ENTRY, EVENT_EXIT}
    if event_type not in valid_events:
        logger.warning(f"Invalid event_type: {event_type}")
        return False
    
    safe_name = _safe_name(name)
    if not safe_name:
        return False
    
    try:
        conn = get_connection()
        c = conn.cursor()
        
        if batch_id is None:
            batch = get_active_batch()
            batch_id = batch.get('id') if batch else None
        
        person_id = _get_person_id_by_name(safe_name)
        
        c.execute("""
            INSERT INTO movement_log (person_id, name, role, timestamp, event_type, batch_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (person_id, safe_name, role, datetime.now().isoformat(), event_type, batch_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to log movement: {e}")
        return False


def get_today_movement():
    """Get today's movement log."""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    next_day = (date.today() + timedelta(days=1)).isoformat()
    
    c.execute("""
        SELECT * FROM movement_log
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp
    """, (today, next_day))
    
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_movement_by_date_range(start_date, end_date):
    """Get movement log by date range."""
    start = _validate_date(start_date)
    end = _validate_date(end_date)
    
    if not start or not end:
        return []
    
    conn = get_connection()
    c = conn.cursor()
    end_inclusive = (end + timedelta(days=1)).isoformat()
    
    c.execute("""
        SELECT * FROM movement_log
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp
    """, (start.isoformat(), end_inclusive))
    
    rows = c.fetchall()
    return [dict(row) for row in rows]


def save_alert(image_path, pdf_path, location):
    """Save alert to database. Returns (alert_db_id, alert_id) or (None, None)."""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        c.execute("""
            INSERT INTO alerts (timestamp, image_path, pdf_path, location, alert_sent, alert_id)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (datetime.now().isoformat(), str(image_path)[:500] if image_path else "",
              str(pdf_path)[:500] if pdf_path else "", str(location)[:200] if location else "",
              alert_id))
        
        alert_db_id = c.lastrowid
        conn.commit()
        return alert_db_id, alert_id
    except Exception as e:
        logger.error(f"Failed to save alert: {e}")
        return None, None


def mark_alert_sent(alert_id):
    """Mark alert as sent. Returns True on success."""
    if not alert_id:
        return False
    
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE alerts SET alert_sent=1 WHERE id=?", (alert_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to mark alert sent: {e}")
        return False


def get_recent_alerts(limit=20):
    """Get recent alerts."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (max(1, limit),))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_setting(key, default=None):
    """Get a setting value. Returns default if not found."""
    if not key:
        return default
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (str(key),))
    row = c.fetchone()
    return row['value'] if row else default


def set_setting(key, value):
    """Set a setting value. Returns True on success."""
    if not key:
        return False
    
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                  (str(key), str(value) if value else ""))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to set setting: {e}")
        return False


def get_all_settings():
    """Get all settings as dict."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    rows = c.fetchall()
    return {row['key']: row['value'] for row in rows}


def get_stats():
    """Get dashboard statistics."""
    conn = get_connection()
    c = conn.cursor()
    
    today = date.today().isoformat()
    
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present_today = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM people WHERE active=1")
    total_people = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT LOWER(name)) FROM people WHERE active=1 AND LOWER(role)=?",
               (ROLE_STUDENT,))
    total_students = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM people WHERE active=1 AND LOWER(role)=?",
               (ROLE_TEACHER,))
    total_teachers = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM alerts WHERE DATE(timestamp)=?", (today,))
    alerts_today = c.fetchone()[0] or 0
    
    c.execute("""
        SELECT COUNT(DISTINCT LOWER(a.name))
        FROM attendance a
        WHERE a.date=? AND EXISTS (
            SELECT 1 FROM people p
            WHERE LOWER(p.name)=LOWER(a.name) AND p.active=1 AND LOWER(p.role)=?
        )
    """, (today, ROLE_STUDENT))
    present_students = c.fetchone()[0] or 0
    
    attendance_rate = round((present_students / total_students * 100), 1) if total_students > 0 else 0
    
    return {
        'present_today': present_today,
        'total_people': total_people,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'alerts_today': alerts_today,
        'present_students': present_students,
        'attendance_rate': attendance_rate,
        'date': today
    }


def backup_database(backup_path=None):
    """Create a backup of the database. Returns backup path or None."""
    if backup_path is None:
        backup_dir = config.REPORTS_DIR
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"backup_{timestamp}.db"
    
    try:
        source = sqlite3.connect(str(config.DB_PATH))
        dest = sqlite3.connect(str(backup_path))
        source.backup(dest)
        source.close()
        dest.close()
        logger.info(f"Database backed up to: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return None


if __name__ == "__main__":
    init_database()
    logger.info("Database module ready")
