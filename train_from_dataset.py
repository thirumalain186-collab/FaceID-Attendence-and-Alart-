#!/usr/bin/env python3
"""
Train model from existing dataset folder
"""

import os
import cv2
import pickle
import numpy as np
from pathlib import Path

print("\n" + "="*70)
print("TRAINING MODEL FROM EXISTING DATASET")
print("="*70 + "\n")

# Initialize LBPH recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Prepare training data
images = []
labels = []
label_dict = {}
next_label = 0

dataset_path = "dataset"

# Go through each folder in dataset
for folder_name in sorted(os.listdir(dataset_path)):
    folder_path = os.path.join(dataset_path, folder_name)
    
    if not os.path.isdir(folder_path):
        continue
    
    # Extract student name from folder name
    # Format: name_roll_student
    parts = folder_name.rsplit('_', 2)
    if len(parts) >= 2:
        student_name = parts[0]
    else:
        student_name = folder_name
    
    print(f"Processing: {folder_name}")
    print(f"  Student: {student_name}")
    
    if student_name not in label_dict:
        label_dict[student_name] = next_label
        next_label += 1
    
    current_label = label_dict[student_name]
    
    # Load all images from folder
    image_count = 0
    for image_file in os.listdir(folder_path):
        if image_file.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder_path, image_file)
            
            # Read image
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                images.append(img)
                labels.append(current_label)
                image_count += 1
    
    print(f"    Loaded: {image_count} images")
    print(f"    Label: {current_label}")

print(f"\n  Total images loaded: {len(images)}")
print(f"  Total labels: {len(set(labels))}")
print(f"  Label mapping: {label_dict}")

if len(images) > 0:
    print("\n  Training model...")
    recognizer.train(images, np.array(labels))
    
    # Save model
    os.makedirs("trainer", exist_ok=True)
    recognizer.save("trainer/trainer.yml")
    
    # Save label map
    with open("trainer/label_map.pkl", "wb") as f:
        pickle.dump(label_dict, f)
    
    print("  Model trained and saved!")
    print(f"\n  Saved to:")
    print(f"    - trainer/trainer.yml")
    print(f"    - trainer/label_map.pkl")
else:
    print("\nERROR: No images found!")

print("\n" + "="*70 + "\n")
