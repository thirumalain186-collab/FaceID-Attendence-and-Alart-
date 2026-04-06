"""
Training Module for Smart Attendance System v2
Train LBPH Face Recognizer
FIXED: Robust folder parsing, proper database lookup
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import config
import database
from logger import get_logger

logger = get_logger()


def train_model():
    """Train the face recognition model"""
    logger.info("Starting model training")
    
    faces = []
    labels = []
    label_names = {}
    
    if not config.DATASET_DIR.exists():
        logger.error("Dataset directory not found")
        return False
    
    user_folders = [f for f in config.DATASET_DIR.iterdir() if f.is_dir()]
    
    if not user_folders:
        logger.error("No registered users found")
        return False
    
    logger.info(f"Found {len(user_folders)} registered users")
    
    people = database.get_active_people()
    person_map = {}
    for p in people:
        person_id, name, role, roll = p[0], p[1], p[2], p[3] or ""
        safe_name = name.replace(" ", "_").lower()
        person_map[safe_name] = {
            'id': person_id,
            'name': name,
            'role': role,
            'roll': roll
        }
    
    label_id = 0
    
    for user_folder in sorted(user_folders):
        folder_name = user_folder.name
        
        matched_person = None
        for safe_name, person_info in person_map.items():
            if safe_name in folder_name.lower():
                matched_person = person_info
                break
        
        if matched_person:
            person_name = matched_person['name']
            role = matched_person['role']
            roll = matched_person['roll']
        else:
            folder_safe = folder_name.replace("_", " ").replace("-", " ").strip()
            name_candidates = [w.title() for w in folder_safe.split() if w.isalpha()]
            person_name = " ".join(name_candidates) if name_candidates else folder_name
            role = "student"
            roll = ""
            
            for part in folder_name.replace("_", " ").split():
                if part.isdigit() and len(part) >= 2:
                    roll = part
                    break
        
        display = f"{person_name} ({roll or role})"
        label_names[label_id] = display
        
        image_files = list(user_folder.glob("*.jpg")) + list(user_folder.glob("*.png"))
        
        if not image_files:
            logger.warning(f"No images found for: {display}")
            continue
        
        logger.info(f"Loading {len(image_files)} images for: {display}")
        
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
                logger.warning(f"Error loading image {image_file}: {e}")
        
        if valid_count > 0:
            label_id += 1
    
    if not faces:
        logger.error("No valid face images found")
        return False
    
    logger.info(f"Training with {len(faces)} images, {len(label_names)} users")
    logger.info("Training model...")
    
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, 
            neighbors=8, 
            grid_x=8, 
            grid_y=8, 
            threshold=float(config.ATTENDANCE_CONFIG.get("confidence_threshold", 100))
        )
        
        faces_array = np.array(faces, dtype='uint8')
        labels_array = np.array(labels, dtype='int32')
        
        recognizer.train(faces_array, labels_array)
        
        config.TRAINER_DIR.mkdir(exist_ok=True)
        recognizer.save(str(config.TRAINER_FILE))
        
        logger.info("Training completed successfully")
        logger.info(f"Model saved: {config.TRAINER_FILE}")
        logger.info(f"Trained {len(label_names)} users:")
        for lid, name in sorted(label_names.items()):
            logger.info(f"  - {name}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Training failed: {e}")
        return False


if __name__ == "__main__":
    success = train_model()
    exit(0 if success else 1)
