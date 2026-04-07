"""
Add Demo Students to Database and Register them
"""
import sqlite3
import os
from pathlib import Path

def add_student_to_db(name, roll_number):
    """Add student to database"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO people (name, role, roll_number, registered_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (name, 'student', roll_number))
        conn.commit()
        person_id = cursor.lastrowid
        print(f"  Added to DB: {name} ({roll_number}) - ID: {person_id}")
        conn.close()
        return person_id
    except Exception as e:
        print(f"  Error: {e}")
        conn.close()
        return None

def main():
    print("\n" + "="*60)
    print("ADD DEMO STUDENTS TO DATABASE")
    print("="*60 + "\n")
    
    students = [
        ("Raj", "03"),
        ("Priya", "04"),
        ("Vikram", "05"),
        ("Neha", "06"),
        ("Arjun", "07"),
    ]
    
    print("Adding students to database...\n")
    
    for name, roll in students:
        # Check if already exists
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM people WHERE roll_number = ?', (roll,))
        existing = cursor.fetchone()
        conn.close()
        
        if existing:
            print(f"  {name} ({roll}) already exists")
        else:
            add_student_to_db(name, roll)
    
    print("\n" + "="*60)
    print("Training model with all registered students...")
    print("="*60 + "\n")
    
    import train
    if train.train_model():
        print("\n[OK] Training complete!")
        
        # Show summary
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, roll_number FROM people ORDER BY id')
        people = cursor.fetchall()
        conn.close()
        
        print(f"\nTotal registered students: {len(people)}")
        for pid, name, roll in people:
            print(f"  {pid}: {name} ({roll})")
        
        return True
    else:
        print("[ERROR] Training failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
