"""
Register face using OpenCV camera - SAME camera as recognition
"""
import cv2
import os
import sys

print("="*50)
print("FACE REGISTRATION")
print("="*50)

# Get name
name = input("\nEnter your name: ").strip()
if not name:
    print("Name required!")
    sys.exit()

roll = input("Enter roll number: ").strip() or "1"
role = "student"

safe_name = name.replace(" ", "_").lower()
person_dir = f"dataset/{safe_name}_{roll}_{role}"
os.makedirs(person_dir, exist_ok=True)

# Open camera
print("\nOpening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    sys.exit()

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("Camera opened!")
print("\nLook at camera and press SPACE to capture photo")
print("Press 'Q' to finish (minimum 15 photos recommended)")
print()

count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 3, minSize=(50, 50))
    
    # Draw box around detected face
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"{count} photos", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    if len(faces) == 1:
        x, y, w, h = faces[0]
        cv2.putText(frame, "Press SPACE to capture!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.putText(frame, f"Photos: {count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Registration - SPACE to capture, Q to quit", frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):
        if len(faces) == 1:
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (200, 200))
            
            filename = f"{safe_name}_{roll}_{count}.jpg"
            filepath = os.path.join(person_dir, filename)
            cv2.imwrite(filepath, face_resized)
            count += 1
            print(f"Captured: {count}")
    
    if key == ord('q') or count >= 30:
        break

cap.release()
cv2.destroyAllWindows()

print(f"\nCaptured {count} photos!")
print(f"Saved to: {person_dir}")

if count >= 10:
    print("\nNow training model...")
    import train
    success = train.train_model()
    if success:
        print("\n✅ REGISTRATION COMPLETE!")
        print(f"You are registered as: {name}")
        print("\nNow run 'python app.py' and use Electron to test attendance!")
    else:
        print("\n❌ Training failed!")
else:
    print(f"\n❌ Need at least 10 photos, got {count}")
