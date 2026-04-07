"""
Enhanced Monitoring Mode with Unknown Face Detection and Email Alerts
Sends alerts to Class Advisor and HOD when unknown persons are detected
"""

import cv2
import numpy as np
import threading
import time
import sqlite3
from datetime import datetime, date
from pathlib import Path
import sys

import config
import database
import email_sender
from attendance_engine import AttendanceEngine
from logger import get_logger

logger = get_logger()


class MonitoringEngine:
    """
    Enhanced monitoring engine that:
    - Detects all faces (registered and unknown)
    - Marks attendance for registered students
    - Sends email alerts for unknown persons
    - Logs all movements
    """
    
    def __init__(self):
        self.engine = AttendanceEngine()
        self.unknown_faces = {}  # Store unknown face detections
        self.alert_sent = {}  # Track which unknown faces had alerts sent
        self.alert_cooldown = 60  # Seconds between alerts for same unknown face
        self.capture_unknown_photos = True
        
    def load_resources(self):
        """Load all required resources"""
        logger.info("Loading monitoring engine resources...")
        if not self.engine.load_resources():
            logger.error("Failed to load resources")
            return False
        
        logger.info(f"Engine loaded with {len(self.engine.label_map)} registered students")
        return True
    
    def capture_and_save_unknown_face(self, frame, face_box, confidence):
        """Save unknown face photo for investigation"""
        try:
            x, y, w, h = face_box
            face_roi = frame[y:y+h, x:x+w]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_id = np.random.randint(1000, 9999)
            filename = f"unknown_{timestamp}_{random_id}.jpg"
            filepath = config.UNKNOWN_DIR / filename
            
            cv2.imwrite(str(filepath), face_roi)
            logger.info(f"Saved unknown face: {filepath}")
            
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save unknown face: {e}")
            return None
    
    def send_alert_for_unknown_face(self, face_photo_path, face_count, confidence):
        """Send email alert to class advisor and HOD"""
        try:
            # Build alert message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            class_name = config.ATTENDANCE_CONFIG.get("class_name", "Unknown Class")
            
            logger.warning(f"UNKNOWN PERSON DETECTED - {timestamp}")
            logger.warning(f"  Photo saved: {face_photo_path}")
            logger.warning(f"  Confidence: {confidence:.2f}")
            logger.warning(f"  Class: {class_name}")
            
            # Send email alert
            email_sender.send_unknown_alert(face_photo_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def process_unknown_faces(self, frame, faces):
        """
        Process unregistered/unknown faces detected in frame
        """
        current_time = time.time()
        
        for (x, y, w, h) in faces:
            # Create a simple face ID based on position
            face_id = f"{x//50}_{y//50}_{w//50}_{h//50}"
            
            # Check if we should send alert for this unknown face
            if face_id not in self.alert_sent:
                # This is a new unknown face - send alert
                
                # Save photo
                photo_path = self.capture_and_save_unknown_face(frame, (x, y, w, h), 0)
                
                # Send alert
                if photo_path:
                    self.send_alert_for_unknown_face(photo_path, len(faces), 0)
                
                # Mark that we sent alert for this face
                self.alert_sent[face_id] = current_time
                
                # Log to database
                try:
                    database.log_movement("Unknown Person", "visitor", None)
                    logger.info("Unknown person movement logged")
                except Exception as e:
                    logger.error(f"Failed to log unknown movement: {e}")
            
            # Check cooldown - allow multiple alerts if person stays too long
            elif current_time - self.alert_sent.get(face_id, 0) > self.alert_cooldown:
                # Re-send alert if same unknown face is still there after cooldown
                photo_path = self.capture_and_save_unknown_face(frame, (x, y, w, h), 0)
                if photo_path:
                    self.send_alert_for_unknown_face(photo_path, len(faces), 0)
                self.alert_sent[face_id] = current_time
    
    def start_monitoring(self, duration=None):
        """
        Start monitoring mode:
        - Detect all faces
        - Mark attendance for known students
        - Send alerts for unknown persons
        - Log all movements
        """
        logger.info("="*70)
        logger.info("MONITORING MODE STARTED")
        logger.info("="*70)
        logger.info(f"Duration: {duration}s (None = continuous)")
        logger.info(f"Email alerts: Enabled")
        logger.info(f"Class Advisor: {config.EMAIL_CONFIG.get('class_advisor_email', 'NOT SET')}")
        logger.info(f"HOD: {config.EMAIL_CONFIG.get('hod_email', 'NOT SET')}")
        logger.info("="*70)
        
        # Verify email is configured
        if not config.EMAIL_CONFIG.get("enabled", False):
            logger.warning("WARNING: Email is NOT enabled in config!")
            logger.warning("To enable email alerts, set EMAIL_ENABLED=true in .env file")
        
        # Start the attendance engine in monitoring mode
        self.engine.mode = "monitoring"
        self.engine.start_camera(mode="monitoring")
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("MONITORING SUMMARY")
        logger.info("="*70)
        
        # Get stats
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            today = str(date.today())
            
            # Registered students
            cursor.execute('SELECT COUNT(*) FROM people')
            total_students = cursor.fetchone()[0]
            
            # Marked attendance
            cursor.execute('SELECT COUNT(DISTINCT person_id) FROM attendance WHERE DATE(date) = ?', (today,))
            marked = cursor.fetchone()[0]
            
            # Movement log
            cursor.execute('SELECT COUNT(*) FROM movement_log WHERE DATE(datetime(timestamp, "unixepoch")) = ?', (today,))
            movements = cursor.fetchone()[0]
            
            # Unknown alerts
            cursor.execute('SELECT COUNT(*) FROM alerts WHERE DATE(datetime(timestamp, "unixepoch")) = ?', (today,))
            alerts = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"Total registered students: {total_students}")
            logger.info(f"Marked attendance: {marked}")
            logger.info(f"Movement detections: {movements}")
            logger.info(f"Security alerts sent: {alerts}")
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        
        logger.info("="*70)


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("ENHANCED MONITORING MODE WITH EMAIL ALERTS")
    print("="*70)
    print("\nThis mode will:")
    print("  1. Monitor all faces in real-time")
    print("  2. Mark attendance for registered students (no emails)")
    print("  3. Detect UNKNOWN persons (unregistered faces)")
    print("  4. Send IMMEDIATE email alerts to:")
    print("     - Class Advisor")
    print("     - HOD (Head of Department)")
    print("  5. Save photos of unknown persons")
    print("  6. Log all movements in database")
    print("\n" + "="*70)
    
    # Check email configuration
    print("\nEmail Configuration:")
    print(f"  Sender Email: {config.EMAIL_CONFIG.get('sender_email', 'NOT SET')}")
    print(f"  Class Advisor: {config.EMAIL_CONFIG.get('class_advisor_email', 'NOT SET')}")
    print(f"  HOD Email: {config.EMAIL_CONFIG.get('hod_email', 'NOT SET')}")
    print(f"  Enabled: {config.EMAIL_CONFIG.get('enabled', False)}")
    
    if not config.EMAIL_CONFIG.get("enabled", False):
        print("\n[WARNING] Email is DISABLED!")
        print("To enable: Add EMAIL_ENABLED=true to .env file")
        response = input("\nContinue without email? (yes/no): ").strip().lower()
        if response != "yes":
            print("Exiting...")
            return False
    
    # Initialize engine
    engine = MonitoringEngine()
    if not engine.load_resources():
        print("[ERROR] Failed to load resources")
        return False
    
    # Get duration
    print("\nHow long to monitor?")
    print("  Enter duration in seconds (or 0 for continuous): ", end="", flush=True)
    try:
        duration_input = input().strip()
        if duration_input == "0" or duration_input == "":
            duration = None
            print("Running continuous monitoring (press CTRL+C to stop)")
        else:
            duration = int(duration_input)
            print(f"Running for {duration} seconds")
    except ValueError:
        print("Invalid input, using 30 seconds")
        duration = 30
    
    print("\n[OK] Starting monitoring...\n")
    
    try:
        engine.start_monitoring(duration=duration)
        return True
    except KeyboardInterrupt:
        print("\n\n[OK] Monitoring stopped by user")
        return True
    except Exception as e:
        print(f"\n[ERROR] Monitoring failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
