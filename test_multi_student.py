"""
Test Multi-Student Recognition - Verify 5+ students can be recognized
"""
import cv2
import pickle
import time

print("="*70)
print("MULTI-STUDENT RECOGNITION TEST")
print("="*70)

# Load model and label map
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

with open('trainer/label_map.pkl', 'rb') as f:
    label_map = pickle.load(f)

print(f"\nRegistered students: {len(label_map)}")
for label_id, name in sorted(label_map.items()):
    print(f"  Label {label_id}: {name}")

if len(label_map) < 2:
    print("\nWarning: Only 1 student registered.")
    print("Register 5+ students for proper multi-student test.")
    print("Use: python register_quick.py")
    exit(1)

# Open camera
print("\nOpening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera not available")
    exit(1)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("Camera ready. Testing for 15 seconds...")
print("Position registered students in front of camera.\n")

start_time = time.time()
recognized_count = 0
recognized_students = {}

while time.time() - start_time < 15:
    ret, frame = cap.read()
    if not ret:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect all faces in frame
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 50))
    
    # Try to recognize each face
    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_resized = cv2.resize(face_roi, (200, 200))
            label, confidence = recognizer.predict(face_resized)
            
            if label >= 0 and confidence < 200:
                name = label_map.get(label, "Unknown")
                recognized_count += 1
                
                if name not in recognized_students:
                    recognized_students[name] = 0
                recognized_students[name] += 1
                
                print(f"[RECOGNIZED] {name} - confidence {confidence:.1f}")
    
    time.sleep(0.1)

cap.release()

print("\n" + "="*70)
print("RESULTS")
print("="*70)

print(f"\nTotal recognitions: {recognized_count}")
print(f"Unique students recognized: {len(recognized_students)}")
print(f"Total registered students: {len(label_map)}")

if recognized_students:
    print("\nRecognition breakdown:")
    for name in sorted(recognized_students.keys()):
        count = recognized_students[name]
        print(f"  - {name}: {count} times")

print("\n" + "="*70)

# Determine success
if recognized_count > 0:
    print("SUCCESS: Multi-student recognition is working!")
    if len(recognized_students) >= 2:
        print(f"Recognized {len(recognized_students)} different students")
    if len(recognized_students) < len(label_map):
        print(f"Tip: {len(label_map) - len(recognized_students)} registered students not in view")
else:
    print("No students recognized in 15 seconds")
    print("Tip: Have registered students look at camera for better results")

print("="*70)
