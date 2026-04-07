#!/usr/bin/env python3
"""
Retrain model with correct label mapping
Labels MUST match database IDs
"""

import os
import cv2
import pickle
import numpy as np
import sqlite3

print("\n" + "="*70)
print("RETRAINING MODEL WITH CORRECT LABELS")
print("="*70 + "\n")

# Get database mappings FIRST
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM people ORDER BY name")
db_people = cursor.fetchall()

db_map = {}  # name -> id
id_map = {}  # id -> name

for person_id, name in db_people:
    db_map[name.lower()] = person_id
    id_map[person_id] = name

print("Database students:")
for pid, name in sorted(id_map.items()):
    print(f"  Label {pid}: {name}")

conn.close()

# Now train with CORRECT labels matching database IDs
recognizer = cv2.face.LBPHFaceRecognizer_create()

images = []
labels = []  # These MUST be database IDs

dataset_path = "dataset"

print("\n\nLoading images with correct database IDs:")

for folder_name in sorted(os.listdir(dataset_path)):
    folder_path = os.path.join(dataset_path, folder_name)
    
    if not os.path.isdir(folder_path):
        continue
    
    # Extract student name
    parts = folder_name.rsplit('_', 2)
    if len(parts) >= 1:
        student_name = parts[0].lower()
    else:
        continue
    
    if student_name not in db_map:
        print(f"  SKIP: {folder_name} (not in database)")
        continue
    
    db_id = db_map[student_name]
    
    print(f"\n  Processing: {folder_name}")
    print(f"    Student: {student_name} -> Database ID: {db_id}")
    
    image_count = 0
    for image_file in os.listdir(folder_path):
        if image_file.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder_path, image_file)
            
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                images.append(img)
                labels.append(db_id)  # Use database ID as label!
                image_count += 1
    
    print(f"    Loaded: {image_count} images with label {db_id}")

print(f"\n\n  Total images: {len(images)}")
print(f"  Unique labels: {len(set(labels))}")
print(f"  Labels used: {sorted(set(labels))}")

if len(images) > 0:
    print("\n  Training model with database IDs as labels...")
    recognizer.train(images, np.array(labels))
    
    os.makedirs("trainer", exist_ok=True)
    recognizer.save("trainer/trainer.yml")
    
    # Save label map (database IDs to names)
    label_map = {db_id: f"{name} ({db_id})" for db_id, name in id_map.items()}
    
    with open("trainer/label_map.pkl", "wb") as f:
        pickle.dump(label_map, f)
    
    print("  SUCCESS!")
    print(f"    Model saved to: trainer/trainer.yml")
    print(f"    Label map saved to: trainer/label_map.pkl")
    print(f"\n  Label map: {label_map}")
else:
    print("\n  ERROR: No images found!")

print("\n" + "="*70 + "\n")
