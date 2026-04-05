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
    
    label_id = 0
    
    for user_folder in sorted(user_folders):
        folder_name = user_folder.name
        parts = folder_name.rsplit('_', 1)
        
        if len(parts) != 2:
            logger.warning(f"Invalid folder format: {folder_name}")
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
                logger.warning(f"Error loading image: {e}")
        
        if valid_count > 0:
            label_id += 1
    
    if not faces:
        logger.error("No valid face images found")
        return False
    
    logger.info(f"Training with {len(faces)} images, {len(label_names)} users")
    logger.info("Training model...")
    
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0
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
    train_model()
