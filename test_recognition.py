import cv2
import cv2.face as cv2_face
import os
from attendance_engine import AttendanceEngine

# Load model
recognizer = cv2_face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Get engine label mapping
engine = AttendanceEngine()

print('=' * 50)
print('Testing Recognition')
print('=' * 50)

# Test with images from each folder
folders = ['dataset/manoj_2_student', 'dataset/manojkumar_1_student', 'dataset/thiru_3_student']

for folder in folders:
    images = [f for f in os.listdir(folder) if f.endswith(('.jpg', '.png'))][:2]
    for img_file in images:
        img_path = os.path.join(folder, img_file)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (200, 200))
        label, conf = recognizer.predict(img)
        
        person_info = engine.label_names.get(label, {})
        name = person_info.get('original_name', 'Unknown')
        
        print(f'{folder}: Label={label}, Conf={conf:.1f} -> {name}')
