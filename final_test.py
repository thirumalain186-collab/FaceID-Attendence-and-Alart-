"""
Final comprehensive system test before Science Expo
Tests all critical components
"""
import os
import sys
import pickle
from pathlib import Path
import cv2

print("="*70)
print("FINAL SYSTEM VERIFICATION FOR SCIENCE EXPO")
print("="*70)

passed = 0
failed = 0

def test(name, condition, error_msg=""):
    global passed, failed
    if condition:
        print(f"[PASS] {name}")
        passed += 1
    else:
        print(f"[FAIL] {name}")
        if error_msg:
            print(f"       {error_msg}")
        failed += 1

# Test 1: OpenCV installation
print("\n=== OPENCV VERIFICATION ===")
try:
    import cv2
    import cv2.face
    test("OpenCV installed", True)
    test("OpenCV version", cv2.__version__.startswith("4.8"))
    test("Face module available", hasattr(cv2, 'face'))
except Exception as e:
    test("OpenCV installed", False, str(e))

# Test 2: Required files exist
print("\n=== FILE STRUCTURE ===")
required_files = [
    "app.py",
    "attendance_engine.py",
    "train.py",
    "database.py",
    "config.py",
    "trainer/trainer.yml",
    "trainer/label_map.pkl",
    "dataset/aizen_01_student"
]

for file in required_files:
    path = Path(file)
    test(f"File: {file}", path.exists())

# Test 3: Model loading
print("\n=== MODEL VERIFICATION ===")
try:
    with open("trainer/label_map.pkl", 'rb') as f:
        label_map = pickle.load(f)
    test("Label map loads", True)
    test("Aizen registered", 0 in label_map and "Aizen" in label_map[0])
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer/trainer.yml")
    test("Model loads", True)
except Exception as e:
    test("Model loading", False, str(e))

# Test 4: Training data quality
print("\n=== TRAINING DATA ===")
dataset_dir = Path("dataset/aizen_01_student")
if dataset_dir.exists():
    images = list(dataset_dir.glob("*.jpg"))
    test("Training images exist", len(images) > 10, f"Found {len(images)} images")
    
    if len(images) > 0:
        img = cv2.imread(str(images[0]))
        test("Image format", img is not None)
        test("Image size is 200x200", img.shape[:2] == (200, 200), f"Size: {img.shape}")
else:
    test("Dataset folder exists", False)

# Test 5: Face detection capability
print("\n=== CAMERA & FACE DETECTION ===")
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
test("Cascade file exists", Path(cascade_path).exists())

try:
    cascade = cv2.CascadeClassifier(cascade_path)
    test("Cascade loads", not cascade.empty())
except:
    test("Cascade loads", False)

# Test 6: Database
print("\n=== DATABASE ===")
try:
    import database
    people = database.get_active_people()
    test("Database connects", True)
    test("People registered", len(people) > 0, f"Found {len(people)} people")
    if len(people) > 0:
        test("Aizen in database", any(p.get('name') == 'Aizen' for p in people))
except Exception as e:
    test("Database access", False, str(e))

# Test 7: Recognition on training image
print("\n=== RECOGNITION TEST ===")
try:
    test_img_path = Path("dataset/aizen_01_student/aizen_01_0.jpg")
    if test_img_path.exists():
        test_img = cv2.imread(str(test_img_path), cv2.IMREAD_GRAYSCALE)
        
        # Detect face
        faces = cascade.detectMultiScale(test_img, 1.05, 3, minSize=(30, 30))
        test("Face detection in training image", len(faces) > 0)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_roi = test_img[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (200, 200))
            
            label, confidence = recognizer.predict(face_resized)
            test("Model prediction works", label >= 0)
            test("Good confidence on training image", confidence < 100, f"Confidence: {confidence:.2f}")
except Exception as e:
    test("Recognition test", False, str(e))

# Summary
print("\n" + "="*70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*70)

if failed == 0:
    print("\n[SUCCESS] SYSTEM IS READY FOR SCIENCE EXPO!")
    print("\nNext steps:")
    print("1. python app.py                    (Start Flask backend)")
    print("2. cd electron && npm start         (Open Electron UI)")
    print("3. Click 'Start Attendance'         (Begin recognition)")
    sys.exit(0)
else:
    print(f"\n[ERROR] SYSTEM HAS {failed} ISSUES - Fix before expo!")
    sys.exit(1)
