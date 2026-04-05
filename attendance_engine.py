"""
Attendance Engine for Smart Attendance System v2
Face recognition, camera control, and attendance marking
"""

import cv2
import numpy as np
import threading
import time
from datetime import datetime, date, time as dt_time
from pathlib import Path
import config
import database
import email_sender
import pdf_generator


class AttendanceEngine:
    """Main attendance system with camera control"""
    
    def __init__(self):
        self.running = False
        self.camera = None
        self.recognizer = None
        self.cascade = None
        self.face_db = {}
        self.label_names = {}
        
        self.marked_today = set()
        self.last_seen = {}
        self.last_alert_time = {}
        self.alert_cooldown = config.ATTENDANCE_CONFIG["unknown_alert_cooldown"]
        
        self.mode = "idle"
        self.frame_count = 0
        self.face_lock = threading.Lock()
        
        self.load_resources()
    
    def load_resources(self):
        """Load cascade and model"""
        if config.HAAR_CASCADE_PATH.exists():
            self.cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
            print("[ENGINE] Haar cascade loaded")
        else:
            print("[ENGINE] ERROR: Haar cascade not found")
        
        if config.TRAINER_FILE.exists():
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(str(config.TRAINER_FILE))
            print("[ENGINE] LBPH model loaded")
        else:
            print("[ENGINE] WARNING: Model not trained")
        
        self.reload_faces()
    
    def reload_faces(self):
        """Reload face database - thread safe"""
        with self.face_lock:
            self.face_db = {}
            self.label_names = {}
            label_id = 0
            
            people = database.get_active_people()
            for person in people:
                person_id, name, role, roll_number = person[0], person[1], person[2], person[3]
                safe_name = name.replace(" ", "_").lower()
                
                for folder in config.DATASET_DIR.iterdir():
                    if folder.is_dir() and safe_name in folder.name.lower():
                        self.label_names[label_id] = {
                            'name': name,
                            'role': role,
                            'roll': roll_number or ''
                        }
                        label_id += 1
                        break
            
            print(f"[ENGINE] Loaded {len(self.label_names)} registered people")
    
    def remove_person_safe(self, name):
        """Remove person without stopping camera"""
        database.remove_person(name)
        self.reload_faces()
        
        safe_name = name.replace(" ", "_").lower()
        for folder in config.DATASET_DIR.iterdir():
            if folder.is_dir() and safe_name in folder.name.lower():
                import shutil
                shutil.rmtree(folder, ignore_errors=True)
                break
        
        print(f"[ENGINE] Removed {name}")
    
    def start_camera(self, mode="attendance"):
        """Start camera in specified mode"""
        if self.running:
            print("[ENGINE] Camera already running")
            return
        
        self.running = True
        self.mode = mode
        self.camera = cv2.VideoCapture(config.ATTENDANCE_CONFIG["camera_index"])
        
        if not self.camera.isOpened():
            print("[ENGINE] ERROR: Cannot open camera")
            self.running = False
            return
        
        print(f"[ENGINE] Camera started in {mode} mode")
        
        thread = threading.Thread(target=self._camera_loop, daemon=True)
        thread.start()
    
    def stop_camera(self):
        """Stop camera"""
        self.running = False
        self.mode = "idle"
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        print("[ENGINE] Camera stopped")
    
    def _camera_loop(self):
        """Main camera processing loop"""
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            if self.frame_count % config.ATTENDANCE_CONFIG["frame_skip"] != 0:
                self._show_frame(frame)
                continue
            
            self._process_frame(frame)
            self._show_frame(frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_camera()
                break
    
    def _process_frame(self, frame):
        """Process single frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=config.ATTENDANCE_CONFIG["scale_factor"],
            minNeighbors=config.ATTENDANCE_CONFIG["min_neighbors"],
            minSize=tuple(config.ATTENDANCE_CONFIG["min_face_size"])
        )
        
        current_time = time.time()
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, tuple(config.ATTENDANCE_CONFIG["image_size"]))
            
            try:
                label, confidence = self.recognizer.predict(face_resized)
                lbph_confidence = max(0, 100 - confidence)
                
                if confidence < config.ATTENDANCE_CONFIG["confidence_threshold"]:
                    face_info = self.label_names.get(label, {})
                    name = face_info.get('name', 'Unknown')
                    role = face_info.get('role', 'unknown')
                    roll = face_info.get('roll', '')
                    
                    label_text = f"{name} ({roll or role})"
                    color = (0, 200, 0) if role == 'student' else (200, 150, 0)
                    
                    if self.mode == "attendance":
                        self._mark_attendance(name, role, roll)
                    elif self.mode == "monitoring":
                        self._log_movement(name, role)
                else:
                    label_text = "UNKNOWN"
                    color = (0, 0, 220)
                    
                    face_key = f"{x}_{y}"
                    if face_key not in self.last_alert_time or \
                       current_time - self.last_alert_time.get(face_key, 0) > self.alert_cooldown:
                        self.last_alert_time[face_key] = current_time
                        self._handle_unknown(frame, x, y, w, h)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.rectangle(frame, (x, y+h+20), (x+w, y+h), color, cv2.FILLED)
                cv2.putText(frame, label_text[:20], (x+4, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
                
            except Exception as e:
                print(f"[ENGINE] Error: {e}")
    
    def _mark_attendance(self, name, role, roll):
        """Mark attendance"""
        if name in self.marked_today:
            return
        
        if database.mark_attendance(name, roll):
            self.marked_today.add(name)
            print(f"[ATTENDANCE] {name} marked present")
    
    def _log_movement(self, name, role):
        """Log entry/exit movement"""
        current_time = time.time()
        
        if name not in self.last_seen:
            self.last_seen[name] = {'time': current_time, 'event': 'entry'}
            database.log_movement(name, role, 'entry')
            print(f"[MOVEMENT] {name} entered")
        else:
            last = self.last_seen[name]
            time_diff = current_time - last['time']
            
            if time_diff > 30 and last['event'] == 'exit':
                database.log_movement(name, role, 'entry')
                self.last_seen[name] = {'time': current_time, 'event': 'entry'}
                print(f"[MOVEMENT] {name} entered")
            elif time_diff > 5 and last['event'] == 'entry':
                self.last_seen[name] = {'time': current_time, 'event': 'entry'}
    
    def _handle_unknown(self, frame, x, y, w, h):
        """Handle unknown person"""
        print("[ALERT] Unknown person detected!")
        
        timestamp = datetime.now()
        expand = 50
        top = max(0, y - expand)
        bottom = min(frame.shape[0], y + h + expand)
        left = max(0, x - expand)
        right = min(frame.shape[1], x + w + expand)
        
        face_image = frame[top:bottom, left:right]
        img_filename = f"unknown_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        img_path = config.UNKNOWN_DIR / img_filename
        cv2.imwrite(str(img_path), face_image, [cv2.IMWRITE_JPEG_QUALITY, 100])
        
        pdf_path = pdf_generator.generate_alert_pdf(str(img_path))
        email_sender.send_unknown_alert(str(img_path), pdf_path)
    
    def _show_frame(self, frame):
        """Display frame"""
        mode_color = (0, 255, 0) if self.mode == "attendance" else (255, 165, 0)
        
        cv2.putText(frame, f"MODE: {self.mode.upper()}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"),
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(frame, f"Registered: {len(self.label_names)} | Marked: {len(self.marked_today)}",
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        
        cv2.imshow("Smart Attendance System", frame)
    
    def get_status(self):
        """Get status"""
        return {
            'running': self.running,
            'mode': self.mode,
            'frames': self.frame_count,
            'registered': len(self.label_names),
            'marked': len(self.marked_today)
        }


_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = AttendanceEngine()
    return _engine
