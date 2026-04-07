"""
Headless camera test - tests recognition without GUI
"""
import cv2
import pickle
import time
import sys

print("Loading model...")
try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainer/trainer.yml')
    print("Model loaded")
except Exception as e:
    print(f"Failed to load model: {e}")
    sys.exit(1)

# Load label map
label_map = {}
try:
    with open('trainer/label_map.pkl', 'rb') as f:
        label_map = pickle.load(f)
    print(f"Label map: {label_map}")
except Exception as e:
    print(f"Failed to load label map: {e}")
    sys.exit(1)

# Open camera
print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open camera")
    sys.exit(1)

print("Camera opened. Running test for 10 seconds...")

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognized_count = 0
unknown_count = 0
start_time = time.time()

while time.time() - start_time < 10:
    ret, frame = cap.read()
    if not ret:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 50))
    
    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_resized = cv2.resize(face_roi, (200, 200))
            label, confidence = recognizer.predict(face_resized)
            
            if label >= 0 and confidence < 150:
                name = label_map.get(label, "Unknown")
                print(f"[RECOGNIZED] {name} (confidence: {confidence:.1f})")
                recognized_count += 1
            else:
                print(f"[UNKNOWN] label={label}, confidence={confidence:.1f}")
                unknown_count += 1
    
    time.sleep(0.1)

cap.release()

print(f"\n=== RESULTS ===")
print(f"Recognized: {recognized_count}")
print(f"Unknown: {unknown_count}")
if recognized_count > 0:
    print("SUCCESS: Recognition is working!")
else:
    print("PROBLEM: No faces were recognized")
