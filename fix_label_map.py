#!/usr/bin/env python3
"""
Fix label map to match database IDs
"""

import pickle
import sqlite3
import cv2
import numpy as np
import os

print("\n" + "="*70)
print("FIXING LABEL MAP TO MATCH DATABASE IDs")
print("="*70 + "\n")

# Get database mappings
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM people ORDER BY name")
db_people = cursor.fetchall()

print("Database students:")
db_map = {}
for person_id, name in db_people:
    print(f"  ID: {person_id:2} | Name: {name}")
    db_map[name.lower()] = person_id

conn.close()

# Load current label map from model training
old_label_map = {'aizen': 0, 'arjun': 1, 'neha': 2, 'priya': 3, 'raj': 4, 'thiru': 5, 'vikram': 6}

print("\n\nCreating new label map:")
new_label_map = {}

for name_lower, old_label in old_label_map.items():
    if name_lower in db_map:
        db_id = db_map[name_lower]
        new_label_map[db_id] = f"{name_lower.capitalize()} ({db_id})"
        print(f"  {old_label} -> {db_id}: {name_lower.capitalize()}")

# Save new label map
with open("trainer/label_map.pkl", "wb") as f:
    pickle.dump(new_label_map, f)

print("\n  Label map updated!")
print(f"  New mapping: {new_label_map}")

print("\n" + "="*70 + "\n")
