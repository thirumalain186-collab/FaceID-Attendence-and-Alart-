"""
Diagnostic script to test recognition on training images
"""
import cv2
import numpy as np
import pickle
from pathlib import Path
import config

# Image size (MUST match training)
IMG_SIZE = (200, 200)

# Load label map
label_map_path = config.TRAINER_DIR / "label_map.pkl"
with open(label_map_path, 'rb') as f:
    label_map = pickle.load(f)
print(f"Label map: {label_map}")

# Load model
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
import cv2.face as cv2_face
recognizer = cv2_face.LBPHFaceRecognizer_create()
recognizer.read(str(config.TRAINER_FILE))
print(f"Model loaded from: {config.TRAINER_FILE}")

# Test on first training image
test_image_path = Path("dataset/aizen_01_student/aizen_01_0.jpg")
if test_image_path.exists():
    print(f"\nTesting image: {test_image_path}")
    
    img = cv2.imread(str(test_image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect face
    faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
    print(f"Faces detected: {len(faces)}")
    
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        print(f"Face location: x={x}, y={y}, w={w}, h={h}")
        
        # Extract and resize
        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, IMG_SIZE)
        print(f"Face resized to: {face_resized.shape}")
        
        # Recognize
        label, confidence = recognizer.predict(face_resized)
        print(f"Recognition: label={label}, confidence={confidence}")
        
        if label in label_map:
            display_name = label_map[label]
            print(f"Display name: {display_name}")
            print(f"Recognition quality: {max(0, 100-confidence):.1f}%")
        else:
            print(f"Label {label} not in label_map!")
    else:
        print("ERROR: No face detected in training image!")
else:
    print(f"Test image not found: {test_image_path}")

print("\n--- Testing on another training image ---")
test_image_path2 = Path("dataset/aizen_01_student/aizen_01_10.jpg")
if test_image_path2.exists():
    print(f"Testing image: {test_image_path2}")
    
    img = cv2.imread(str(test_image_path2))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
    print(f"Faces detected: {len(faces)}")
    
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, IMG_SIZE)
        label, confidence = recognizer.predict(face_resized)
        print(f"Recognition: label={label}, confidence={confidence}, quality={max(0, 100-confidence):.1f}%")
