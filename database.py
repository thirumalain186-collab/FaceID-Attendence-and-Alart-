"""
Database Module for Smart Attendance System v2
All SQLite database operations
"""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
import config
from logger import get_logger

logger = get_logger()


def get_connection():
    """Get database connection"""
    return sqlite3.connect(str(config.DB_PATH))


def init_database():
    """Initialize database with schema"""
    conn = get_connection()
    c = conn.cursor()
    
    # Batches table
    c.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            class_name TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # People table
    c.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            roll_number TEXT,
            email TEXT,
            class_name TEXT,
            batch_id INTEGER,
            active INTEGER DEFAULT 1,
            registered_at TEXT,
            FOREIGN KEY (batch_id) REFERENCES batches(id)
        )
    """)
    
    # Attendance table
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT,
            roll_number TEXT,
            date TEXT,
            time_in TEXT,
            status TEXT DEFAULT 'present',
            batch_id INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    
    # Movement log table
    c.execute("""
        CREATE TABLE IF NOT EXISTS movement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT,
            role TEXT,
            timestamp TEXT,
            event_type TEXT,
            batch_id INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    
    # Alerts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            image_path TEXT,
            pdf_path TEXT,
            location TEXT,
            alert_sent INTEGER DEFAULT 0,
            alert_id TEXT
        )
    """)
    
    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Create indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_name ON attendance(name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_movement_timestamp ON movement_log(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_people_active ON people(active)")
    
    conn.commit()
    conn.close()
    logger.info("Database initialized with indexes")


# ============ BATCH FUNCTIONS ============

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
    conn.close()
    
    return batch_id


def get_active_batch():
    """Get the currently active batch"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM batches WHERE status='active' ORDER BY id DESC LIMIT 1")
    batch = c.fetchone()
    conn.close()
    return batch


def get_batch_progress():
    """Get progress info for active batch"""
    batch = get_active_batch()
    if not batch:
        return None
    
    start_date = datetime.strptime(batch[1], "%Y-%m-%d").date()
    end_date = datetime.strptime(batch[2], "%Y-%m-%d").date()
    today = date.today()
    
    days_total = (end_date - start_date).days
    days_elapsed = (today - start_date).days + 1
    days_remaining = (end_date - today).days
    
    return {
        'id': batch[0],
        'start_date': batch[1],
        'end_date': batch[2],
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
    conn.close()


# ============ PEOPLE FUNCTIONS ============

def add_person(name, role, roll_number="", email="", batch_id=None):
    """Add a new person to the database"""
    conn = get_connection()
    c = conn.cursor()
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch[0] if batch else None
    
    c.execute("""
        INSERT INTO people (name, role, roll_number, email, class_name, batch_id, active, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    """, (name, role, roll_number, email, config.ATTENDANCE_CONFIG["class_name"], 
          batch_id, datetime.now().isoformat()))
    
    person_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return person_id


def get_active_people():
    """Get all active people"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM people WHERE active=1 ORDER BY name")
    people = c.fetchall()
    conn.close()
    return people


def get_person_by_name(name):
    """Get person by name"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM people WHERE name=? AND active=1", (name,))
    person = c.fetchone()
    conn.close()
    return person


def remove_person(name):
    """Mark person as inactive (soft delete)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE people SET active=0 WHERE name=?", (name,))
    conn.commit()
    conn.close()


# ============ ATTENDANCE FUNCTIONS ============

def mark_attendance(name, roll_number="", batch_id=None):
    """Mark attendance for a person"""
    conn = get_connection()
    c = conn.cursor()
    
    today = date.today().isoformat()
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch[0] if batch else None
    
    # Check if already marked today
    c.execute("SELECT id FROM attendance WHERE name=? AND date=?", (name, today))
    if c.fetchone():
        conn.close()
        return False
    
    c.execute("""
        INSERT INTO attendance (person_id, name, roll_number, date, time_in, status, batch_id)
        VALUES (?, ?, ?, ?, ?, 'present', ?)
    """, (None, name, roll_number, today, current_time, batch_id))
    
    conn.commit()
    conn.close()
    return True


def get_today_attendance():
    """Get today's attendance records"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT * FROM attendance WHERE date=? ORDER BY time_in", (today,))
    records = c.fetchall()
    conn.close()
    return records


