"""
Debug training - step by step verification
"""
import cv2
import numpy as np
import pickle
from pathlib import Path
import config

print("=== DEBUG TRAINING ===\n")

# Find dataset folder
dataset_dir = config.DATASET_DIR
print(f"Dataset dir: {dataset_dir}")
print(f"Exists: {dataset_dir.exists()}\n")

# List registered users
user_folders = [f for f in dataset_dir.iterdir() if f.is_dir()]
print(f"Found {len(user_folders)} user folders:")
for uf in user_folders:
    images = list(uf.glob("*.jpg")) + list(uf.glob("*.png"))
    print(f"  - {uf.name}: {len(images)} images")
    # Show first 3 image names
    for img in images[:3]:
        print(f"    * {img.name}")

print("\n=== LOAD & VERIFY IMAGES ===\n")

target_size = (200, 200)
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
label_names = {}
label_id = 0

for user_folder in sorted(user_folders):
    folder_name = user_folder.name
    image_files = list(user_folder.glob("*.jpg")) + list(user_folder.glob("*.png"))
    
    print(f"\nProcessing: {folder_name}")
    print(f"  Total images: {len(image_files)}")
    
    valid_count = 0
    for idx, image_file in enumerate(image_files):
        # Load image
        img = cv2.imread(str(image_file), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"    [{idx}] FAILED to read: {image_file.name}")
            continue
        
        if img.shape[0] < 20 or img.shape[1] < 20:
            print(f"    [{idx}] TOO SMALL ({img.shape}): {image_file.name}")
            continue
        
        img_resized = cv2.resize(img, target_size)
        
        # Check face detection
        detected_faces = cascade.detectMultiScale(img_resized, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
        
        if len(detected_faces) > 0:
            print(f"    [{idx}] OK ({img.shape} -> {img_resized.shape}, face detected): {image_file.name}")
            faces.append(img_resized)
            labels.append(label_id)
            valid_count += 1
        else:
            print(f"    [{idx}] NO FACE DETECTED: {image_file.name}")
    
    if valid_count > 0:
        display = f"{folder_name}"
        label_names[label_id] = display
        print(f"  ✓ Loaded {valid_count} valid images for label {label_id}")
        label_id += 1
    else:
        print(f"  ✗ NO VALID IMAGES FOR THIS FOLDER")

print(f"\n=== SUMMARY ===")
print(f"Total faces loaded: {len(faces)}")
print(f"Total labels: {len(labels)}")
print(f"Unique label_ids: {len(label_names)}")
print(f"Label mapping: {label_names}")

if len(faces) > 0:
    print(f"\n=== TRAINING ===")
    faces_array = np.array(faces, dtype='uint8')
    labels_array = np.array(labels, dtype='int32')
    
    print(f"Faces array shape: {faces_array.shape}")
    print(f"Labels array shape: {labels_array.shape}")
    
    try:
        import cv2.face as cv2_face
        recognizer = cv2_face.LBPHFaceRecognizer_create(
            radius=2,
            neighbors=12,
            grid_x=8,
            grid_y=8,
            threshold=100
        )
        
        recognizer.train(faces_array, labels_array)
        print("✓ Training completed")
        
        # Test on first image
        print(f"\n=== TEST ON FIRST IMAGE ===")
        test_img = faces[0]
        label, confidence = recognizer.predict(test_img)
        print(f"Predicted: label={label}, confidence={confidence}")
        print(f"Expected: label=0 (first trained user)")
        
        if label == 0:
            print("✓ TEST PASSED!")
        else:
            print("✗ TEST FAILED - Model didn't recognize its own training image")
            
    except Exception as e:
        print(f"✗ Training failed: {e}")
