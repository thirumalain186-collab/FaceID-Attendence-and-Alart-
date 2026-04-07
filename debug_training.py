"""
Debug training process
"""
import cv2
import numpy as np
import pickle
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

# Get active people
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

print(f"Person map: {person_map}")
print()

# Check dataset folders
dataset_dir = Path("dataset")
user_folders = [f for f in dataset_dir.iterdir() if f.is_dir()]

for user_folder in sorted(user_folders):
    folder_name = user_folder.name
    print(f"Folder: {folder_name}")
    
    matched_person = _best_match(folder_name, person_map)
    
    if matched_person:
        print(f"  MATCHED to: {matched_person['name']} ({matched_person['roll']})")
    else:
        print(f"  NOT MATCHED")
    
    image_files = list(user_folder.glob("*.jpg")) + list(user_folder.glob("*.png"))
    print(f"  Images: {len(image_files)}")
    print()
