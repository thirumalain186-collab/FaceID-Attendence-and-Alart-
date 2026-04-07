"""
Optimized camera test - Fast & Error-free
"""
import cv2
import cv2.face as cv2_face
import pickle
import os

print("Starting...")

# Load model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Load label map
label_map = {}
if os.path.exists('trainer/label_map.pkl'):
    with open('trainer/label_map.pkl', 'rb') as f:
        label_map = pickle.load(f)
print("People:", [v.split('(')[0].strip() for v in label_map.values()])

# Open camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
print("Camera ready")

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces with better settings
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 50))
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_resized = cv2.resize(face_roi, (200, 200))
            
            label, confidence = recognizer.predict(face_resized)
            
            # Skip invalid predictions
            if label < 0 or confidence > 150:
                cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                continue
            
            name_raw = label_map.get(label, "Unknown")
            name = name_raw.split('(')[0].strip() if '(' in name_raw else name_raw
            
            cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.putText(frame, f"Q to quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.imshow("Camera", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Done!")
