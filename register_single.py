"""
Simple Single Person Registration
Enter Name and Roll Number only
"""

import cv2
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import config

def register_single_person():
    """Register a single person with name and roll number"""
    
    print("\n" + "=" * 50)
    print("   SINGLE PERSON REGISTRATION")
    print("=" * 50)
    
    # Get user info
    name = input("\nEnter Name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty")
        return False
    
    roll = input("Enter Roll Number: ").strip()
    if not roll:
        print("[ERROR] Roll number cannot be empty")
        return False
    
    role = input("Enter Role (student/teacher): ").strip().lower()
    if role not in ['student', 'teacher']:
        print("[ERROR] Role must be 'student' or 'teacher'")
        return False
    
    print(f"\n[INFO] Registering: {name} ({roll})")
    print("[INFO] Press SPACE to capture face, Q to quit")
    
    # Initialize webcam
    cap = cv2.VideoCapture(config.ATTENDANCE_CONFIG["camera_index"])
    if not cap.isOpened():
        print("[ERROR] Cannot access camera")
        return False
    
    # Load cascade
    cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    if cascade.empty():
        print("[ERROR] Cannot load face detector")
        cap.release()
        return False
    
    # Create folders - use name and roll for unique identification
    safe_name = name.replace(" ", "_").lower()
    safe_roll = roll.replace(" ", "_").lower()
    person_dir = config.DATASET_DIR / f"{safe_name}_{safe_roll}_{role}"
    person_dir.mkdir(exist_ok=True, parents=True)
    
    config.KNOWN_FACES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Save to database
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                roll_number TEXT,
                email TEXT,
                class_name TEXT,
                registered_at TEXT
            )
        """)
        c.execute("SELECT id FROM people WHERE roll_number=?", (roll,))
        existing = c.fetchone()
        if existing:
            print("[WARNING] Roll number already registered!")
            conn.close()
            cap.release()
            return False
        
        c.execute("""
            INSERT INTO people (name, role, roll_number, class_name, registered_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, role, roll, config.ATTENDANCE_CONFIG["class_name"], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print("[INFO] Saved to database")
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        cap.release()
        return False
    
    # Capture images
    count = 0
    target = config.ATTENDANCE_CONFIG["samples_per_person"]
    
    while count < target:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.putText(frame, f"{name} ({roll})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Captured: {count}/{target}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "SPACE=capture | Q=quit", (10, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Registration", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and len(faces) == 1:
            x, y, w, h = faces[0]
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, config.ATTENDANCE_CONFIG["image_size"])
            
            filename = f"{safe_name}_{role}_{count}.jpg"
            cv2.imwrite(str(person_dir / filename), face)
            
            count += 1
            print(f"  Captured {count}/{target}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if count > 0:
        print(f"\n[SUCCESS] Registered: {name} ({roll})")
        print(f"[INFO] Captured {count} images")
        print(f"[NEXT] Run: python train.py")
        return True
    else:
        print("[WARNING] No images captured")
        return False

if __name__ == "__main__":
    register_single_person()
