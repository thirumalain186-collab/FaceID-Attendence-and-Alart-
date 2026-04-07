"""
Test LBPH prediction directly on live camera
"""
import cv2
import numpy as np
import pickle
from pathlib import Path

# Load model and label map
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

with open('trainer/label_map.pkl', 'rb') as f:
    label_map = pickle.load(f)

print(f"Label map: {label_map}")

# Load cascade
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Test on all training images
dataset_dir = Path('dataset')
test_count = 0
success_count = 0

for person_folder in sorted(dataset_dir.iterdir()):
    if not person_folder.is_dir():
        continue
    
    images = list(person_folder.glob('*.jpg'))
    print(f"\n{person_folder.name}: {len(images)} images")
    
    for img_path in images[:3]:  # Test first 3 images
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        img_resized = cv2.resize(img, (200, 200))
        
        try:
            label, confidence = recognizer.predict(img_resized)
            expected_label = 0 if 'aizen' in person_folder.name.lower() else 1
            status = "OK" if label == expected_label else "WRONG"
            print(f"  {img_path.name}: label={label} conf={confidence:.2f} [{status}]")
            test_count += 1
            if label == expected_label and confidence < 200:
                success_count += 1
        except Exception as e:
            print(f"  {img_path.name}: ERROR - {e}")

print(f"\nTotal tested: {test_count}, Success: {success_count}")
