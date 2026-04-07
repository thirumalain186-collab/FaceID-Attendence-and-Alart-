"""
Simple camera test with face recognition
Run this to test if camera and recognition work
"""
import cv2
import cv2.face as cv2_face
import os

print("="*50)
print("CAMERA TEST")
print("="*50)

# Check if model exists
if not os.path.exists('trainer/trainer.yml'):
    print("NO MODEL - Please register someone first!")
    exit(1)

# Load model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
print("Model loaded!")

# Load label map
import pickle
label_map = {}
if os.path.exists('trainer/label_map.pkl'):
    with open('trainer/label_map.pkl', 'rb') as f:
        label_map = pickle.load(f)
print("People:", list(label_map.values()))

# Open camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    exit(1)

print("\nCamera opened! Press 'Q' to quit")
print("Look at camera - your name should appear!")

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        # Draw box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Get face and recognize
        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200, 200))
        
        label, conf = recognizer.predict(face_resized)
        name = label_map.get(label, "Unknown")
        
        # Draw name
        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        print(f"Recognized: {name} (conf={conf:.1f})")
    
    cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imshow("Test - Q to quit", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Done!")
