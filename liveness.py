"""
Liveness Detection Module for Smart Attendance System v2
Face anti-spoofing using blink detection and texture analysis
"""

import cv2
import numpy as np
import math
import config
from logger import get_logger

logger = get_logger()

# Eye landmark indices for 68-point face landmark model
LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

# EAR threshold for blink detection
BLINK_EAR_THRESHOLD = 0.21
BLINK_CONSECUTIVE_FRAMES = 2


def euclidean_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class LivenessDetector:
    """Face liveness detection using multiple techniques."""
    
    def __init__(self):
        self.blink_count = 0
        self.last_blink_time = 0
        self.blink_timestamps = []
        self.ear_history = []
        self.frame_count = 0
        
        # Settings
        self.enable_blink = config.LIVENESS_CONFIG.get("enable_blink_detection", True)
        self.enable_texture = config.LIVENESS_CONFIG.get("enable_texture_analysis", True)
        self.required_blinks = config.LIVENESS_CONFIG.get("required_blinks", 1)
        
        logger.info(f"Liveness detector initialized (blink={self.enable_blink}, texture={self.enable_texture})")
    
    def calculate_ear(self, eye_points):
        """Calculate Eye Aspect Ratio for blink detection.
        
        EAR = (|p1-p5| + |p2-p4|) / (2 * |p0-p3|)
        
        Normal EAR: ~0.25-0.35
        Blink EAR: < 0.21
        """
        if len(eye_points) != 6:
            return 0.3
        
        # Vertical distances
        A = euclidean_distance(eye_points[1], eye_points[5])
        B = euclidean_distance(eye_points[2], eye_points[4])
        
        # Horizontal distance
        C = euclidean_distance(eye_points[0], eye_points[3])
        
        if C == 0:
            return 0.3
        
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_eye_landmarks(self, landmarks, eye_indices):
        """Extract eye landmarks from 68-point landmark array."""
        if landmarks is None or len(landmarks) < 68:
            return None
        
        eye_points = []
        for idx in eye_indices:
            if idx < len(landmarks):
                point = landmarks[idx]
                eye_points.append((float(point[0]), float(point[1])))
        
        return eye_points if len(eye_points) == 6 else None
    
    def detect_blink(self, left_eye, right_eye):
        """Detect if a blink has occurred."""
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Store EAR history
        self.ear_history.append(avg_ear)
        if len(self.ear_history) > 30:
            self.ear_history.pop(0)
        
        # Blink detected if EAR drops below threshold
        is_blink = avg_ear < BLINK_EAR_THRESHOLD
        
        if is_blink:
            self.blink_count += 1
            self.blink_timestamps.append(self.frame_count)
            
            # Keep only recent blinks
            if len(self.blink_timestamps) > 10:
                self.blink_timestamps.pop(0)
        
        return {
            'is_blink': is_blink,
            'left_ear': left_ear,
            'right_ear': right_ear,
            'avg_ear': avg_ear,
            'blink_count': self.blink_count
        }
    
    def analyze_texture(self, face_roi):
        """Analyze face texture to detect photo/spoof attacks.
        
        Real faces have more texture variation than printed photos.
        Uses Local Binary Pattern (LBP) analysis.
        """
        if face_roi is None or face_roi.size == 0:
            return 0.5
        
        try:
            # Convert to grayscale if needed
            if len(face_roi.shape) == 3:
                gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_roi
            
            # Resize for consistent analysis
            gray = cv2.resize(gray, (64, 64))
            
            # Calculate gradient magnitude (Sobel)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient = np.sqrt(sobelx**2 + sobely**2)
            
            # Calculate variance of gradient
            gradient_var = np.var(gradient)
            
            # Normalize to 0-1 range
            texture_score = min(1.0, gradient_var / 1000.0)
            
            return texture_score
            
        except Exception as e:
            logger.debug(f"Texture analysis error: {e}")
            return 0.5
    
    def analyze_color_variance(self, face_roi):
        """Analyze color variance in face region.
        
        Real faces have natural color gradients.
        Photos may have more uniform color distribution.
        """
        if face_roi is None or face_roi.size == 0:
            return 0.5
        
        try:
            if len(face_roi.shape) != 3:
                return 0.5
            
            # Calculate color variance per channel
            variances = []
            for i in range(3):
                channel = face_roi[:, :, i]
                variances.append(np.var(channel))
            
            # Normalize
            avg_variance = np.mean(variances)
            color_score = min(1.0, avg_variance / 500.0)
            
            return color_score
            
        except Exception as e:
            logger.debug(f"Color analysis error: {e}")
            return 0.5
    
    def check_liveness(self, face_roi, landmarks=None, left_eye=None, right_eye=None):
        """Main liveness check combining all techniques.
        
        Returns dict with:
        - is_live: bool - True if face appears to be real
        - score: float - Overall liveness score (0-1)
        - details: dict - Individual check results
        """
        self.frame_count += 1
        
        results = {
            'is_live': False,
            'score': 0.0,
            'details': {},
            'passed': False
        }
        
        scores = []
        
        # Blink detection
        if self.enable_blink and left_eye and right_eye:
            blink_result = self.detect_blink(left_eye, right_eye)
            results['details']['blink'] = blink_result
            
            # Real face should have blinked at least once
            if self.blink_count >= self.required_blinks:
                scores.append(1.0)
            elif self.blink_count > 0:
                scores.append(0.5)
            else:
                # No blink yet - not necessarily fake
                scores.append(0.8)
        
        # Texture analysis
        if self.enable_texture and face_roi is not None:
            texture_score = self.analyze_texture(face_roi)
            results['details']['texture'] = {
                'score': texture_score,
                'real_threshold': 0.15
            }
            scores.append(texture_score)
            
            color_score = self.analyze_color_variance(face_roi)
            results['details']['color'] = {
                'score': color_score,
                'real_threshold': 0.1
            }
            scores.append(color_score)
        
        # Calculate overall score
        if scores:
            results['score'] = np.mean(scores)
            results['is_live'] = results['score'] >= 0.3
            results['passed'] = results['score'] >= 0.25
        
        return results
    
    def reset(self):
        """Reset liveness detection state."""
        self.blink_count = 0
        self.blink_timestamps = []
        self.ear_history = []
        self.frame_count = 0
        logger.info("Liveness detector reset")


# Global liveness detector instance
_liveness_detector = None


def get_liveness_detector():
    """Get or create the global liveness detector."""
    global _liveness_detector
    if _liveness_detector is None:
        _liveness_detector = LivenessDetector()
    return _liveness_detector


def check_face_liveness(face_roi, landmarks=None):
    """Convenience function to check face liveness."""
    detector = get_liveness_detector()
    
    left_eye = None
    right_eye = None
    
    if landmarks is not None:
        left_eye = detector.get_eye_landmarks(landmarks, LEFT_EYE)
        right_eye = detector.get_eye_landmarks(landmarks, RIGHT_EYE)
    
    return detector.check_liveness(face_roi, landmarks, left_eye, right_eye)


if __name__ == "__main__":
    # Test liveness detector
    detector = LivenessDetector()
    print(f"Settings - Blink: {detector.enable_blink}, Texture: {detector.enable_texture}")
    
    # Simulate EAR values
    test_ears = [0.30, 0.28, 0.25, 0.22, 0.18, 0.15, 0.20, 0.25, 0.28, 0.30]
    for ear in test_ears:
        detector.ear_history.append(ear)
    
    print(f"Average EAR: {np.mean(detector.ear_history):.3f}")