def get_attendance_by_date_range(start_date, end_date):
    """Get attendance records by date range"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM attendance 
        WHERE date BETWEEN ? AND ? 
        ORDER BY date, time_in
    """, (start_date, end_date))
    records = c.fetchall()
    conn.close()
    return records


def get_attendance_summary(start_date, end_date):
    """Get attendance summary per student"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, roll_number, COUNT(*) as days_present,
               SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present_days
        FROM attendance 
        WHERE date BETWEEN ? AND ?
        GROUP BY name
    """, (start_date, end_date))
    records = c.fetchall()
    conn.close()
    return records


# ============ MOVEMENT LOG FUNCTIONS ============

def log_movement(name, role, event_type, batch_id=None):
    """Log entry/exit movement"""
    conn = get_connection()
    c = conn.cursor()
    
    if batch_id is None:
        batch = get_active_batch()
        batch_id = batch[0] if batch else None
    
    c.execute("""
        INSERT INTO movement_log (person_id, name, role, timestamp, event_type, batch_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (None, name, role, datetime.now().isoformat(), event_type, batch_id))
    
    conn.commit()
    conn.close()


def get_today_movement():
    """Get today's movement log"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT * FROM movement_log 
        WHERE DATE(timestamp)=? 
        ORDER BY timestamp
    """, (today,))
    records = c.fetchall()
    conn.close()
    return records


def get_movement_by_date_range(start_date, end_date):
    """Get movement log by date range"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM movement_log 
        WHERE DATE(timestamp) BETWEEN ? AND ?
        ORDER BY timestamp
    """, (start_date, end_date))
    records = c.fetchall()
    conn.close()
    return records


# ============ ALERTS FUNCTIONS ============

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
    conn.close()
    
    return alert_db_id, alert_id


def mark_alert_sent(alert_id):
    """Mark alert as sent"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE alerts SET alert_sent=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()


def get_recent_alerts(limit=20):
    """Get recent alerts"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
    alerts = c.fetchall()
    conn.close()
    return alerts


# ============ SETTINGS FUNCTIONS ============

def get_setting(key, default=None):
    """Get a setting value"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    """Set a setting value"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_all_settings():
    """Get all settings as dict"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    rows = c.fetchall()
    conn.close()
    return dict(rows)


# ============ STATS FUNCTIONS ============

def get_stats():
    """Get dashboard statistics"""
    conn = get_connection()
    c = conn.cursor()
    
    today = date.today().isoformat()
    
    # Today's attendance count
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present_today = c.fetchone()[0] or 0
    
    # Total active people
    c.execute("SELECT COUNT(*) FROM people WHERE active=1")
    total_people = c.fetchone()[0] or 0
    
    # Active students
    c.execute("SELECT COUNT(*) FROM people WHERE active=1 AND role='student'")
    total_students = c.fetchone()[0] or 0
    
    # Active teachers
    c.execute("SELECT COUNT(*) FROM people WHERE active=1 AND role='teacher'")
    total_teachers = c.fetchone()[0] or 0
    
    # Today's alerts
    c.execute("SELECT COUNT(*) FROM alerts WHERE DATE(timestamp)=?", (today,))
    alerts_today = c.fetchone()[0] or 0
    
    # Today's present students
    c.execute("SELECT COUNT(DISTINCT name) FROM attendance WHERE date=? AND name IN (SELECT name FROM people WHERE role='student' AND active=1)", (today,))
    present_students = c.fetchone()[0] or 0
    
    attendance_rate = round((present_students / total_students * 100), 1) if total_students > 0 else 0
    
    conn.close()
    
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
