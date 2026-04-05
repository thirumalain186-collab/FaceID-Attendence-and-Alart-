"""
Face Registration Module for Smart Attendance System v2
Register new people with webcam
"""

import cv2
from pathlib import Path
import config
import database
import attendance_engine


def register_person_webcam():
    """Register person using webcam"""
    print("\n" + "="*50)
    print("   FACE REGISTRATION - Webcam")
    print("="*50)
    
    name = input("\nEnter Name: ").strip()
    if not name:
        print("[ERROR] Name required")
        return False
    
    roll = input("Enter Roll Number: ").strip()
    if not roll:
        print("[ERROR] Roll number required")
        return False
    
    role = input("Role (student/teacher): ").strip().lower()
    if role not in ['student', 'teacher']:
        print("[ERROR] Role must be 'student' or 'teacher'")
        return False
    
    people = database.get_active_people()
    for p in people:
        if p[3] == roll:
            print(f"[ERROR] Roll number {roll} already registered!")
            return False
    
    print(f"\n[INFO] Registering: {name} ({roll})")
    
    camera = cv2.VideoCapture(config.ATTENDANCE_CONFIG["camera_index"])
    if not camera.isOpened():
        print("[ERROR] Cannot access camera")
        return False
    
    cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    if cascade.empty():
        print("[ERROR] Cannot load face detector")
        camera.release()
        return False
    
    safe_name = name.replace(" ", "_").lower()
    safe_roll = roll.replace(" ", "_").lower()
    person_dir = config.DATASET_DIR / f"{safe_name}_{safe_roll}_{role}"
    person_dir.mkdir(exist_ok=True)
    
    person_id = database.add_person(name, role, roll)
    print(f"[INFO] Added to database (ID: {person_id})")
    
    count = 0
    target = config.ATTENDANCE_CONFIG["samples_per_person"]
    
    print(f"\n[INFO] Capturing {target} face images...")
    print("[INFO] Press SPACE to capture, Q to quit\n")
    
    while count < target:
        ret, frame = camera.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.putText(frame, f"{name} ({roll})", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Captured: {count}/{target}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "SPACE=capture | Q=quit",
                   (10, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if len(faces) == 1:
            cv2.putText(frame, "Face detected!", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        elif len(faces) == 0:
            cv2.putText(frame, "No face detected",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        cv2.imshow("Registration", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and len(faces) == 1:
            x, y, w, h = faces[0]
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, tuple(config.ATTENDANCE_CONFIG["image_size"]))
            
            filename = f"{safe_name}_{safe_roll}_{count}.jpg"
            cv2.imwrite(str(person_dir / filename), face)
            
            count += 1
            print(f"  Captured {count}/{target}")
    
    camera.release()
    cv2.destroyAllWindows()
    
    if count > 0:
        print(f"\n[SUCCESS] Registered: {name} ({roll})")
        print(f"[INFO] Captured {count} images")
        print(f"[INFO] Run 'python train.py' to train the model")
        return True
    else:
        print("[WARNING] No images captured")
        return False


def list_people():
    """List all registered people"""
    people = database.get_active_people()
    
    if not people:
        print("[INFO] No registered people")
        return
    
    print("\n" + "="*60)
    print(f"{'Name':<25} {'Roll':<15} {'Role':<10}")
    print("-"*60)
    
    for p in people:
        name = p[1][:24]
        roll = p[3] or '-'
        role = p[2]
        print(f"{name:<25} {roll:<15} {role:<10}")
    
    print("-"*60)
    print(f"Total: {len(people)}")


def remove_person(name):
    """Remove a person from the system"""
    try:
        engine = attendance_engine.get_engine()
        engine.remove_person_safe(name)
    except Exception as e:
        database.remove_person(name)
        safe_name = name.replace(" ", "_").lower()
        for folder in config.DATASET_DIR.iterdir():
            if folder.is_dir() and safe_name in folder.name.lower():
                import shutil
                shutil.rmtree(folder, ignore_errors=True)
                break
    
    print(f"[SUCCESS] Removed: {name}")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("   SMART ATTENDANCE - REGISTRATION TOOL")
    print("="*50)
    print("\n1. Register new person (webcam)")
    print("2. List registered people")
    print("3. Remove person")
    print("4. Exit")
    
    while True:
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            register_person_webcam()
        elif choice == '2':
            list_people()
        elif choice == '3':
            name = input("Enter name to remove: ").strip()
            confirm = input(f"Remove '{name}'? (yes/no): ").strip().lower()
            if confirm == 'yes':
                remove_person(name)
        elif choice == '4':
            break
