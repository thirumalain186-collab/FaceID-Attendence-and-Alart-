"""
Database Optimization Module for Smart Attendance System v2
Provides database maintenance and optimization functions
"""

import sqlite3
from pathlib import Path
import config
from logger import get_logger

logger = get_logger()


def get_connection():
    """Get database connection"""
    return sqlite3.connect(str(config.DB_PATH))


def add_indexes():
    """Add performance indexes to database tables"""
    conn = get_connection()
    c = conn.cursor()
    
    indexes = [
        ("idx_attendance_date", "attendance", "date"),
        ("idx_attendance_name", "attendance", "name"),
        ("idx_attendance_person_id", "attendance", "person_id"),
        ("idx_movement_timestamp", "movement_log", "timestamp"),
        ("idx_alerts_timestamp", "alerts", "timestamp"),
        ("idx_people_active", "people", "active"),
        ("idx_people_roll", "people", "roll_number"),
        ("idx_batches_status", "batches", "status"),
    ]
    
    for index_name, table, column in indexes:
        try:
            c.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
            logger.info(f"Created index: {index_name}")
        except sqlite3.Error as e:
            logger.warning(f"Index {index_name} failed: {e}")
    
    conn.commit()
    conn.close()
    logger.info("Database indexes added/verified")


def analyze_database():
    """Analyze database for query optimization"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("ANALYZE")
    conn.commit()
    conn.close()
    logger.info("Database analyzed")


def vacuum_database():
    """Vacuum database to reclaim space"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute("VACUUM")
        conn.commit()
        logger.info("Database vacuumed successfully")
    except sqlite3.Error as e:
        logger.error(f"Vacuum failed: {e}")
    finally:
        conn.close()


def get_database_stats():
    """Get database statistics"""
    conn = get_connection()
    c = conn.cursor()
    
    stats = {}
    
    tables = ['batches', 'people', 'attendance', 'movement_log', 'alerts', 'settings']
    for table in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = c.fetchone()[0]
        except sqlite3.Error:
            stats[table] = 0
    
    c.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    result = c.fetchone()
    stats['size_bytes'] = result[0] if result else 0
    stats['size_mb'] = round(stats['size_bytes'] / (1024 * 1024), 2)
    
    conn.close()
    return stats


def cleanup_old_data(days: int = 90):
    """Clean up old data from database"""
    from datetime import datetime, timedelta
    
    conn = get_connection()
    c = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    deleted = 0
    try:
        c.execute("DELETE FROM movement_log WHERE DATE(timestamp) < ?", (cutoff_date,))
        deleted += c.rowcount
        
        c.execute("DELETE FROM alerts WHERE DATE(timestamp) < ?", (cutoff_date,))
        deleted += c.rowcount
        
        conn.commit()
        logger.info(f"Cleaned up {deleted} old records (older than {days} days)")
    except sqlite3.Error as e:
        logger.error(f"Cleanup failed: {e}")
    finally:
        conn.close()
    
    return deleted


def repair_database():
    """Attempt to repair corrupted database"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute("REINDEX")
        c.execute("PRAGMA integrity_check")
        result = c.fetchone()
        
        if result[0] == 'ok':
            logger.info("Database integrity check passed")
        else:
            logger.warning(f"Database integrity issues: {result}")
        
        conn.close()
        return result[0] == 'ok'
    except sqlite3.Error as e:
        logger.error(f"Repair check failed: {e}")
        conn.close()
        return False


def optimize_all():
    """Run all database optimizations"""
    logger.info("Starting database optimization...")
    
    add_indexes()
    analyze_database()
    vacuum_database()
    
    stats = get_database_stats()
    logger.info(f"Database stats: {stats}")
    
    logger.info("Database optimization complete")
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "optimize":
            optimize_all()
        elif command == "stats":
            print(get_database_stats())
        elif command == "vacuum":
            vacuum_database()
        elif command == "repair":
            repair_database()
        elif command == "cleanup" and len(sys.argv) > 2:
            cleanup_old_data(int(sys.argv[2]))
        elif command == "indexes":
            add_indexes()
        else:
            print("Commands: optimize, stats, vacuum, repair, cleanup <days>, indexes")
    else:
        optimize_all()
