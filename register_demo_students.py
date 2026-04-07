"""
Register Demo Students for Science Expo
Creates 5 additional synthetic students for multi-student testing
Uses existing registered faces and creates variations
"""
import os
import cv2
import numpy as np
import shutil
from pathlib import Path

def create_demo_face_variations(source_dir, target_dir, new_name, new_roll, num_images=20):
    """Create variations of a face by applying transformations"""
    os.makedirs(target_dir, exist_ok=True)
    
    # Get source face images
    source_files = list(Path(source_dir).glob("*.jpg"))
    if not source_files:
        print(f"  [ERROR] No images found in {source_dir}")
        return False
    
    source_img = cv2.imread(str(source_files[0]))
    if source_img is None:
        return False
    
    # Create variations and save
    saved = 0
    for i in range(num_images):
        # Apply random transformations
        angle = np.random.randint(-15, 15)
        scale = np.random.uniform(0.9, 1.1)
        brightness = np.random.uniform(0.8, 1.2)
        
        # Rotate
        center = (source_img.shape[1] // 2, source_img.shape[0] // 2)
        rot_matrix = cv2.getRotationMatrix2D(center, angle, scale)
        rotated = cv2.warpAffine(source_img, rot_matrix, (source_img.shape[1], source_img.shape[0]))
        
        # Adjust brightness
        adjusted = cv2.convertScaleAbs(rotated, alpha=brightness, beta=0)
        
        # Add slight gaussian noise
        noise = np.random.normal(0, 5, adjusted.shape).astype(np.uint8)
        final = cv2.add(adjusted, noise)
        
        # Save
        filename = os.path.join(target_dir, f"{new_name}_{new_roll}_{i}.jpg")
        cv2.imwrite(filename, final)
        saved += 1
    
    return saved == num_images

def main():
    print("\n" + "="*60)
    print("REGISTER DEMO STUDENTS FOR SCIENCE EXPO")
    print("="*60)
    
    students = [
        ("Raj", "03"),
        ("Priya", "04"),
        ("Vikram", "05"),
        ("Neha", "06"),
        ("Arjun", "07"),
    ]
    
    # Use Aizen's images as base for creating variations
    base_dir = "dataset/aizen_01_student"
    
    if not os.path.exists(base_dir):
        print(f"[ERROR] Base directory {base_dir} not found")
        return False
    
    print(f"\nCreating {len(students)} demo students using variations of existing faces...\n")
    
    for name, roll in students:
        safe_name = name.replace(" ", "_").lower()
        target_dir = f"dataset/{safe_name}_{roll}_student"
        
        print(f"Registering: {name} ({roll})...", end=" ", flush=True)
        
        if create_demo_face_variations(base_dir, target_dir, safe_name, roll, 20):
            print("[OK]")
        else:
            print("[FAILED]")
            return False
    
    print("\n" + "="*60)
    print("Training model with all students...")
    print("="*60 + "\n")
    
    import train
    if train.train_model():
        print("\n[OK] All demo students registered!")
        
        # Show summary
        import sqlite3
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM people')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"Total registered students: {count}")
        return True
    else:
        print("[FAILED] Training failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
