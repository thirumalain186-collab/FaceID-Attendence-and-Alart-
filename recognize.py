"""
Face Recognition and Attendance Module for Smart Attendance System
Detects and recognizes faces, marks attendance, and alerts for unknown persons
"""

import cv2
import os
import numpy as np
from datetime import datetime
import config
import email_alert
from logger import get_logger

logger = get_logger()


class AttendanceSystem:
    """Main attendance system class handling face recognition and attendance"""
    
    def __init__(self):
        """Initialize the attendance system"""
        self.recognizer = None
        self.label_names = {}
        self.cascade = None
        self.marked_today = set()
        self.session_attendance = set()
        self.start_time = datetime.now()
        
    def load_model(self):
        """
        Load trained model and Haar cascade classifier
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not os.path.exists(config.TRAINER_FILE):
            logger.error(f"Model not found: {config.TRAINER_FILE}")
            return False
        
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(config.TRAINER_FILE)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.exception(f"Failed to load model: {e}")
            return False
        
        if not os.path.exists(config.HAAR_CASCADE_PATH):
            logger.error(f"Haar Cascade not found: {config.HAAR_CASCADE_PATH}")
            return False
        
        self.cascade = cv2.CascadeClassifier(config.HAAR_CASCADE_PATH)
        
        if self.cascade.empty():
            logger.error("Failed to load Haar Cascade")
            return False
        
        logger.info("Haar Cascade loaded")
        
        self.load_label_names()
        
        return True
    
    def load_label_names(self):
        """Load label names from dataset folder structure"""
        if not os.path.exists(config.DATASET_DIR):
            return
        
        label_id = 0
        for user_folder in sorted(os.listdir(config.DATASET_DIR)):
            user_path = os.path.join(config.DATASET_DIR, user_folder)
            
            if not os.path.isdir(user_path):
                continue
            
            parts = user_folder.rsplit('_', 1)
            if len(parts) == 2:
                user_name, user_role = parts
                self.label_names[label_id] = f"{user_name} ({user_role})"
                label_id += 1
    
    def mark_attendance(self, name, role, confidence):
        """
        Mark attendance for a recognized user
        
        Args:
            name: Recognized person's name
            role: Recognized person's role
            confidence: Recognition confidence score
        
        Returns:
            bool: True if attendance marked, False if already marked
        """
        if name in self.session_attendance:
            return False
        
        self.session_attendance.add(name)
        
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        time_str = current_time.strftime("%H:%M:%S")
        
        attendance_record = f"{name},{role},{date_str},{time_str},{confidence:.2f}"
        
        file_exists = os.path.exists(config.ATTENDANCE_FILE)
        
        try:
            with open(config.ATTENDANCE_FILE, 'a', newline='') as f:
                f.write(attendance_record + '\n')
            
            logger.info(f"Attendance marked: {name} ({role}) at {time_str}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to save attendance: {e}")
            return False
    
    def save_unknown_image(self, face_roi, person_id):
        """
        Save unknown person's image for review
        
        Args:
            face_roi: Face region of interest
            person_id: Unique identifier for the unknown person
        
        Returns:
            str: Path to saved image or None
        """
        try:
            os.makedirs(config.UNKNOWN_DIR, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unknown_{timestamp}_{person_id}.jpg"
            filepath = os.path.join(config.UNKNOWN_DIR, filename)
            
            if face_roi is not None and face_roi.size > 0:
                cv2.imwrite(filepath, face_roi)
                return filepath
            
            return None
            
        except Exception as e:
            logger.exception(f"Failed to save unknown image: {e}")
            return None
    
    def process_unknown(self, face_roi, confidence):
        """
        Process unknown person detection and send alerts
        
        Args:
            face_roi: Face region of interest
            confidence: Recognition confidence score
        """
        person_id = len(os.listdir(config.UNKNOWN_DIR)) if os.path.exists(config.UNKNOWN_DIR) else 0
        
        image_path = self.save_unknown_image(face_roi, person_id)
        
        if image_path:
            conf_display = f"{confidence:.2f}" if 0 < confidence < 1000 else "N/A"
            logger.warning(f"Unknown person detected! Confidence: {conf_display}")
            logger.info(f"Unknown face saved to: {image_path}")
            
            logger.info("Sending email alert...")
            email_alert.send_unknown_alert(image_path, "Unknown Person")
    
    def run(self):
        """
        Main recognition loop
        
        Returns:
            None
        """
        if not self.load_model():
            logger.error("Failed to initialize recognition system")
            return
        
        cap = cv2.VideoCapture(config.ATTENDANCE_CONFIG["camera_index"])
        
        if not cap.isOpened():
            logger.error("Cannot access webcam")
            return
        
        print("\n" + "=" * 60)
        print("     SMART ATTENDANCE SYSTEM - LIVE RECOGNITION")
        print("=" * 60)
        print(f"[INFO] Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("[INFO] Press 'q' to quit | Press 's' to save screenshot")
        print("[INFO] Press 'a' to show attendance list")
        print("-" * 60)
        
        frame_count = 0
        unknown_detection_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    logger.error("Failed to capture frame")
                    break
                
                frame_count += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                faces = self.cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.3,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                current_time = datetime.now()
                time_str = current_time.strftime("%H:%M:%S")
                
                cv2.putText(frame, f"Time: {time_str}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Recognized: {len(self.session_attendance)}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    face_roi = gray[y:y + h, x:x + w]
                    
                    if face_roi.size == 0:
                        continue
                    
                    try:
                        label, confidence = self.recognizer.predict(face_roi)
                        
                        if confidence < config.ATTENDANCE_CONFIG["confidence_threshold"]:
                            name = self.label_names.get(label, "Unknown")
                            
                            parts = name.rsplit(' (', 1)
                            if len(parts) == 2:
                                person_name = parts[0]
                                role = parts[1].rstrip(')')
                            else:
                                person_name = name
                                role = "Unknown"
                            
                            cv2.putText(frame, person_name, (x, y - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.putText(frame, f"Conf: {100 - confidence:.0f}%", 
                                       (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                                       (0, 255, 0), 1)
                            
                            self.mark_attendance(person_name, role, confidence)
                            
                        else:
                            cv2.putText(frame, "Unknown", (x, y - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            cv2.putText(frame, f"Conf: {100 - confidence:.0f}%", 
                                       (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                                       (0, 0, 255), 1)
                            
                            unknown_detection_count += 1
                            if unknown_detection_count >= 5:
                                self.process_unknown(face_roi, confidence)
                                unknown_detection_count = 0
                                
                    except cv2.error as e:
                        logger.error(f"Recognition error: {e}")
                        continue
                
                cv2.imshow("Smart Attendance System", frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    logger.info("Quitting...")
                    break
                    
                elif key == ord('s'):
                    screenshot_path = os.path.join(
                        config.UNKNOWN_DIR if os.path.exists(config.UNKNOWN_DIR) else ".",
                        f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    )
                    cv2.imwrite(screenshot_path, frame)
                    logger.info(f"Screenshot saved: {screenshot_path}")
                    
                elif key == ord('a'):
                    print("\n" + "=" * 60)
                    print("           TODAY'S ATTENDANCE")
                    print("=" * 60)
                    if self.session_attendance:
                        for i, name in enumerate(sorted(self.session_attendance), 1):
                            print(f"{i}. {name}")
                    else:
                        print("No attendance recorded yet.")
                    print("=" * 60)
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
            print("\n" + "=" * 60)
            print("           SESSION SUMMARY")
            print("=" * 60)
            print(f"[INFO] Total frames processed: {frame_count}")
            print(f"[INFO] Attendance marked: {len(self.session_attendance)}")
            print(f"[INFO] Session ended at: {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)


def show_attendance_records():
    """Display all attendance records from CSV file."""
    if not os.path.exists(config.ATTENDANCE_FILE):
        logger.info("No attendance records found")
        return
    
    try:
        with open(config.ATTENDANCE_FILE, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            logger.info("Attendance file is empty")
            return
        
        print("\n" + "=" * 80)
        print("                      ATTENDANCE RECORDS")
        print("=" * 80)
        print(f"{'Name':<25} {'Role':<12} {'Date':<15} {'Time':<12} {'Confidence':<10}")
        print("-" * 80)
        
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                name = parts[0]
                role = parts[1]
                date = parts[2]
                time = parts[3]
                conf = parts[4]
                print(f"{name:<25} {role:<12} {date:<15} {time:<12} {conf:<10}")
        
        print("-" * 80)
        print(f"Total records: {len(lines) - 1}")
        print("=" * 80)
        
    except Exception as e:
        logger.exception(f"Failed to read attendance file: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        print("=" * 60)
        print("     SMART ATTENDANCE SYSTEM - VIEW ATTENDANCE")
        print("=" * 60)
        show_attendance_records()
    else:
        print("=" * 60)
        print("     SMART ATTENDANCE SYSTEM - FACE RECOGNITION")
        print("=" * 60)
        print("\nInstructions:")
        print("- The system will automatically detect and recognize faces")
        print("- Attendance will be marked automatically for recognized users")
        print("- Unknown persons will trigger email alerts")
        print("- Press 'q' to quit")
        print("- Press 's' to save a screenshot")
        print("- Press 'a' to view today's attendance")
        print("\n" + "-" * 60)
        
        try:
            system = AttendanceSystem()
            system.run()
        except Exception as e:
            logger.exception(f"Failed to start attendance system: {e}")
