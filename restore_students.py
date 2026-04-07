#!/usr/bin/env python3
"""
Quick Fix: Re-add 7 students and retrain model
"""

import sqlite3
import os
import shutil

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

print("\n" + "="*70)
print("RE-ADDING 7 STUDENTS TO DATABASE")
print("="*70 + "\n")

# First, clear the current people table
cursor.execute("DELETE FROM people")
conn.commit()

# Add 7 students back
students = [
    ("Aizen", "01"),
    ("Thiru", "02"),
    ("Raj", "03"),
    ("Priya", "04"),
    ("Vikram", "05"),
    ("Neha", "06"),
    ("Arjun", "07")
]

for name, roll in students:
    cursor.execute("INSERT INTO people (name, role, roll_number) VALUES (?, ?, ?)", (name, 'student', roll))
    conn.commit()
    student_id = cursor.lastrowid
    print(f"Added: {name:15} (ID: {student_id:2}, Roll: {roll})")

print("\n" + "="*70)
print("STUDENT DATABASE RESTORED")
print("="*70 + "\n")

conn.close()

print("Now you need to:")
print("1. Register each student with their face images")
print("2. System will automatically train the model")
print("\nOr use existing face dataset if available:")

# Check if dataset folder exists
dataset_path = "dataset"
if os.path.exists(dataset_path):
    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    print(f"  Found {len(folders)} folders in dataset/")
    for folder in folders[:7]:
        print(f"    - {folder}")
