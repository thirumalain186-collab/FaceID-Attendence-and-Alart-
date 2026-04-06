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
            status TEXT DEFAULT 'active'
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
    """Get person ID by name (case-insensitive)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM people WHERE name=? COLLATE NOCASE AND active=1", (name,))
    row = c.fetchone()
    return row['id'] if row else None


def create_batch():
    """Create a new batch with 30-day validity"""
    conn = get_connection()
    c = conn.cursor()
    
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    
    c.execute("""
        INSERT INTO batches (start_date, end_date, class_name, status)
        VALUES (?, ?, ?, 'active')
    """, (start_date.isoformat(), end_date.isoformat(), config.ATTENDANCE_CONFIG["class_name"]))
    
    batch_id = c.lastrowid
    conn.commit()
    
    return batch_id


def get_active_batch():
    """Get the currently active batch"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM batches WHERE status='active' ORDER BY id DESC LIMIT 1")
    batch = c.fetchone()
    return dict(batch) if batch else None


def get_batch_progress():
    """Get progress info for active batch"""
    batch = get_active_batch()
    if not batch:
        return None
    
    start_date = datetime.strptime(batch['start_date'], "%Y-%m-%d").date()
    end_date = datetime.strptime(batch['end_date'], "%Y-%m-%d").date()
    today = date.today()
    
    days_total = (end_date - start_date).days
    days_elapsed = (today - start_date).days + 1
    days_remaining = (end_date - today).days
    
    return {
        'id': batch['id'],
        'start_date': batch['start_date'],
        'end_date': batch['end_date'],
        'days_total': days_total,
        'days_elapsed': days_elapsed,
        'days_remaining': max(0, days_remaining),
        'is_last_day': days_remaining <= 1
    }


def close_batch(batch_id):
    """Close a batch"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE batches SET status='closed' WHERE id=?", (batch_id,))
    conn.commit()


def add_person(name, role, roll_number="", email="", batch_id=None):
    """Add a new person to the database"""
    conn = get_connection()
    c = conn.cursor()
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch['id'] if batch else None
    
    c.execute("""
        INSERT INTO people (name, role, roll_number, email, class_name, batch_id, active, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    """, (name, role, roll_number, email, config.ATTENDANCE_CONFIG["class_name"], 
          batch_id, datetime.now().isoformat()))
    
    person_id = c.lastrowid
    conn.commit()
    
    return person_id


def get_active_people():
    """Get all active people"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, role, roll_number, email, class_name, registered_at FROM people WHERE active=1 ORDER BY name")
    rows = c.fetchall()
    return [tuple(row) for row in rows]


def get_person_by_name(name):
    """Get person by name (case-insensitive)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM people WHERE name=? COLLATE NOCASE AND active=1", (name,))
    row = c.fetchone()
    return dict(row) if row else None


def remove_person(name):
    """Mark person as inactive (soft delete)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE people SET active=0 WHERE name=? COLLATE NOCASE", (name,))
    conn.commit()


def mark_attendance(name, roll_number="", batch_id=None, confidence=None):
    """Mark attendance for a person (case-insensitive)."""
    conn = get_connection()
    c = conn.cursor()
    
    today = date.today().isoformat()
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch['id'] if batch else None
    
    person_id = _get_person_id_by_name(name)
    
    try:
        c.execute("""
            INSERT INTO attendance (person_id, name, roll_number, date, time_in, status, batch_id, confidence)
            VALUES (?, ?, ?, ?, ?, 'present', ?, ?)
        """, (person_id, name, roll_number, today, current_time, batch_id, confidence))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False


def get_today_attendance():
    """Get today's attendance records"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT * FROM attendance WHERE date=? ORDER BY time_in", (today,))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_attendance_by_date_range(start_date, end_date):
    """Get attendance records by date range"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM attendance 
        WHERE date BETWEEN ? AND ? 
        ORDER BY date, time_in
    """, (start_date, end_date))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_attendance_summary(start_date, end_date):
    """Get attendance summary per student"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, roll_number, COUNT(*) as days_present,
               SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present_days
        FROM attendance 
        WHERE date BETWEEN ? AND ?
        GROUP BY name COLLATE NOCASE
    """, (start_date, end_date))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def log_movement(name, role, event_type, batch_id=None):
    """Log entry/exit movement."""
    valid_events = {'entry', 'exit'}
    if event_type not in valid_events:
        logger.warning(f"Invalid event_type: {event_type}")
        return
    
    conn = get_connection()
    c = conn.cursor()
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch['id'] if batch else None
    
    person_id = _get_person_id_by_name(name)
    
    c.execute("""
        INSERT INTO movement_log (person_id, name, role, timestamp, event_type, batch_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (person_id, name, role, datetime.now().isoformat(), event_type, batch_id))
    
    conn.commit()


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
    conn = get_connection()
    c = conn.cursor()
    end_inclusive = (datetime.strptime(end_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
    c.execute("""
        SELECT * FROM movement_log
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp
    """, (start_date, end_inclusive))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def save_alert(image_path, pdf_path, location):
    """Save alert to database"""
    conn = get_connection()
    c = conn.cursor()
    
    alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    c.execute("""
        INSERT INTO alerts (timestamp, image_path, pdf_path, location, alert_sent, alert_id)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (datetime.now().isoformat(), image_path, pdf_path, location, alert_id))
    
    alert_db_id = c.lastrowid
    conn.commit()
    
    return alert_db_id, alert_id


def mark_alert_sent(alert_id):
    """Mark alert as sent"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE alerts SET alert_sent=1 WHERE id=?", (alert_id,))
    conn.commit()


def get_recent_alerts(limit=20):
    """Get recent alerts"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    return [dict(row) for row in rows]


def get_setting(key, default=None):
    """Get a setting value"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    return row['value'] if row else default


def set_setting(key, value):
    """Set a setting value"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


def get_all_settings():
    """Get all settings as dict"""
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
    
    c.execute("SELECT COUNT(DISTINCT LOWER(name)) FROM people WHERE active=1 AND LOWER(role)='student'")
    total_students = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM people WHERE active=1 AND LOWER(role)='teacher'")
    total_teachers = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM alerts WHERE DATE(timestamp)=?", (today,))
    alerts_today = c.fetchone()[0] or 0
    
    c.execute("""
        SELECT COUNT(DISTINCT LOWER(a.name))
        FROM attendance a
        WHERE a.date=? AND EXISTS (
            SELECT 1 FROM people p
            WHERE LOWER(p.name)=LOWER(a.name) AND p.active=1 AND LOWER(p.role)='student'
        )
    """, (today,))
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


if __name__ == "__main__":
    init_database()
    logger.info("Database module ready")
