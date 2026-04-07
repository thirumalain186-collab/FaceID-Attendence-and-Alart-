"""
Camera test with recognition
"""
import cv2
import cv2.face as cv2_face
import numpy as np

# Load recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Label mapping (must match training order)
label_names = {0: 'Manoj', 1: 'Manojkumar', 2: 'Thiru'}

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    exit(1)

print("Camera opened! Press 'Q' to quit")
print("Registered people:", list(label_names.values()))

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(20, 20))
    
    for (x, y, w, h) in faces:
        # Draw box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Get face ROI
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_resized = cv2.resize(face_roi, (200, 200))
            
            # Predict
            label, confidence = recognizer.predict(face_resized)
            
            # Get name
            name = label_names.get(label, 'Unknown')
            
            # Draw name
            cv2.putText(frame, name, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Print to terminal
            print(f"Detected: {name} (Label={label}, Conf={confidence:.1f})")
    
    cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imshow("Recognition Test - Q to quit", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Done!")
