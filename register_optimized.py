"""
REGISTER FACE - Optimized for better recognition
Stand closer to camera for larger face capture!
"""
import cv2
import os
import sys

print("="*60)
print("FACE REGISTRATION - OPTIMIZED VERSION")
print("="*60)
print("\nIMPORTANT: Stand 30-50cm from camera for best results")
print("Keep lighting bright and face centered\n")

# Get name
name = input("Enter your name: ").strip()
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

print("Camera ready!")
print("\nInstructions:")
print("1. Position your face in the green box")
print("2. Press SPACE to capture")
print("3. Press 'Q' when done (minimum 15 photos)")
print("4. Photos with large faces work BEST for recognition\n")

count = 0
max_photos = 30
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Detect faces - more sensitive to get larger crops
    faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(80, 80))
    
    # Draw boxes and info
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "GOOD!", (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Status text
    cv2.putText(frame, f"Photos: {count}/{max_photos}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    if len(faces) == 1:
        cv2.putText(frame, "Press SPACE to capture", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    elif len(faces) > 1:
        cv2.putText(frame, "Multiple faces - please alone", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Face not detected - move closer", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow("Registration - SPACE to capture, Q to finish", frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):
        if len(faces) == 1:
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            # Resize to 200x200 (same as training)
            face_resized = cv2.resize(face_roi, (200, 200))
            
            filename = f"{safe_name}_{roll}_{count}.jpg"
            filepath = os.path.join(person_dir, filename)
            cv2.imwrite(filepath, face_resized)
            count += 1
            print(f"Captured photo {count}")
        else:
            print(f"Cannot capture - detected {len(faces)} faces (need exactly 1)")
    
    if key == ord('q') or count >= max_photos:
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n{'='*60}")
print(f"Captured {count} photos!")
print(f"Saved to: {person_dir}")
print(f"{'='*60}\n")

if count >= 10:
    print("Training model...")
    import train
    success = train.train_model()
    if success:
        print("\n✅ REGISTRATION COMPLETE!")
        print(f"Name: {name}")
        print(f"Roll: {roll}")
        print(f"Photos captured: {count}")
        print("\nYou are now registered!")
        print("Run 'python app.py' and use Electron to test attendance")
    else:
        print("\n❌ Training failed - check logs")
else:
    print(f"❌ Need at least 10 photos, got {count}")
    print("Run this script again to complete registration")
