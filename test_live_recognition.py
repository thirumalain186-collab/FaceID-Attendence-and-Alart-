"""
Test: Capture live face and check recognition
"""
import cv2
import pickle
import time

print("Loading model...")
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Load label map
with open('trainer/label_map.pkl', 'rb') as f:
    label_map = pickle.load(f)
print(f"Label map: {label_map}")

print("\nOpening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("Waiting for face detection...")
start = time.time()

captured_frame = None
while time.time() - start < 20:  # Try for 20 seconds
    ret, frame = cap.read()
    if not ret:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 50))
    
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        captured_frame = (gray, x, y, w, h)
        print(f"Face captured at ({x},{y}) size {w}x{h}")
        break

cap.release()

if captured_frame:
    gray, x, y, w, h = captured_frame
    face_roi = gray[y:y+h, x:x+w]
    face_resized = cv2.resize(face_roi, (200, 200))
    
    print(f"\nTesting recognition on live camera face...")
    print(f"Face region: {face_roi.shape}, Resized: {face_resized.shape}")
    
    label, confidence = recognizer.predict(face_resized)
    print(f"Result: label={label}, confidence={confidence}")
    
    if label >= 0:
        name = label_map.get(label, "Unknown")
        print(f"RECOGNIZED: {name} (confidence: {confidence:.2f}, quality: {max(0, 100-confidence):.1f}%)")
    else:
        print(f"NOT RECOGNIZED (label=-1, confidence too high: {confidence})")
else:
    print("ERROR: Could not detect face in 20 seconds")
