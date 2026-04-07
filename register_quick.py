"""
Quick Registration Helper - Simplified version
Perfect for Science Expo demonstrations
"""
import os
import sys
import cv2

def register_student():
    print("\n" + "="*60)
    print("REGISTER NEW STUDENT")
    print("="*60 + "\n")
    
    # Get info
    name = input("Student Name: ").strip()
    if not name:
        print("Error: Name required!")
        return False
    
    roll = input("Roll Number: ").strip()
    if not roll:
        print("Error: Roll number required!")
        return False
    
    print(f"\nRegistering: {name} ({roll})")
    print("Stand 30-50cm from camera")
    print("Press SPACE to capture, Q to finish\n")
    
    # Setup
    safe_name = name.replace(" ", "_").lower()
    dataset_dir = f"dataset/{safe_name}_{roll}_student"
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Camera not available!")
        return False
    
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(80, 80))
        
        # Display info
        cv2.putText(frame, f"Photos: {count}/20", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, name, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        if len(faces) == 0:
            cv2.putText(frame, "No face detected - move closer", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        elif len(faces) > 1:
            cv2.putText(frame, "Multiple faces - please be alone", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Press SPACE to capture", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.imshow("Registration", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' ') and len(faces) == 1:
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (200, 200))
            
            filename = f"{safe_name}_{roll}_{count}.jpg"
            filepath = os.path.join(dataset_dir, filename)
            cv2.imwrite(filepath, face_resized)
            count += 1
            print(f"Captured: {count}/20")
        
        if key == ord('q') or count >= 20:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n✓ Captured {count} photos")
    
    if count >= 10:
        print("Training model...")
        import train
        if train.train_model():
            print(f"✓ {name} is now registered!")
            return True
        else:
            print("✗ Training failed")
            return False
    else:
        print(f"✗ Need at least 10 photos (got {count})")
        return False

if __name__ == "__main__":
    success = register_student()
    sys.exit(0 if success else 1)
