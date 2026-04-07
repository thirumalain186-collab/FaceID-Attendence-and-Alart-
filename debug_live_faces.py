"""
Debug live camera face preprocessing
"""
import cv2
import numpy as np

# Load cascade
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open camera
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

print("Camera opened. Press SPACE to capture a face.")

captured_faces = []

while len(captured_faces) < 3:
    ret, frame = cap.read()
    if not ret:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(80, 80))
    
    # Draw rectangles
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    cv2.putText(frame, f"Faces: {len(faces)} (Press SPACE to capture)", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Camera", frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' ') and len(faces) == 1:
        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200, 200))
        captured_faces.append({
            'raw': face_roi,
            'resized': face_resized,
            'size': face_roi.shape,
            'dtype': face_roi.dtype,
            'min': face_roi.min(),
            'max': face_roi.max(),
            'mean': face_roi.mean()
        })
        print(f"Captured face {len(captured_faces)}")
    
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Analyze captured faces
print("\nCaptured face analysis:")
for i, face_data in enumerate(captured_faces):
    print(f"\nFace {i+1}:")
    print(f"  Original size: {face_data['size']}")
    print(f"  Data type: {face_data['dtype']}")
    print(f"  Value range: {face_data['min']:.0f} - {face_data['max']:.0f}")
    print(f"  Mean: {face_data['mean']:.0f}")
    
    resized = face_data['resized']
    print(f"  Resized size: {resized.shape}")
    print(f"  Resized dtype: {resized.dtype}")
    print(f"  Resized range: {resized.min():.0f} - {resized.max():.0f}")
    print(f"  Resized mean: {resized.mean():.0f}")
    
    # Check if resized is valid
    if not np.isfinite(resized).all():
        print(f"  WARNING: Non-finite values in resized face!")
    
    # Test prediction
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainer/trainer.yml')
    
    try:
        label, confidence = recognizer.predict(resized)
        print(f"  Prediction: label={label}, confidence={confidence}")
        if np.isinf(confidence):
            print(f"  ERROR: Confidence is infinity!")
    except Exception as e:
        print(f"  Prediction error: {e}")
