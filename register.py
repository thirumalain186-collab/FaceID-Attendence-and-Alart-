"""
Face Registration Module for Smart Attendance System
Captures face images from webcam and saves them to dataset folder
"""

import cv2
import os
import numpy as np
from datetime import datetime
import config


def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(config.DATASET_DIR, exist_ok=True)
    os.makedirs(config.UNKNOWN_DIR, exist_ok=True)


def validate_name(name):
    """
    Validate user input for name
    
    Args:
        name: User's name input
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not name or len(name.strip()) < 2:
        print("[ERROR] Name must be at least 2 characters long.")
        return False
    if any(char.isdigit() for char in name):
        print("[ERROR] Name should not contain numbers.")
        return False
    return True


def validate_role(role):
    """
    Validate user input for role
    
    Args:
        role: User's role input
    
    Returns:
        bool: True if valid, False otherwise
    """
    role = role.lower().strip()
    valid_roles = ["student", "teacher"]
    if role not in valid_roles:
        print(f"[ERROR] Role must be either 'student' or 'teacher'.")
        return False
    return True


def get_user_info():
    """
    Get user information (name and role) from user input
    
    Returns:
        tuple: (name, role) if valid, (None, None) otherwise
    """
    try:
        print("\n" + "=" * 60)
        print("           FACE REGISTRATION - USER INFORMATION")
        print("=" * 60)
        
        name = input("\nEnter your Name: ").strip()
        if not validate_name(name):
            return None, None
        
        role = input("Enter your Role (student/teacher): ").strip()
        if not validate_role(role):
            return None, None
        
        return name, role
        
    except KeyboardInterrupt:
        print("\n[INFO] Registration cancelled by user.")
        return None, None


def load_haar_cascade():
    """
    Load Haar Cascade classifier for face detection
    
    Returns:
        cv2.CascadeClassifier: Loaded cascade classifier
    """
    if not os.path.exists(config.HAAR_CASCADE_PATH):
        print(f"[ERROR] Haar Cascade file not found: {config.HAAR_CASCADE_PATH}")
        print("[HINT] Download haarcascade_frontalface_default.xml and place it in the project directory.")
        return None
    
    cascade = cv2.CascadeClassifier(config.HAAR_CASCADE_PATH)
    if cascade.empty():
        print("[ERROR] Failed to load Haar Cascade classifier.")
        return None
    
    return cascade


def capture_face_images(name, role):
    """
    Capture face images from webcam and save to dataset
    
    Args:
        name: User's name
        role: User's role (student/teacher)
    
    Returns:
        bool: True if capture successful, False otherwise
    """
    cap = cv2.VideoCapture(config.ATTENDANCE_CONFIG["camera_index"])
    
    if not cap.isOpened():
        print("[ERROR] Cannot access webcam. Please check if camera is connected.")
        return False
    
    cascade = load_haar_cascade()
    if cascade is None:
        cap.release()
        return False
    
    user_folder = os.path.join(config.DATASET_DIR, f"{name}_{role}")
    os.makedirs(user_folder, exist_ok=True)
    
    existing_images = len([f for f in os.listdir(user_folder) if f.endswith('.jpg')])
    start_count = existing_images
    target_count = config.ATTENDANCE_CONFIG["samples_per_person"]
    total_to_capture = start_count + target_count
    
    print(f"\n[INFO] Starting face capture for: {name} ({role})")
    print(f"[INFO] Already captured: {existing_images} images")
    print(f"[INFO] Need to capture: {target_count} more images")
    print("[INFO] Press 'q' to quit or 's' to skip")
    print("-" * 60)
    
    count = start_count
    required_detections = 0
    min_detections = 3
    
    print("[INFO] Look at the camera and keep your face centered...")
    
    while count < total_to_capture:
        ret, frame = cap.read()
        
        if not ret:
            print("[ERROR] Failed to capture frame from webcam.")
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            face_roi = gray[y:y + h, x:x + w]
            
            if face_roi.size > 0:
                cv2.imwrite(
                    os.path.join(user_folder, f"{name}_{count}.jpg"),
                    face_roi
                )
                count += 1
        
        remaining = total_to_capture - count
        progress = ((count - start_count) / target_count) * 100
        
        cv2.putText(frame, f"Capturing: {name} ({role})", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Progress: {progress:.1f}% ({count - start_count}/{target_count})", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Remaining: {remaining}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Face Registration", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n[INFO] Capture stopped by user.")
            break
        elif key == ord('s'):
            print("\n[INFO] Capture skipped.")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    captured = count - start_count
    print(f"\n[INFO] Captured {captured} images for {name} ({role})")
    
    if captured >= min_detections:
        print("[SUCCESS] Sufficient images captured for training!")
        return True
    else:
        print(f"[WARNING] Only captured {captured} images. Need at least {min_detections} for training.")
        return False


def register_user():
    """
    Main registration workflow
    
    Returns:
        bool: True if registration successful, False otherwise
    """
    create_directories()
    
    name, role = get_user_info()
    if name is None:
        return False
    
    print(f"\n[INFO] Initializing webcam for {name}...")
    
    success = capture_face_images(name, role)
    
    if success:
        print("\n" + "=" * 60)
        print("           REGISTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Name: {name}")
        print(f"Role: {role}")
        print(f"Dataset: {os.path.join(config.DATASET_DIR, f'{name}_{role}')}")
        print("\n[NEXT STEP] Run 'train.py' to train the face recognition model.")
    else:
        print("\n[ERROR] Registration failed. Please try again.")
    
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("     SMART ATTENDANCE SYSTEM - FACE REGISTRATION")
    print("=" * 60)
    print("\nInstructions:")
    print("- Enter your name and role (student/teacher)")
    print("- Look at the camera and keep your face visible")
    print("- System will automatically capture 30 face images")
    print("- You can press 'q' to quit or 's' to skip")
    print("\n" + "-" * 60)
    
    try:
        register_user()
    except KeyboardInterrupt:
        print("\n[INFO] Program interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
