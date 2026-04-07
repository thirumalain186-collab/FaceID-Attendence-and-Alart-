"""
Attendance Engine for Smart Attendance System v2
Face recognition, camera control, and attendance marking
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
    """Main attendance system with camera control."""
    
    def __init__(self):
        self.running = False
        self.camera = None
        self.recognizer = None
        self.cascade = None
        self.label_names = {}
        self.person_id_map = {}
        
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
        
        # Performance optimization: face tracking
        self._tracked_faces = {}  # {face_key: {'x':, 'y':, 'w':, 'h':, 'last_seen': frame_num}}
        self._process_detection = True  # Toggle between detection and tracking frames
        
        self.load_resources()
    
    def load_resources(self):
        """Load cascade and model."""
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
            logger.warning("Model not trained")
        
        self.reload_faces()
    
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
    
    def remove_person_safe(self, name):
        """Remove person without stopping camera."""
        database.remove_person(name)
        self.reload_faces()
        
        safe_name = name.replace(" ", "_").lower()
        for folder in config.DATASET_DIR.iterdir():
            if folder.is_dir() and safe_name in folder.name.lower():
                try:
                    import shutil
                    shutil.rmtree(folder, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Could not remove folder: {e}")
                break
        
        logger.info(f"Removed {name} from system")
    
    def start_camera(self, mode="attendance", demo_mode=False, headless=False):
        """Start camera in specified mode.
        
        Args:
            mode: "attendance" or "monitoring"
            demo_mode: Show GUI window (False = real camera, True = demo window)
            headless: No GUI at all (True forces headless regardless of demo_mode)
        """
        if self.running:
            logger.warning("Camera already running")
            return
        
        self.running = True
        self.mode = mode
        self._is_headless = bool(headless)
        self._is_demo_mode = bool(demo_mode) or self._is_headless
        self.demo_timer = 0
        
        if not self._is_demo_mode:
            self.camera = cv2.VideoCapture(config.ATTENDANCE_CONFIG.get("camera_index", 0))
            
            # Performance: Set camera resolution once at startup
            cam_width = config.ATTENDANCE_CONFIG.get("camera_width", 640)
            cam_height = config.ATTENDANCE_CONFIG.get("camera_height", 480)
            self.camera.set(3, cam_width)  # Width
            self.camera.set(4, cam_height)  # Height
            
            if not self.camera.isOpened():
                logger.error("Cannot open camera - starting in demo mode")
                self._is_demo_mode = True
        
        if self._is_headless:
            logger.info(f"HEADLESS mode started in {mode} mode (no display)")
        elif self._is_demo_mode:
            logger.info(f"DEMO mode started in {mode} mode (no camera)")
        else:
            logger.info(f"Camera started in {mode} mode")
        
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
        """Main camera processing loop."""
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
            
            frame_skip = config.ATTENDANCE_CONFIG.get("frame_skip", 3)
            if self.frame_count % frame_skip != 0:
                self._show_frame_safe(frame)
                continue
            
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
        """Mark all unmarked people in demo/headless mode. Returns list of names marked."""
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
        """Process single frame with thread safety and optimizations."""
        if self.cascade is None:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        scale_factor = config.ATTENDANCE_CONFIG.get("scale_factor", 1.1)
        min_neighbors = config.ATTENDANCE_CONFIG.get("min_neighbors", 5)
        min_face_size = config.ATTENDANCE_CONFIG.get("min_face_size", (30, 30))
        image_size = config.ATTENDANCE_CONFIG.get("image_size", (200, 200))
        confidence_threshold = config.ATTENDANCE_CONFIG.get("confidence_threshold", 80)
        detect_scale = config.ATTENDANCE_CONFIG.get("detect_scale_factor", 0.5)
        enable_tracking = config.ATTENDANCE_CONFIG.get("track_faces", True)
        process_nth = config.ATTENDANCE_CONFIG.get("process_every_nth", 3)
        
        current_time = time.time()
        
        # Toggle between detection and tracking frames
        should_detect = (self.frame_count % process_nth == 0)
        
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        if should_detect:
            # OPTIMIZATION: Detect on scaled-down image for speed
            if detect_scale < 1.0:
                small_gray = cv2.resize(gray, None, fx=detect_scale, fy=detect_scale)
                scale_w = 1.0 / detect_scale
                scale_h = 1.0 / detect_scale
            else:
                small_gray = gray
                scale_w = 1.0
                scale_h = 1.0
            
            faces = self.cascade.detectMultiScale(
                small_gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=(min_face_size[0] // 2, min_face_size[1] // 2)
            )
            
            # Update tracked faces with new detections
            self._tracked_faces = {}
            for (sx, sy, sw, sh) in faces:
                # Scale coordinates back to original frame
                x, y, w, h = int(sx * scale_w), int(sy * scale_h), int(sw * scale_w), int(sh * scale_h)
                face_key = self._generate_face_key(x, y, w, h)
                self._tracked_faces[face_key] = {
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'last_seen': self.frame_count,
                    'recognized': False
                }
        
        # Process tracked faces (from detection or previous tracking)
        faces_to_process = []
        if enable_tracking and not should_detect:
            # Between detection frames, use tracked positions
            faces_to_process = [
                (f['x'], f['y'], f['w'], f['h'])
                for f in self._tracked_faces.values()
            ]
        else:
            faces_to_process = [
                (f['x'], f['y'], f['w'], f['h'])
                for f in self._tracked_faces.values()
            ]
        
        for (x, y, w, h) in faces_to_process:
            face_key = self._generate_face_key(x, y, w, h)
            
            if face_key in self.last_seen and current_time - self.last_seen[face_key].get('time', 0) < 2:
                continue
            
            self.last_seen[face_key] = {'time': current_time}
            
            face_roi = gray[y:y+h, x:x+w]
            if face_roi.size == 0:
                continue
            face_resized = cv2.resize(face_roi, tuple(image_size))
            
            try:
                if self.recognizer is None:
                    label_text = "Model not loaded"
                    color = (100, 100, 100)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, label_text[:20], (x+4, y+h+15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
                    continue
                
                label, confidence = self.recognizer.predict(face_resized)
                
                lbph_confidence = max(0, 100 - confidence)
                
                if confidence < confidence_threshold:
                    face_info = label_names_snapshot.get(label, {})
                    
                    if face_info:
                        name = face_info['original_name']
                        role = face_info['role']
                        roll = face_info.get('roll', '')
                        person_id = face_info.get('id')
                        
                        label_text = f"{name} ({roll or role})"
                        color = (0, 200, 0) if role == 'student' else (200, 150, 0)
                        
                        if self.mode == "attendance":
                            self._mark_attendance(name, role, roll, lbph_confidence, person_id)
                        elif self.mode == "monitoring":
                            self._log_movement(name, role, person_id)
                    else:
                        label_text = "Unknown"
                        color = (100, 100, 100)
                else:
                    label_text = "UNKNOWN"
                    color = (0, 0, 220)
                    
                    with self.alert_lock:
                        should_alert = (
                            face_key not in self.last_alert_time or
                            current_time - self.last_alert_time.get(face_key, 0) > self.alert_cooldown
                        )
                        if should_alert:
                            self.last_alert_time[face_key] = current_time
                    
                    if should_alert:
                        self._handle_unknown(frame, x, y, w, h)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.rectangle(frame, (x, y+h+20), (x+w, y+h), color, cv2.FILLED)
                cv2.putText(frame, label_text[:20], (x+4, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
                
            except Exception as e:
                logger.debug(f"Error processing face: {e}")
    
    def _generate_face_key(self, x, y, w, h):
        """Generate stable key for face position (without timestamp)."""
        hash_input = f"{x//10}_{y//10}_{w//10}_{h//10}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _mark_attendance(self, name, role, roll, confidence=None, person_id=None):
        """Mark attendance - thread safe."""
        self._check_midnight_reset()
        name_lower = name.lower()
        
        if name_lower in self.marked_today:
            return
        
        if database.mark_attendance(name, roll, confidence=confidence, person_id=person_id):
            self.marked_today.add(name_lower)
            logger.info(f"Attendance marked: {name} (ID: {person_id})")
    
    def _log_movement(self, name, role, person_id=None):
        """Log entry/exit movement - thread safe."""
        with self.movement_lock:
            current_time = time.time()
            name_lower = name.lower()
            movement_gap = config.ATTENDANCE_CONFIG.get("movement_gap_seconds", 5)
            exit_gap = 30
            
            key = f"mov_{name_lower}"
            
            if key not in self.last_seen:
                self.last_seen[key] = {'time': current_time, 'event': 'entry'}
                database.log_movement(name, role, 'entry', person_id=person_id)
                logger.info(f"{name} entered (ID: {person_id})")
            else:
                last = self.last_seen[key]
                time_diff = current_time - last['time']
                
                if time_diff > exit_gap:
                    if last['event'] == 'exit':
                        self.last_seen[key] = {'time': current_time, 'event': 'entry'}
                        database.log_movement(name, role, 'entry', person_id=person_id)
                        logger.info(f"{name} entered (ID: {person_id})")
                    elif last['event'] == 'entry':
                        self.last_seen[key] = {'time': current_time, 'event': 'exit'}
                        database.log_movement(name, role, 'exit', person_id=person_id)
                        logger.info(f"{name} exited (ID: {person_id})")
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
            
            pdf_path = None
            try:
                pdf_path = pdf_generator.generate_alert_pdf(str(img_path))
            except Exception as e:
                logger.warning(f"Failed to generate alert PDF: {e}")
            
            email_sender.send_unknown_alert(str(img_path), pdf_path)
        except Exception as e:
            logger.error(f"Failed to handle unknown person: {e}")
    
    def _show_frame_safe(self, frame):
        """Display frame with error handling."""
        mode_color = (0, 255, 0) if self.mode == "attendance" else (255, 165, 0)
        
        cv2.putText(frame, f"MODE: {self.mode.upper()}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"),
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        with self.face_lock:
            label_count = len(self.label_names)
        cv2.putText(frame, f"Registered: {label_count} | Marked: {len(self.marked_today)}",
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        
        try:
            if not self._is_headless:
                cv2.imshow("Smart Attendance System", frame)
        except Exception as e:
            logger.debug(f"Cannot display frame: {e}")
    
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
    """Get the global engine instance, thread-safe."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = AttendanceEngine()
    return _engine
