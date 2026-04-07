"""
Register Thiru (Roll 2) - Non-interactive script
"""
import os
import sys
import cv2
import time

def register_thiru():
    name = "Thiru"
    roll = "2"
    
    print("\n" + "="*60)
    print(f"REGISTERING: {name} (Roll {roll})")
    print("="*60 + "\n")
    
    print("Stand 30-50cm from camera")
    print("You have 30 seconds to capture 20 photos")
    print("System will auto-capture when face is detected\n")
    
    # Setup
    safe_name = name.replace(" ", "_").lower()
    dataset_dir = f"dataset/{safe_name}_{roll}_student"
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Clear old images if any
    for f in os.listdir(dataset_dir):
        os.remove(os.path.join(dataset_dir, f))
    
    # Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Camera not available!")
        return False
    
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    count = 0
    start_time = time.time()
    last_capture = 0
    
    while count < 20:
        elapsed = time.time() - start_time
        if elapsed > 30:
            print("Time's up!")
            break
        
        ret, frame = cap.read()
        if not ret:
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(80, 80))
        
        # Display info
        cv2.putText(frame, f"Photos: {count}/20 | Time: {int(30-elapsed)}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, name, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        if len(faces) == 1:
            current_time = time.time()
            if current_time - last_capture > 0.5:  # Auto-capture every 0.5s
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_roi, (200, 200))
                
                filename = f"{safe_name}_{roll}_{count}.jpg"
                filepath = os.path.join(dataset_dir, filename)
                cv2.imwrite(filepath, face_resized)
                count += 1
                last_capture = current_time
                print(f"Captured: {count}/20")
                
                # Show capture feedback
                cv2.putText(frame, "CAPTURED!", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        elif len(faces) > 1:
            cv2.putText(frame, "Multiple faces - be alone", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "No face - move closer", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        cv2.imshow("Registration", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n[OK] Captured {count} photos")
    
    if count >= 10:
        print("Training model...")
        import train
        if train.train_model():
            print(f"[OK] {name} is now registered!")
            return True
        else:
            print("[ERROR] Training failed")
            return False
    else:
        print(f"[ERROR] Need at least 10 photos (got {count})")
        return False

if __name__ == "__main__":
    success = register_thiru()
    sys.exit(0 if success else 1)
