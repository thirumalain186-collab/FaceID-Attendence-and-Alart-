"""
Face Registration Module for Smart Attendance System v2
Register new people with webcam
"""

import cv2
import shutil
from pathlib import Path
import config
import database
import attendance_engine
from logger import get_logger

logger = get_logger()


def _generate_folder_name(name, roll, role):
    """Generate consistent folder name. Format: name_roll_role."""
    safe_name = "".join(c if c.isalnum() else "_" for c in name).lower()
    safe_name = safe_name.strip("_")
    safe_roll = "".join(c if c.isalnum() else "_" for c in roll).lower()
    safe_roll = safe_roll.strip("_")
    return f"{safe_name}_{safe_roll}_{role.lower()}"


def register_person_webcam():
    """Register person using webcam with transaction safety."""
    logger.info("Starting face registration")
    
    name = input("\nEnter Name: ").strip()
    if not name or len(name) > 50:
        logger.error("Valid name required (max 50 chars)")
        return False
    
    roll = input("Enter Roll Number: ").strip()
    if not roll or len(roll) > 30:
        logger.error("Valid roll number required (max 30 chars)")
        return False
    
    role_input = input("Role (student/teacher) [default: student]: ").strip().lower()
    role = role_input if role_input in ('student', 'teacher') else 'student'
    
    people = database.get_active_people()
    for p in people:
        p_name = p.get('name', '')
        p_roll = p.get('roll_number') or ''
        
        if p_name.lower() == name.lower():
            logger.error(f"Name '{name}' already registered")
            return False
        if p_roll.lower() == roll.lower():
            logger.error(f"Roll number {roll} already registered")
            return False
    
    folder_name = _generate_folder_name(name, roll, role)
    person_dir = config.DATASET_DIR / folder_name
    
    if person_dir.exists():
        logger.error(f"Dataset folder already exists: {folder_name}")
        return False
    
    person_id = None
    camera = None
    try:
        person_id = database.add_person(name, role, roll)
        if person_id is None:
            logger.error("Failed to add person to database")
            return False
        
        logger.info(f"Added to database (ID: {person_id})")
        
        camera = cv2.VideoCapture(config.ATTENDANCE_CONFIG.get("camera_index", 0))
        if not camera.isOpened():
            logger.error("Cannot access camera")
            database.remove_person(name)
            return False
        
        cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
        if cascade.empty():
            logger.error("Cannot load face detector")
            camera.release()
            database.remove_person(name)
            return False
        
        person_dir.mkdir(exist_ok=True)
        
        count = 0
        target = config.ATTENDANCE_CONFIG.get("samples_per_person", 30)
        min_required = 5
        image_size = tuple(config.ATTENDANCE_CONFIG.get("image_size", (200, 200)))
        
        logger.info(f"Capturing {target} face images (minimum {min_required})")
        print(f"\nPress SPACE to capture, Q to quit (minimum {min_required} images required)\n")
        
        while count < target:
            ret, frame = camera.read()
            if not ret:
                logger.warning("Camera read failed")
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            display_name = f"{name} ({roll})"[:40]
            cv2.putText(frame, display_name, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Captured: {count}/{target}",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, "SPACE=capture | Q=quit",
                       (10, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            face_status = "Face detected!" if len(faces) == 1 else ("No face" if len(faces) == 0 else "Multiple faces")
            color = (0, 255, 0) if len(faces) == 1 else (0, 0, 255)
            cv2.putText(frame, face_status, (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            cv2.imshow("Registration", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' ') and len(faces) == 1:
                x, y, w, h = faces[0]
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, image_size)
                
                filename = f"{folder_name}_{count}.jpg"
                success = cv2.imwrite(str(person_dir / filename), face)
                
                if success:
                    count += 1
                    logger.debug(f"Captured {count}/{target}")
    
    finally:
        if camera:
            camera.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    
    if count >= min_required:
        logger.info(f"Registered: {name} ({roll}) with {count} images")
        print(f"\n[SUCCESS] Registered: {name} ({roll}) - ID: {person_id}")
        print(f"[INFO] Captured {count} images")
        print(f"[INFO] Run 'python train.py' to train the model")
        
        try:
            engine = attendance_engine.get_engine()
            engine.reload_faces()
        except Exception as e:
            logger.debug(f"Could not reload engine: {e}")
        
        return True
    else:
        logger.warning(f"Insufficient images captured ({count}/{min_required}) - rolling back")
        database.remove_person(name)
        if person_dir.exists():
            shutil.rmtree(person_dir, ignore_errors=True)
        print(f"\n[FAILED] Registration cancelled: need at least {min_required} images")
        return False


def list_people():
    """List all registered people."""
    people = database.get_active_people()
    
    if not people:
        print("[INFO] No registered people")
        return
    
    print("\n" + "="*60)
    print(f"{'Name':<25} {'Roll':<15} {'Role':<10}")
    print("-"*60)
    
    for p in people:
        name = str(p.get('name', ''))[:24]
        roll = p.get('roll_number') or '-'
        role = p.get('role', '')
        print(f"{name:<25} {roll:<15} {role:<10}")
    
    print("-"*60)
    print(f"Total: {len(people)}")
    logger.info(f"Listed {len(people)} registered people")


def remove_person(name):
    """Remove a person from the system."""
    try:
        engine = attendance_engine.get_engine()
        engine.remove_person_safe(name)
    except Exception:
        database.remove_person(name)
        folder_name = _generate_folder_name(name, "", "student")
        for folder in config.DATASET_DIR.iterdir():
            if folder.is_dir() and folder.name.startswith(folder_name.split("_")[0]):
                shutil.rmtree(folder, ignore_errors=True)
                break
    
    logger.info(f"Removed: {name}")


if __name__ == "__main__":
    logger.info("Starting registration tool")
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
            if not name:
                continue
            confirm = input(f"Remove '{name}'? (yes/no): ").strip().lower()
            if confirm == 'yes':
                remove_person(name)
        elif choice == '4':
            break
