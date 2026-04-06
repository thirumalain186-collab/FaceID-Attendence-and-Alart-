"""
Training Module for Smart Attendance System v2
Train LBPH Face Recognizer
"""

import cv2
import numpy as np
from pathlib import Path
import config
import database
from logger import get_logger

logger = get_logger()


def _best_match(folder_name, person_map):
    """Find best matching person for a folder name."""
    folder_lower = folder_name.lower()
    matches = []
    
    for safe_name, person_info in person_map.items():
        if safe_name in folder_lower:
            score = len(safe_name)
            matches.append((score, person_info))
    
    if not matches:
        return None
    
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


def _extract_roll_from_folder(folder_name):
    """Extract roll number from folder name."""
    parts = folder_name.replace("_", " ").replace("-", " ").split()
    for part in parts:
        if part.isdigit() and len(part) >= 3:
            return part
    return ""


def _load_image(image_path, target_size):
    """Load and preprocess image. Returns grayscale numpy array or None."""
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        if img.shape[0] < 20 or img.shape[1] < 20:
            return None
        img = cv2.resize(img, target_size)
        return img
    except Exception:
        return None


def train_model():
    """Train the face recognition model."""
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
        person_id = p.get('id')
        name = p.get('name', '')
        role = p.get('role', 'student')
        roll = p.get('roll_number') or ''
        
        if not name:
            continue
        
        safe_name = name.replace(" ", "_").lower()
        person_map[safe_name] = {
            'id': person_id,
            'name': name,
            'role': role.lower(),
            'roll': roll
        }
    
    target_size = tuple(config.ATTENDANCE_CONFIG.get("image_size", (200, 200)))
    threshold = float(config.ATTENDANCE_CONFIG.get("confidence_threshold", 100))
    
    label_id = 0
    total_images = 0
    skipped_images = 0
    
    for user_folder in sorted(user_folders):
        folder_name = user_folder.name
        
        matched_person = _best_match(folder_name, person_map)
        
        if matched_person:
            person_name = matched_person['name']
            role = matched_person['role']
            roll = matched_person['roll']
            person_id = matched_person['id']
            logger.debug(f"Matched folder '{folder_name}' to person ID {person_id}")
        else:
            logger.warning(f"Folder '{folder_name}' not matched to any registered person - skipping")
            continue
        
        display = f"{person_name} ({roll or role})"
        
        image_files = list(user_folder.glob("*.jpg")) + list(user_folder.glob("*.png"))
        
        if not image_files:
            logger.warning(f"No images found for: {display}")
            continue
        
        logger.info(f"Loading {len(image_files)} images for: {display}")
        
        valid_count = 0
        for image_file in image_files:
            img = _load_image(image_file, target_size)
            if img is None:
                skipped_images += 1
                logger.debug(f"Skipped invalid image: {image_file.name}")
                continue
            
            faces.append(img)
            labels.append(label_id)
            valid_count += 1
        
        if valid_count > 0:
            label_names[label_id] = display
            total_images += valid_count
            label_id += 1
    
    if not faces:
        logger.error("No valid face images found")
        logger.error(f"Skipped {skipped_images} invalid images across all folders")
        return False
    
    logger.info(f"Training with {total_images} images, {len(label_names)} users")
    
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2,
            neighbors=12,
            grid_x=8,
            grid_y=8,
            threshold=threshold
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
