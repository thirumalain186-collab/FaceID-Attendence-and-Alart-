#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attendance System Diagnostics
Diagnose why attendance is not being marked
"""

import sqlite3
import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("ATTENDANCE SYSTEM DIAGNOSTICS")
print("="*70 + "\n")

try:
    # Connect to database
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Check tables
    print("1. CHECKING DATABASE TABLES:")
    print("-" * 70)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    if tables:
        for table in tables:
            print(f"  [OK] {table[0]}")
    else:
        print("  [ERROR] No tables found!")
    
    # Check attendance table schema
    print("\n2. ATTENDANCE TABLE SCHEMA:")
    print("-" * 70)
    cursor.execute("PRAGMA table_info(attendance)")
    schema = cursor.fetchall()
    if schema:
        for col in schema:
            print(f"  {col[1]:25} {col[2]}")
    
    # Check people table
    print("\n3. REGISTERED STUDENTS:")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) FROM people")
    count = cursor.fetchone()[0]
    print(f"  Total students: {count}")
    
    cursor.execute("SELECT id, name FROM people ORDER BY id")
    people = cursor.fetchall()
    if people:
        for person in people:
            print(f"    ID: {person[0]:2} | Name: {person[1]}")
    else:
        print("  ✗ No students registered!")
    
    # Check attendance records
    print("\n4. ATTENDANCE RECORDS:")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) FROM attendance")
    total = cursor.fetchone()[0]
    print(f"  Total records: {total}")
    
    cursor.execute("SELECT person_id, timestamp FROM attendance ORDER BY timestamp DESC LIMIT 5")
    records = cursor.fetchall()
    if records:
        print("  Last 5 records:")
        for rec in records:
            print(f"    Person {rec[0]} | {rec[1]}")
    else:
        print("  ✗ No attendance records found!")
    
    # Check today's attendance
    print("\n5. TODAY'S ATTENDANCE:")
    print("-" * 70)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute(
        "SELECT person_id, COUNT(*) FROM attendance WHERE timestamp LIKE ? GROUP BY person_id",
        (f"{today}%",)
    )
    today_records = cursor.fetchall()
    if today_records:
        print(f"  Date: {today}")
        for rec in today_records:
            print(f"    Person {rec[0]} | Count: {rec[1]}")
    else:
        print(f"  ✗ No attendance marked today ({today})")
    
    # Check if trainer/model exists
    print("\n6. FACE RECOGNITION MODEL:")
    print("-" * 70)
    model_path = Path("trainer/trainer.yml")
    if model_path.exists():
        size = model_path.stat().st_size / (1024*1024)
        print(f"  ✓ Model exists: trainer.yml ({size:.1f} MB)")
    else:
        print(f"  ✗ Model NOT found: trainer/trainer.yml")
    
    label_path = Path("trainer/label_map.pkl")
    if label_path.exists():
        print(f"  ✓ Label map exists")
    else:
        print(f"  ✗ Label map NOT found")
    
    # Summary
    print("\n7. DIAGNOSIS SUMMARY:")
    print("-" * 70)
    
    issues = []
    
    if count == 0:
        issues.append("✗ No students registered - need to register faces first")
    else:
        print(f"  ✓ {count} students registered")
    
    if not model_path.exists():
        issues.append("✗ Face recognition model not trained")
    else:
        print(f"  ✓ Face recognition model exists")
    
    if total == 0 and count > 0:
        issues.append("⚠ System running but attendance not being marked")
    elif total > 0:
        print(f"  ✓ Attendance records being marked ({total} total)")
    
    if issues:
        print("\n  ISSUES FOUND:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("\n  ✓ ALL SYSTEMS OPERATIONAL")
    
    print("\n" + "="*70)
    
    conn.close()
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
