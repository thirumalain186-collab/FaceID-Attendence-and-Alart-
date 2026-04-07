"""
Attendance Engine for Smart Attendance System v2
GPU-ACCELERATED VERSION with YOLO + DeepSort + Face Recognition
Real-time multi-person tracking with automatic attendance marking
"""

import cv2
import numpy as np
import threading
import time
import hashlib
from datetime import datetime, date
from pathlib import Path
import config
import database
import email_sender
import pdf_generator
from logger import get_logger

logger = get_logger()

# GPU Detection
GPU_CONFIG = {
    'gpu_available': False,
    'use_gpu': False,
    'use_yolo': False,
    'detection_model': 'haar',
    'frame_scale': 0.25,
    'frame_skip': 2,
}

# Check for YOLO + DeepSort availability
# DISABLED - Use Haar cascade for stability
GPU_CONFIG['use_yolo'] = False
GPU_CONFIG['use_gpu'] = False
print("[CPU] YOLO disabled - Using Haar Cascade (more stable)")


class AttendanceEngine:
    """Main attendance system with GPU-accelerated face tracking."""
    
    def __init__(self):
        self.running = False
        self.camera = None
        self.recognizer = None
        self.cascade = None
        self.label_names = {}
        self.person_id_map = {}
        
        # Attendance tracking
        self.marked_today = set()
        self.last_seen = {}
        self.last_alert_time = {}
        self.alert_cooldown = config.ATTENDANCE_CONFIG.get("unknown_alert_cooldown", 60)
        
        self.mode = "idle"
        self.frame_count = 0
        self.face_lock = threading.Lock()
        self.alert_lock = threading.Lock()
        self.movement_lock = threading.Lock()
        
        self._is_demo_mode = False
        self._is_headless = False
        self.demo_timer = 0
        self._last_reset_date = date.today()
        
        # Face tracking
        self._tracked_faces = {}
        
        # GPU components
        self._yolo_model = None
        self._tracker = None
        self._processed_ids = set()  # Track IDs already recognized
        
        # PRELOAD resources
        self.load_resources()
    
    def load_resources(self):
        """Load cascade, model, and face encodings."""
        if GPU_CONFIG['use_yolo']:
            try:
                self._yolo_model = YOLO("yolov8n.pt")
                self._tracker = DeepSort(max_age=30, n_init=2)
                logger.info("YOLO + DeepSort initialized")
            except Exception as e:
                logger.error(f"Failed to load YOLO: {e}")
                GPU_CONFIG['use_yolo'] = False
                GPU_CONFIG['use_gpu'] = False
        
        if not GPU_CONFIG['use_yolo']:
            # Use OpenCV's built-in cascade
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.cascade = cv2.CascadeClassifier(cascade_path)
            logger.info(f"Haar cascade loaded from {cascade_path}")
        
        if config.TRAINER_FILE.exists():
            try:
                import cv2.face as cv2_face
                self.recognizer = cv2_face.LBPHFaceRecognizer_create()
                self.recognizer.read(str(config.TRAINER_FILE))
                logger.info("LBPH model loaded")
            except AttributeError:
                logger.warning("cv2.face not available - using YOLO tracking only")
                self.recognizer = None
            except Exception as e:
                logger.error(f"Failed to load LBPH model: {e}")
                self.recognizer = None
        else:
            logger.warning("Model not trained - using YOLO tracking only")
        
        self.reload_faces()
        logger.info(f"Resources preloaded - {len(self.label_names)} people loaded")
    
    def reload_faces(self):
        """Reload face database."""
        with self.face_lock:
            self.label_names = {}
            self.person_id_map = {}
            
            people = database.get_active_people()
            for person in people:
                person_id = person.get('id')
                name = person.get('name', '')
                role = person.get('role', 'student')
                roll_number = person.get('roll_number') or ''
                
                if not name:
                    continue
                
                safe_name = name.replace(" ", "_").lower()
                
                for folder in config.DATASET_DIR.iterdir():
                    if folder.is_dir() and safe_name in folder.name.lower():
                        label_id = len(self.label_names)
                        self.label_names[label_id] = {
                            'id': person_id,
                            'name': name.lower(),
                            'original_name': name,
                            'role': role.lower(),
                            'roll': roll_number
                        }
                        if person_id:
                            self.person_id_map[person_id] = {
                                'name': name.lower(),
                                'original_name': name
                            }
                        break
            
            logger.info(f"Loaded {len(self.label_names)} registered people")
    
    def start_camera(self, mode="attendance", demo_mode=False, headless=False):
        """Start camera in specified mode."""
        if self.running:
            logger.warning("Camera already running")
            return
        
        self.running = True
        self.mode = mode
        self._is_headless = bool(headless)
        self._is_demo_mode = bool(demo_mode) or self._is_headless
        self.demo_timer = 0
        self._processed_ids.clear()  # Clear processed IDs on start
        
        if not self._is_demo_mode:
            start_time = time.time()
            
            # Camera with CAP_DSHOW for Windows compatibility
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            cam_width = config.ATTENDANCE_CONFIG.get("camera_width", 640)
            cam_height = config.ATTENDANCE_CONFIG.get("camera_height", 480)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.camera.isOpened():
                # Try without CAP_DSHOW
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    logger.error("Cannot open camera - starting in demo mode")
                    self._is_demo_mode = True
            else:
                for _ in range(5):
                    self.camera.read()
                logger.info(f"Camera ready in {time.time() - start_time:.3f}s")
        
        if self._is_headless:
            logger.info(f"HEADLESS mode started - {'YOLO' if GPU_CONFIG['use_yolo'] else 'Haar'}")
        elif self._is_demo_mode:
            logger.info(f"DEMO mode started")
        else:
            logger.info(f"Camera started - {'YOLO GPU' if GPU_CONFIG['use_yolo'] else 'Haar Cascade'}")
        
        thread = threading.Thread(target=self._camera_loop, daemon=True)
        thread.start()
    
    def stop_camera(self):
        """Stop camera."""
        self.running = False
        self.mode = "idle"
        self._processed_ids.clear()
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        
        logger.info("Camera stopped")
    
    def _camera_loop(self):
        """Main camera processing loop."""
        while self.running:
            if self._is_headless:
                self._headless_loop()
                continue
            elif self._is_demo_mode:
                self._demo_loop()
                continue
            
            ret, frame = self.camera.read()
            if not ret or frame is None or frame.size == 0:
                logger.warning("Camera read failed, retrying...")
                time.sleep(0.1)
                continue
            
            self.frame_count += 1
            
            if self.frame_count % GPU_CONFIG['frame_skip'] != 0:
                self._show_frame_safe(frame)
                continue
            
            if GPU_CONFIG['use_yolo']:
                self._process_frame_yolo(frame)
            else:
                self._process_frame_haar(frame)
            
            self._show_frame_safe(frame)
            
            # FPS limiter - prevents CPU overheating
            time.sleep(0.01)  # ~100 FPS max
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_camera()
                break
    
    def _process_frame_yolo(self, frame):
        """GPU-accelerated processing with YOLO + DeepSort."""
        if self._yolo_model is None or self._tracker is None:
            return
        
        current_time = time.time()
        
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        results = self._yolo_model(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            cls = int(box.cls[0])
            if cls == 0:  # Person class in COCO
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                if conf > 0.5:  # Only high confidence
                    detections.append(([x1, y1, x2-x1, y2-y1], conf, 'person'))
        
        tracks = self._tracker.update_tracks(detections, frame=frame)
        
        for track in tracks:
            if not track.is_confirmed():
                continue
            
            track_id = track.track_id
            l, t, w, h = map(int, track.to_ltrb())
            
            # Draw tracking box immediately
            color = (0, 200, 0)  # Green
            cv2.rectangle(frame, (l, t), (l+w, t+h), color, 2)
            cv2.putText(frame, f"ID {track_id}", (l, t-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            
            # Only run face recognition ONCE per person ID
            if track_id not in self._processed_ids:
                face_img = frame[t:t+h, l:l+w]
                if face_img.size > 0:
                    self._recognize_person(face_img, frame, l, t, w, h, 
                                          track_id, current_time, label_names_snapshot)
                    self._processed_ids.add(track_id)
    
    def _recognize_person(self, face_img, frame, x, y, w, h, 
                          track_id, current_time, label_names_snapshot):
        """Recognize a person from tracked region."""
        if self.recognizer is None:
            return
        
        try:
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            face_resized = cv2.resize(gray, (200, 200))
            
            label, confidence = self.recognizer.predict(face_resized)
            lbph_confidence = max(0, 100 - confidence)
            
            if confidence < 80:
                face_info = label_names_snapshot.get(label, {})
                
                if face_info:
                    name = face_info['original_name']
                    role = face_info['role']
                    roll = face_info.get('roll', '')
                    person_id = face_info.get('id')
                    
                    # Draw green box with name
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(frame, f"{name}", (x, y-25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if self.mode == "attendance":
                        self._mark_attendance(name, roll, lbph_confidence, person_id)
                    elif self.mode == "monitoring":
                        self._log_movement(name, role, person_id)
                else:
                    cv2.putText(frame, "Unknown", (x, y-25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
            else:
                cv2.putText(frame, "UNKNOWN", (x, y-25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                with self.alert_lock:
                    face_key = f"yolo_{track_id}"
                    should_alert = (
                        face_key not in self.last_alert_time or
                        current_time - self.last_alert_time.get(face_key, 0) > self.alert_cooldown
                    )
                    if should_alert:
                        self.last_alert_time[face_key] = current_time
                        self._handle_unknown(frame, x, y, w, h)
        
        except Exception as e:
            logger.debug(f"Recognition error: {e}")
    
    def _process_frame_haar(self, frame):
        """CPU fallback processing with Haar cascade."""
        if self.cascade is None:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        scale_factor = 1.1
        min_neighbors = 5
        image_size = (200, 200)
        confidence_threshold = 80
        detect_scale = GPU_CONFIG['frame_scale']
        max_faces = 10
        
        current_time = time.time()
        
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        small_gray = cv2.resize(gray, None, fx=detect_scale, fy=detect_scale)
        scale_w = 1.0 / detect_scale
        scale_h = 1.0 / detect_scale
        
        faces = self.cascade.detectMultiScale(
            small_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(15, 15)
        )
        
        self._tracked_faces = {}
        faces_processed = 0
        
        for (sx, sy, sw, sh) in faces:
            if faces_processed >= max_faces:
                break
            
            x, y, w, h = int(sx * scale_w), int(sy * scale_h), int(sw * scale_w), int(sh * scale_h)
            face_key = self._generate_face_key(x, y, w, h)
            
            recently_seen = face_key in self.last_seen and \
                current_time - self.last_seen[face_key].get('time', 0) < 3
            
            self._tracked_faces[face_key] = {
                'x': x, 'y': y, 'w': w, 'h': h,
                'recognized': recently_seen
            }
            faces_processed += 1
        
        for face_key, face_data in self._tracked_faces.items():
            x, y, w, h = face_data['x'], face_data['y'], face_data['w'], face_data['h']
            
            if not face_data.get('recognized', False):
                self._recognize_haar_face(frame, gray, x, y, w, h, face_key, 
                                        current_time, label_names_snapshot, image_size, confidence_threshold)
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 200, 0), 2)
            
            if face_key in self._tracked_faces and self._tracked_faces[face_key].get('name'):
                name = self._tracked_faces[face_key]['name'][:15]
                cv2.putText(frame, name, (x+4, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    
    def _recognize_haar_face(self, frame, gray, x, y, w, h, face_key,
                            current_time, label_names_snapshot, image_size, confidence_threshold):
        """Recognize face using Haar cascade (CPU fallback)."""
        self.last_seen[face_key] = {'time': current_time}
        
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0:
            return
        
        face_resized = cv2.resize(face_roi, tuple(image_size))
        
        try:
            if self.recognizer is None:
                return
            
            label, confidence = self.recognizer.predict(face_resized)
            lbph_confidence = max(0, 100 - confidence)
            
            if confidence < confidence_threshold:
                face_info = label_names_snapshot.get(label, {})
                
                if face_info:
                    name = face_info['original_name']
                    role = face_info['role']
                    roll = face_info.get('roll', '')
                    person_id = face_info.get('id')
                    
                    self._tracked_faces[face_key]['name'] = f"{name} ({roll or role})"
                    
                    if self.mode == "attendance":
                        self._mark_attendance(name, roll, lbph_confidence, person_id)
                    elif self.mode == "monitoring":
                        self._log_movement(name, role, person_id)
                else:
                    self._tracked_faces[face_key]['name'] = "Unknown"
            else:
                self._tracked_faces[face_key]['name'] = "UNKNOWN"
                
                with self.alert_lock:
                    should_alert = (
                        face_key not in self.last_alert_time or
                        current_time - self.last_alert_time.get(face_key, 0) > self.alert_cooldown
                    )
                    if should_alert:
                        self.last_alert_time[face_key] = current_time
                        self._handle_unknown(frame, x, y, w, h)
        
        except Exception as e:
            logger.debug(f"Recognition error: {e}")
    
    def _generate_face_key(self, x, y, w, h):
        """Generate stable key for face position."""
        hash_input = f"{x//50}_{y//50}_{w//50}_{h//50}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _mark_attendance(self, name, roll, confidence=None, person_id=None):
        """Mark attendance - duplicate prevention."""
        self._check_midnight_reset()
        name_lower = name.lower()
        
        if name_lower in self.marked_today:
            return
        
        if database.mark_attendance(name, roll, confidence=confidence, person_id=person_id):
            self.marked_today.add(name_lower)
            logger.info(f"Attendance marked: {name} (ID: {person_id})")
    
    def _log_movement(self, name, role, person_id=None):
        """Log entry/exit movement."""
        with self.movement_lock:
            current_time = time.time()
            name_lower = name.lower()
            movement_gap = 5
            exit_gap = 30
            
            key = f"mov_{name_lower}"
            
            if key not in self.last_seen:
                self.last_seen[key] = {'time': current_time, 'event': 'entry'}
                database.log_movement(name, role, 'entry', person_id=person_id)
                logger.info(f"{name} entered")
            else:
                last = self.last_seen[key]
                time_diff = current_time - last['time']
                
                if time_diff > exit_gap:
                    if last['event'] == 'exit':
                        self.last_seen[key] = {'time': current_time, 'event': 'entry'}
                        database.log_movement(name, role, 'entry', person_id=person_id)
                    elif last['event'] == 'entry':
                        self.last_seen[key] = {'time': current_time, 'event': 'exit'}
                        database.log_movement(name, role, 'exit', person_id=person_id)
                elif time_diff > movement_gap:
                    self.last_seen[key] = {'time': current_time, 'event': 'entry'}
    
    def _handle_unknown(self, frame, x, y, w, h):
        """Handle unknown person."""
        logger.warning("Unknown person detected!")
        
        timestamp = datetime.now()
        expand = 50
        top = max(0, y - expand)
        bottom = min(frame.shape[0], y + h + expand)
        left = max(0, x - expand)
        right = min(frame.shape[1], x + w + expand)
        
        face_image = frame[top:bottom, left:right]
        img_filename = f"unknown_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        img_path = config.UNKNOWN_DIR / img_filename
        
        try:
            cv2.imwrite(str(img_path), face_image, [cv2.IMWRITE_JPEG_QUALITY, 100])
            pdf_path = pdf_generator.generate_alert_pdf(str(img_path))
            email_sender.send_unknown_alert(str(img_path), pdf_path)
        except Exception as e:
            logger.error(f"Failed to handle unknown: {e}")
    
    def _headless_loop(self):
        """Headless mode."""
        self._check_midnight_reset()
        self.frame_count += 1
        self.demo_timer += 1
        
        if self.demo_timer % 10 == 0:
            with self.face_lock:
                label_count = len(self.label_names)
            logger.info(f"Headless: {self.mode} - Frame: {self.frame_count}, Registered: {label_count}, Marked: {len(self.marked_today)}")
            
            if self.mode == "attendance" and label_count > 0:
                self._auto_mark_attendance()
        
        time.sleep(1)
    
    def _demo_loop(self):
        """Demo mode."""
        try:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "DEMO MODE", (200, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Mode: {self.mode.upper()}", (230, 230),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"), (200, 270),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            with self.face_lock:
                label_count = len(self.label_names)
            cv2.putText(frame, f"Registered: {label_count} | Marked: {len(self.marked_today)}", (170, 310),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            
            self.frame_count += 1
            self.demo_timer += 1
            
            if self.mode == "attendance" and self.demo_timer % 60 == 0 and label_count > 0:
                marked = self._auto_mark_attendance()
                for i, name in enumerate(marked[:5]):
                    cv2.putText(frame, f"[AUTO] {name}", (150, 380 + i * 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            self._show_frame_safe(frame)
            time.sleep(0.033)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_camera()
        except Exception as e:
            logger.warning(f"GUI not available: {e}")
            self._is_headless = True
    
    def _auto_mark_attendance(self):
        """Mark all unmarked people in demo mode."""
        marked = []
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        for label_id, info in label_names_snapshot.items():
            name_lower = info['original_name'].lower()
            if name_lower not in self.marked_today:
                person_id = info.get('id')
                success = database.mark_attendance(
                    info['original_name'], 
                    info.get('roll', ''),
                    person_id=person_id
                )
                if success:
                    self.marked_today.add(name_lower)
                    marked.append(info['original_name'])
                    logger.info(f"Marked (auto): {info['original_name']}")
        return marked
    
    def _check_midnight_reset(self):
        """Reset tracking at midnight."""
        today = date.today()
        if today > self._last_reset_date:
            self.marked_today.clear()
            self.last_seen.clear()
            self.last_alert_time.clear()
            self._processed_ids.clear()
            self._last_reset_date = today
            logger.info("Midnight reset")
    
    def _show_frame_safe(self, frame):
        """Display frame with status."""
        mode_color = (0, 255, 0) if self.mode == "attendance" else (255, 165, 0)
        
        cv2.putText(frame, f"MODE: {self.mode.upper()}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"),
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        with self.face_lock:
            label_count = len(self.label_names)
        cv2.putText(frame, f"Registered: {label_count} | Marked: {len(self.marked_today)}",
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        
        # Show engine type
        engine = "YOLO GPU" if GPU_CONFIG['use_yolo'] else "Haar CPU"
        cv2.putText(frame, engine, (10, frame.shape[0]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        try:
            if not self._is_headless:
                cv2.imshow("Smart Attendance System", frame)
        except Exception as e:
            logger.debug(f"Cannot display: {e}")
    
    def get_status(self):
        """Get status."""
        with self.face_lock:
            registered = len(self.label_names)
        return {
            'running': self.running,
            'mode': self.mode,
            'frames': self.frame_count,
            'registered': registered,
            'marked': len(self.marked_today),
            'headless': self._is_headless,
            'demo_mode': self._is_demo_mode,
            'engine': 'yolo' if GPU_CONFIG['use_yolo'] else 'haar'
        }


_engine = None
_engine_lock = threading.Lock()


def get_engine():
    """Get global engine instance."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = AttendanceEngine()
    return _engine
