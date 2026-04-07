"""
Direct test of recognition and attendance marking
"""
import cv2
import pickle
import numpy as np
from pathlib import Path
import database
from attendance_engine import AttendanceEngine

print("="*60)
print("TESTING RECOGNITION AND ATTENDANCE MARKING")
print("="*60)

# Initialize engine
engine = AttendanceEngine()

print(f"\nLabel map: {engine.label_map}")
print(f"Person ID map: {engine.person_id_map}")

# Check database
people = database.get_active_people()
print(f"\nActive people in DB: {len(people)}")
for p in people:
    print(f"  - {p.get('name')} (Roll: {p.get('roll_number')}, ID: {p.get('id')})")

# Test recognition on training images
dataset_dir = Path('dataset')
test_images = []

for person_folder in sorted(dataset_dir.iterdir()):
    if not person_folder.is_dir():
        continue
    if 'raj' in person_folder.name:
        continue
    
    images = list(person_folder.glob('*.jpg'))[:1]  # Just test first image
    for img_path in images:
        test_images.append((person_folder.name, img_path))

print(f"\nTesting {len(test_images)} images:")

for folder_name, img_path in test_images:
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    img_resized = cv2.resize(img, (200, 200))
    
    try:
        label, confidence = engine.recognizer.predict(img_resized)
        display_name = engine.label_map.get(label, "UNKNOWN")
        
        print(f"\n{folder_name}:")
        print(f"  Image: {img_path.name}")
        print(f"  Prediction: label={label}, confidence={confidence}")
        print(f"  Display name: {display_name}")
        
        # Check if should be marked
        if label >= 0 and confidence <= 200 and not np.isinf(confidence):
            name = display_name.split('(')[0].strip()
            print(f"  Status: SHOULD MARK - {name}")
        else:
            print(f"  Status: SKIP - invalid prediction")
            
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
