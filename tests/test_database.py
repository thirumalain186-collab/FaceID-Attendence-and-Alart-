"""
Unit Tests for Smart Attendance System v2
"""

import pytest
import sqlite3
import os
import sys
from pathlib import Path
from datetime import date, datetime
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import database


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    test_db_path = Path(tempfile.gettempdir()) / "test_attendance.db"
    
    if test_db_path.exists():
        test_db_path.unlink()
    
    conn = sqlite3.connect(str(test_db_path))
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
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            roll_number TEXT,
            email TEXT,
            class_name TEXT,
            batch_id INTEGER,
            active INTEGER DEFAULT 1,
            registered_at TEXT
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT,
            roll_number TEXT,
            date TEXT,
            time_in TEXT,
            status TEXT DEFAULT 'present',
            batch_id INTEGER
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS movement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT,
            role TEXT,
            timestamp TEXT,
            event_type TEXT,
            batch_id INTEGER
        )
    """)
    
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
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    original_db_path = config.DB_PATH
    config.DB_PATH = test_db_path
    
    yield test_db_path
    
    config.DB_PATH = original_db_path
    if test_db_path.exists():
        test_db_path.unlink()


class TestDatabaseFunctions:
    """Test database operations"""
    
    def test_init_database(self, test_db):
        """Test database initialization"""
        database.init_database()
        conn = sqlite3.connect(str(test_db))
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        
        assert 'batches' in tables
        assert 'people' in tables
        assert 'attendance' in tables
        assert 'settings' in tables
    
    def test_add_person(self, test_db):
        """Test adding a person"""
        person_id = database.add_person("Test User", "student", "TEST001")
        
        assert person_id is not None
        assert person_id > 0
        
        conn = sqlite3.connect(str(test_db))
        c = conn.cursor()
        c.execute("SELECT name, role, roll_number FROM people WHERE id=?", (person_id,))
        result = c.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "Test User"
        assert result[1] == "student"
        assert result[2] == "TEST001"
    
    def test_get_active_people(self, test_db):
        """Test retrieving active people"""
        database.add_person("User 1", "student", "ROLL001")
        database.add_person("User 2", "teacher", "TEACH001")
        
        people = database.get_active_people()
        
        assert len(people) >= 2
        names = [p[1] for p in people]
        assert "User 1" in names
        assert "User 2" in names
    
    def test_mark_attendance_success(self, test_db):
        """Test marking attendance successfully"""
        database.add_person("Test Student", "student", "STU001")
        
        result = database.mark_attendance("Test Student", "STU001")
        
        assert result is True
        
        attendance = database.get_today_attendance()
        assert len(attendance) >= 1
        names = [a[2] for a in attendance]
        assert "Test Student" in names
    
    def test_mark_attendance_duplicate(self, test_db):
        """Test duplicate attendance prevention"""
        database.add_person("Test Student", "student", "STU001")
        
        result1 = database.mark_attendance("Test Student", "STU001")
        result2 = database.mark_attendance("Test Student", "STU001")
        
        assert result1 is True
        assert result2 is False
    
    def test_remove_person(self, test_db):
        """Test removing a person"""
        person_id = database.add_person("To Remove", "student", "REM001")
        
        database.remove_person("To Remove")
        
        people = database.get_active_people()
        names = [p[1] for p in people]
        assert "To Remove" not in names
    
    def test_attendance_summary(self, test_db):
        """Test attendance summary"""
        database.add_person("Summary Test 1", "student", "SUM001")
        database.add_person("Summary Test 2", "student", "SUM002")
        
        database.mark_attendance("Summary Test 1", "SUM001")
        database.mark_attendance("Summary Test 2", "SUM002")
        
        today = date.today().isoformat()
        summary = database.get_attendance_by_date_range(today, today)
        
        assert len(summary) >= 2
    
    def test_log_movement(self, test_db):
        """Test movement logging"""
        database.add_person("Movement Test", "student", "MOV001")
        
        database.log_movement("Movement Test", "student", "entry")
        
        movement = database.get_today_movement()
        assert len(movement) >= 1
    
    def test_save_alert(self, test_db):
        """Test saving alerts"""
        alert_id, alert_db_id = database.save_alert("/test/image.jpg", "/test/report.pdf", "Test Location")
        
        assert alert_id is not None
        assert alert_db_id is not None
        
        alerts = database.get_recent_alerts(1)
        assert len(alerts) >= 1
    
    def test_settings(self, test_db):
        """Test settings get/set"""
        database.set_setting("test_key", "test_value")
        value = database.get_setting("test_key")
        
        assert value == "test_value"
    
    def test_stats(self, test_db):
        """Test statistics function"""
        database.add_person("Stats Test", "student", "STAT001")
        database.mark_attendance("Stats Test", "STAT001")
        
        stats = database.get_stats()
        
        assert 'present_today' in stats
        assert 'total_people' in stats
        assert 'total_students' in stats
        assert stats['total_students'] >= 1


class TestBatchFunctions:
    """Test batch operations"""
    
    def test_create_batch(self, test_db):
        """Test batch creation"""
        batch_id = database.create_batch()
        
        assert batch_id is not None
        assert batch_id > 0
        
        batch = database.get_active_batch()
        assert batch is not None
        assert batch[4] == 'active'
    
    def test_batch_progress(self, test_db):
        """Test batch progress"""
        database.create_batch()
        
        progress = database.get_batch_progress()
        
        assert progress is not None
        assert 'days_remaining' in progress
        assert 'days_total' in progress
        assert progress['days_total'] == 30
    
    def test_close_batch(self, test_db):
        """Test batch closing"""
        batch_id = database.create_batch()
        
        database.close_batch(batch_id)
        
        batch = database.get_active_batch()
        assert batch is None


class TestConfig:
    """Test configuration"""
    
    def test_config_loading(self):
        """Test config loads correctly"""
        assert config.DATASET_DIR is not None
        assert config.TRAINER_DIR is not None
        assert config.DB_PATH is not None
    
    def test_email_config_structure(self):
        """Test email config structure"""
        assert 'smtp_server' in config.EMAIL_CONFIG
        assert 'smtp_port' in config.EMAIL_CONFIG
        assert 'sender_email' in config.EMAIL_CONFIG
    
    def test_attendance_config_structure(self):
        """Test attendance config structure"""
        assert 'confidence_threshold' in config.ATTENDANCE_CONFIG
        assert 'camera_index' in config.ATTENDANCE_CONFIG
        assert 'samples_per_person' in config.ATTENDANCE_CONFIG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
