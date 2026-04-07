"""
Attendance Engine for Smart Attendance System v2
OPTIMIZED VERSION: Real-time, Multi-Face, Fast Performance
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


class AttendanceEngine:
    """Main attendance system with camera control - OPTIMIZED."""
    
    def __init__(self):
        self.running = False
        self.camera = None
        self.recognizer = None
        self.cascade = None
        self.label_names = {}
        self.person_id_map = {}
        
        # Attendance tracking - prevents duplicate marking
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
        
        # Performance optimization: face tracking between frames
        self._tracked_faces = {}
        
        # PRELOAD resources BEFORE camera starts
        self.load_resources()
    
    def load_resources(self):
        """Load cascade, model, and face encodings - called BEFORE camera starts."""
        if config.HAAR_CASCADE_PATH.exists():
            self.cascade = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
            logger.info("Haar cascade loaded")
        else:
            logger.error("Haar cascade not found")
        
        if config.TRAINER_FILE.exists():
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(str(config.TRAINER_FILE))
                logger.info("LBPH model loaded")
            except Exception as e:
                logger.error(f"Failed to load LBPH model: {e}")
                self.recognizer = None
        else:
            logger.warning("Model not trained - run train.py first")
        
        # PRELOAD face database
        self.reload_faces()
        logger.info(f"Resources preloaded - {len(self.label_names)} people loaded")
    
    def reload_faces(self):
        """Reload face database - thread safe."""
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
        """Start camera in specified mode - OPTIMIZED for instant start."""
        if self.running:
            logger.warning("Camera already running")
            return
        
        self.running = True
        self.mode = mode
        self._is_headless = bool(headless)
        self._is_demo_mode = bool(demo_mode) or self._is_headless
        self.demo_timer = 0
        
        if not self._is_demo_mode:
            start_time = time.time()
            
            # FAST camera initialization
            self.camera = cv2.VideoCapture(config.ATTENDANCE_CONFIG.get("camera_index", 0))
            
            # Set resolution FIRST (before reading)
            cam_width = config.ATTENDANCE_CONFIG.get("camera_width", 640)
            cam_height = config.ATTENDANCE_CONFIG.get("camera_height", 480)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Min buffer = faster
            
            if not self.camera.isOpened():
                logger.error("Cannot open camera - starting in demo mode")
                self._is_demo_mode = True
            else:
                # CAMERA WARMUP: Discard first 5 frames for stable capture
                for _ in range(5):
                    self.camera.read()
                
                logger.info(f"Camera ready in {time.time() - start_time:.3f}s")
        
        if self._is_headless:
            logger.info(f"HEADLESS mode started in {mode} mode")
        elif self._is_demo_mode:
            logger.info(f"DEMO mode started in {mode} mode")
        else:
            logger.info(f"Camera started in {mode} mode")
        
        # Start processing in background thread
        thread = threading.Thread(target=self._camera_loop, daemon=True)
        thread.start()
    
    def stop_camera(self):
        """Stop camera."""
        self.running = False
        self.mode = "idle"
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        
        logger.info("Camera stopped")
    
    def _camera_loop(self):
        """Main camera processing loop - SUPER OPTIMIZED."""
        while self.running:
            if self._is_headless:
                self._headless_loop()
                continue
            elif self._is_demo_mode:
                self._demo_loop()
                continue
            
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Camera read failed")
                break
            
            self.frame_count += 1
            
            # SUPER AGGRESSIVE FRAME SKIPPING: Process every 2nd frame only
            process_this_frame = self.frame_count % 2 == 0
            if not process_this_frame:
                self._show_frame_safe(frame)
                continue
            
            # Process frame with face detection
            self._process_frame(frame)
            self._show_frame_safe(frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_camera()
                break
    
    def _headless_loop(self):
        """Headless mode - no display, for server environments."""
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
        """Demo mode - shows placeholder window."""
        try:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "DEMO MODE - No Camera Connected", (120, 180),
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
                    cv2.putText(frame, f"[AUTO] Marked: {name}", (150, 380 + i * 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            self._show_frame_safe(frame)
            time.sleep(0.033)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_camera()
        except Exception as e:
            logger.warning(f"GUI not available, switching to headless: {e}")
            self._is_headless = True
    
    def _auto_mark_attendance(self):
        """Mark all unmarked people in demo/headless mode."""
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
                    logger.info(f"Attendance marked (auto): {info['original_name']} (ID: {person_id})")
        return marked
    
    def _check_midnight_reset(self):
        """Reset marked_today at midnight."""
        today = date.today()
        if today > self._last_reset_date:
            self.marked_today.clear()
            self.last_seen.clear()
            self.last_alert_time.clear()
            self._last_reset_date = today
            logger.info("Midnight reset - cleared attendance tracking")
    
    def _process_frame(self, frame):
        """Process frame - OPTIMIZED for real-time multi-face detection.
        
        KEY OPTIMIZATIONS:
        1. Resize to 25% for detection (16x faster)
        2. Limit max faces per frame (10)
        3. Skip recently recognized faces
        4. Track faces between frames
        """
        if self.cascade is None:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Configuration
        scale_factor = 1.1
        min_neighbors = 5
        image_size = (200, 200)
        confidence_threshold = 80
        detect_scale = 0.25  # 25% size = 16x faster detection
        max_faces = 10  # Limit to prevent overload
        
        current_time = time.time()
        
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        # RESIZE to 25% for detection
        small_gray = cv2.resize(gray, None, fx=detect_scale, fy=detect_scale)
        scale_w = 1.0 / detect_scale
        scale_h = 1.0 / detect_scale
        
        # Detect faces on small image
        faces = self.cascade.detectMultiScale(
            small_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(15, 15)  # Smaller min size for distant faces
        )
        
        # Update tracked faces
        self._tracked_faces = {}
        faces_processed = 0
        
        # Limit faces to prevent CPU overload
        for (sx, sy, sw, sh) in faces:
            if faces_processed >= max_faces:
                break
            
            # Scale back to original size
            x, y, w, h = int(sx * scale_w), int(sy * scale_h), int(sw * scale_w), int(sh * scale_h)
            face_key = self._generate_face_key(x, y, w, h)
            
            # Skip if recently recognized (3 second cooldown)
            recently_seen = face_key in self.last_seen and \
                current_time - self.last_seen[face_key].get('time', 0) < 3
            
            self._tracked_faces[face_key] = {
                'x': x, 'y': y, 'w': w, 'h': h,
                'recognized': recently_seen
            }
            faces_processed += 1
        
        # Process all tracked faces
        for face_key, face_data in self._tracked_faces.items():
            x, y, w, h = face_data['x'], face_data['y'], face_data['w'], face_data['h']
            
            # Only do recognition if not recently seen
            if not face_data.get('recognized', False):
                self._recognize_face(frame, gray, x, y, w, h, face_key, 
                                    current_time, label_names_snapshot, image_size, confidence_threshold)
            
            # Draw box immediately for all faces
            color = (0, 200, 0)  # Green
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.rectangle(frame, (x, y+h+20), (x+w, y+h), color, cv2.FILLED)
            
            # Show name if recognized
            if face_key in self._tracked_faces and self._tracked_faces[face_key].get('name'):
                name = self._tracked_faces[face_key]['name'][:15]
                cv2.putText(frame, name, (x+4, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    
    def _recognize_face(self, frame, gray, x, y, w, h, face_key, 
                        current_time, label_names_snapshot, image_size, confidence_threshold):
        """Recognize a single face - optimized."""
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
                    
                    # Store name for display
                    self._tracked_faces[face_key]['name'] = f"{name} ({roll or role})"
                    
                    # Mark attendance (duplicate check included)
                    if self.mode == "attendance":
                        self._mark_attendance(name, roll, lbph_confidence, person_id)
                    elif self.mode == "monitoring":
                        self._log_movement(name, role, person_id)
                else:
                    self._tracked_faces[face_key]['name'] = "Unknown"
            else:
                self._tracked_faces[face_key]['name'] = "UNKNOWN"
                
                # Alert for unknown faces
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
        """Generate stable key for face position - groups nearby detections."""
        hash_input = f"{x//50}_{y//50}_{w//50}_{h//50}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _mark_attendance(self, name, roll, confidence=None, person_id=None):
        """Mark attendance - DUPLICATE PREVENTION included."""
        self._check_midnight_reset()
        name_lower = name.lower()
        
        # DUPLICATE CHECK: Already marked today?
        if name_lower in self.marked_today:
            return
        
        # Mark in database
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
        """Handle unknown person - save photo and alert."""
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
    
    def _show_frame_safe(self, frame):
        """Display frame with status overlay."""
        mode_color = (0, 255, 0) if self.mode == "attendance" else (255, 165, 0)
        
        cv2.putText(frame, f"MODE: {self.mode.upper()}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"),
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        with self.face_lock:
            label_count = len(self.label_names)
        cv2.putText(frame, f"Registered: {label_count} | Marked: {len(self.marked_today)}",
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        
        # Show FPS indicator
        cv2.putText(frame, "REAL-TIME OPTIMIZED", (10, frame.shape[0]-10),
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
            'demo_mode': self._is_demo_mode
        }


_engine = None
_engine_lock = threading.Lock()


def get_engine():
    """Get the global engine instance - thread-safe singleton."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = AttendanceEngine()
    return _engine
