"""
Training Module for Smart Attendance System v2
Train LBPH Face Recognizer
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import config
import database


def train_model():
    """Train the face recognition model"""
    print("\n" + "="*50)
    print("   MODEL TRAINING")
    print("="*50)
    
    faces = []
    labels = []
    label_names = {}
    
    if not config.DATASET_DIR.exists():
        print("[ERROR] Dataset directory not found")
        return False
    
    user_folders = [f for f in config.DATASET_DIR.iterdir() if f.is_dir()]
    
    if not user_folders:
        print("[ERROR] No registered users found")
        return False
    
    print(f"[INFO] Found {len(user_folders)} registered users")
    print("-"*50)
    
    label_id = 0
    
    for user_folder in sorted(user_folders):
        folder_name = user_folder.name
        parts = folder_name.rsplit('_', 1)
        
        if len(parts) != 2:
            print(f"[WARNING] Invalid folder: {folder_name}")
            continue
        
        person_name = parts[0].replace("_", " ").title()
        role = parts[1]
        roll = ""
        
        try:
            people = database.get_active_people()
            for p in people:
                safe_db = p[1].replace(" ", "_").lower()
                if safe_db in folder_name.lower():
                    person_name = p[1]
                    role = p[2]
                    roll = p[3] or ""
                    break
        except:
            pass
        
        if not roll:
            name_parts = folder_name.replace("_", " ").split()
            for part in name_parts:
                if part.isdigit():
                    roll = part
                    break
        
        display = f"{person_name} ({roll or role})"
        label_names[label_id] = display
        
        image_files = list(user_folder.glob("*.jpg")) + list(user_folder.glob("*.png"))
        
        if not image_files:
            print(f"[WARNING] No images: {display}")
            continue
        
        print(f"[INFO] Loading {len(image_files)} images for: {display}")
        
        valid_count = 0
        for image_file in image_files:
            try:
                pil_image = Image.open(image_file).convert('L')
                numpy_image = np.array(pil_image, 'uint8')
                numpy_image = cv2.resize(numpy_image, tuple(config.ATTENDANCE_CONFIG["image_size"]))
                
                faces.append(numpy_image)
                labels.append(label_id)
                valid_count += 1
            except Exception as e:
                print(f"[WARNING] Error: {e}")
        
        if valid_count > 0:
            label_id += 1
    
    if not faces:
        print("[ERROR] No valid face images")
        return False
    
    print("-"*50)
    print(f"[INFO] Total: {len(faces)} images, {len(label_names)} users")
    print("\n[INFO] Training...")
    
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0
        )
        
        faces_array = np.array(faces, dtype='uint8')
        labels_array = np.array(labels, dtype='int32')
        
        recognizer.train(faces_array, labels_array)
        
        config.TRAINER_DIR.mkdir(exist_ok=True)
        recognizer.save(str(config.TRAINER_FILE))
        
        print("="*50)
        print("   TRAINING COMPLETED!")
        print("="*50)
        print(f"[INFO] Model: {config.TRAINER_FILE}")
        print(f"[INFO] {len(label_names)} users:")
        for lid, name in sorted(label_names.items()):
            print(f"  - {name}")
        print("\n[NEXT] Run 'python main.py'")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


if __name__ == "__main__":
    train_model()
