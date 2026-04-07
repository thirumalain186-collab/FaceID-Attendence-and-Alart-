"""
Attendance Engine v3 - PRODUCTION READY
======================================
- Direct frame processing (NO temp files)
- Smart face cache for speed
- Stable Haar cascade detection
- Optimized for Electron + Flask
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
from logger import get_logger

logger = get_logger()

GPU_CONFIG = {
    'use_yolo': False,
    'use_gpu': False,
    'frame_scale': 0.25,
    'frame_skip': 2,
}

print("[PRODUCTION] Attendance Engine v3 loaded")


class AttendanceEngine:
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
        self.alert_cooldown = 60
        
        self.mode = "idle"
        self.frame_count = 0
        self.face_lock = threading.Lock()
        self.alert_lock = threading.Lock()
        self.movement_lock = threading.Lock()
        
        self._is_demo_mode = False
        self._is_headless = False
        self.demo_timer = 0
        self._last_reset_date = date.today()
        self._tracked_faces = {}
        self._processed_ids = set()
        
        self._face_cache = {}
        self._face_cache_max = 1000
        self._unknown_count = 0
        
        self.load_resources()
    
    def load_resources(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        logger.info(f"Haar cascade loaded: {cascade_path}")
        
        if config.TRAINER_FILE.exists():
            try:
                import cv2.face as cv2_face
                self.recognizer = cv2_face.LBPHFaceRecognizer_create()
                self.recognizer.read(str(config.TRAINER_FILE))
                logger.info("LBPH model loaded")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.recognizer = None
        else:
            logger.warning("Model not trained")
        
        self.reload_faces()
        logger.info(f"Resources loaded - {len(self.label_names)} people")
    
    def _best_match(self, folder_name, person_map):
        """Find best matching person - MUST match train.py logic."""
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
    
    def reload_faces(self):
        with self.face_lock:
            self.label_names = {}
            self.person_id_map = {}
            
            # Build person map (same as train.py)
            person_map = {}
            for person in database.get_active_people():
                name = person.get('name', '')
                if not name:
                    continue
                safe_name = name.replace(" ", "_").lower()
                person_map[safe_name] = {
                    'id': person.get('id'),
                    'name': name,
                    'role': person.get('role', 'student').lower(),
                    'roll': person.get('roll_number') or ''
                }
            
            # Iterate sorted folders (MUST match training order)
            for folder in sorted(config.DATASET_DIR.iterdir()):
                if not folder.is_dir():
                    continue
                
                matched = self._best_match(folder.name, person_map)
                if not matched:
                    continue
                
                label_id = len(self.label_names)
                self.label_names[label_id] = {
                    'id': matched['id'],
                    'name': matched['name'].lower(),
                    'original_name': matched['name'],
                    'role': matched['role'],
                    'roll': matched['roll']
                }
                if matched['id']:
                    self.person_id_map[matched['id']] = {'name': matched['name'].lower()}
            
            names = [v['original_name'] for v in self.label_names.values()]
            logger.info(f"Loaded {len(self.label_names)} people: {names}")
    
    def start_camera(self, mode="attendance", demo_mode=False, headless=False):
        if self.running:
            return
        
        self.running = True
        self.mode = mode
        self._is_headless = bool(headless)
        self._is_demo_mode = bool(demo_mode) or self._is_headless
        self.demo_timer = 0
        self._processed_ids.clear()
        self._face_cache.clear()
        
        if not self._is_demo_mode:
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not self.camera.isOpened():
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    logger.error("Camera failed - demo mode")
                    self._is_demo_mode = True
            else:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                for _ in range(5):
                    self.camera.read()
                logger.info("Camera ready")
        
        mode_str = "HEADLESS" if self._is_headless else "DEMO" if self._is_demo_mode else "LIVE"
        logger.info(f"Started: {mode_str} mode")
        
        thread = threading.Thread(target=self._camera_loop, daemon=True)
        thread.start()
    
    def stop_camera(self):
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
        while self.running:
            if self._is_headless:
                self._headless_loop()
                continue
            elif self._is_demo_mode:
                self._demo_loop()
                continue
            
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            self.frame_count += 1
            
            if self.frame_count % GPU_CONFIG['frame_skip'] != 0:
                self._show_frame(frame)
                continue
            
            self._process_frame(frame)
            self._show_frame(frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_camera()
                break
    
    def _process_frame(self, frame):
        if self.cascade is None:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_time = time.time()
        
        with self.face_lock:
            label_names_snapshot = dict(self.label_names)
        
        # Detect on full-size gray for better accuracy
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        # Debug: Print face count every 30 frames
        if self.frame_count % 30 == 0:
            print(f"[DEBUG] Faces detected: {len(faces)}")
        
        self._tracked_faces = {}
        
        for (sx, sy, sw, sh) in faces[:10]:
            x, y, w, h = sx, sy, sw, sh
            
            face_key = self._generate_face_key(x, y, w, h)
            recently_seen = face_key in self.last_seen and \
                           current_time - self.last_seen[face_key].get('time', 0) < 3
            
            self._tracked_faces[face_key] = {
                'x': x, 'y': y, 'w': w, 'h': h,
                'recognized': recently_seen
            }
        
        for face_key, face_data in self._tracked_faces.items():
            x, y, w, h = face_data['x'], face_data['y'], face_data['w'], face_data['h']
            
            if not face_data.get('recognized', False):
                self._recognize_face(frame, gray, x, y, w, h, face_key, 
                                    current_time, label_names_snapshot)
            
            color = (0, 200, 0)
            if face_key in self._tracked_faces and self._tracked_faces[face_key].get('name'):
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, face_data['name'][:15], (x+4, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
    
    def _recognize_face(self, frame, gray, x, y, w, h, face_key,
                        current_time, label_names_snapshot):
        self.last_seen[face_key] = {'time': current_time}
        
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0:
            return
        
        face_resized = cv2.resize(face_roi, (200, 200))
        face_hash = hash(face_resized.tobytes()) % 10000
        
        if face_hash in self._face_cache:
            label, confidence = self._face_cache[face_hash]
        else:
            if self.recognizer is None:
                return
            try:
                label, confidence = self.recognizer.predict(face_resized)
                
                # Debug output
                if self.frame_count % 30 == 0:
                    face_info = label_names_snapshot.get(label, {})
                    name = face_info.get('original_name', 'Unknown') if face_info else 'Unknown'
                    print(f"[RECOG] Label={label}, Conf={confidence:.1f}, Name={name}")
                
                if len(self._face_cache) < self._face_cache_max:
                    self._face_cache[face_hash] = (label, confidence)
            except Exception as e:
                print(f"[ERROR] Recognition failed: {e}")
                return
        
        lbph_confidence = max(0, 100 - confidence)
        
        if confidence < 80:
            face_info = label_names_snapshot.get(label, {})
            
            if face_info:
                name = face_info['original_name']
                role = face_info['role']
                roll = face_info.get('roll', '')
                person_id = face_info.get('id')
                
                self._tracked_faces[face_key]['name'] = f"{name}"
                
                if self.mode == "attendance":
                    self._mark_attendance(name, roll, lbph_confidence, person_id)
                elif self.mode == "monitoring":
                    self._log_movement(name, role, person_id)
            else:
                self._tracked_faces[face_key]['name'] = "Unknown"
        else:
            self._tracked_faces[face_key]['name'] = "UNKNOWN"
    
    def _generate_face_key(self, x, y, w, h):
        hash_input = f"{x//50}_{y//50}_{w//50}_{h//50}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _mark_attendance(self, name, roll, confidence=None, person_id=None):
        self._check_midnight_reset()
        name_lower = name.lower()
        
        if name_lower in self.marked_today:
            return
        
        if database.mark_attendance(name, roll, confidence=confidence, person_id=person_id):
            self.marked_today.add(name_lower)
            logger.info(f"Attendance: {name}")
    
    def _log_movement(self, name, role, person_id=None):
        with self.movement_lock:
            current_time = time.time()
            name_lower = name.lower()
            key = f"mov_{name_lower}"
            
            if key not in self.last_seen or current_time - self.last_seen.get(key, {}).get('time', 0) > 30:
                database.log_movement(name, role, 'entry', person_id=person_id)
                self.last_seen[key] = {'time': current_time}
                logger.info(f"{name} entered")
    
    def _headless_loop(self):
        self._check_midnight_reset()
        self.frame_count += 1
        
        if self.frame_count % 10 == 0:
            with self.face_lock:
                label_count = len(self.label_names)
            logger.info(f"Headless: {self.mode} | Frames: {self.frame_count} | Registered: {label_count}")
            
            if self.mode == "attendance" and label_count > 0:
                self._auto_mark()
        
        time.sleep(1)
    
    def _demo_loop(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "DEMO MODE", (200, 180),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Mode: {self.mode.upper()}", (230, 230),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"), (200, 270),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        self.frame_count += 1
        self._show_frame(frame)
        time.sleep(0.033)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.stop_camera()
    
    def _auto_mark(self):
        marked = []
        with self.face_lock:
            for label_id, info in self.label_names.items():
                name_lower = info['original_name'].lower()
                if name_lower not in self.marked_today:
                    if database.mark_attendance(info['original_name'], info.get('roll', '')):
                        self.marked_today.add(name_lower)
                        marked.append(info['original_name'])
        return marked
    
    def _check_midnight_reset(self):
        today = date.today()
        if today > self._last_reset_date:
            self.marked_today.clear()
            self.last_seen.clear()
            self.last_alert_time.clear()
            self._processed_ids.clear()
            self._last_reset_date = today
            logger.info("Midnight reset")
    
    def _show_frame(self, frame):
        cv2.putText(frame, f"MODE: {self.mode.upper()}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, datetime.now().strftime("%d %b %Y %H:%M:%S"),
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        with self.face_lock:
            label_count = len(self.label_names)
        cv2.putText(frame, f"Registered: {label_count} | Marked: {len(self.marked_today)}",
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        
        try:
            if not self._is_headless and not self._is_demo_mode:
                cv2.imshow("Smart Attendance System", frame)
        except Exception:
            pass
    
    def get_status(self):
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
            'engine': 'haar',
            'cache_size': len(self._face_cache)
        }


_engine = None
_engine_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = AttendanceEngine()
    return _engine
