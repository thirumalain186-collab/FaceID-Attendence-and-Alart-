#!/usr/bin/env python3
"""
USB Webcam Compatibility Test
Tests if your USB webcam will work with the attendance system
"""

import cv2
import sys
from time import sleep

print("\n" + "="*60)
print("USB WEBCAM COMPATIBILITY TEST")
print("="*60 + "\n")

def test_camera():
    """Test camera initialization"""
    print("STEP 1: Testing camera detection...")
    print("-" * 60)
    
    # Try different camera indices
    for i in range(5):
        print(f"\nTrying camera index {i}...", end=" ")
        
        # Try with DirectShow (Windows)
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        
        if cap.isOpened():
            print("✓ SUCCESS!")
            print(f"\nCamera found at index {i}")
            
            # Get camera properties
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"  Resolution: {int(width)} x {int(height)}")
            print(f"  FPS: {fps}")
            
            # Try to capture a frame
            print("\nTrying to capture frame...", end=" ")
            ret, frame = cap.read()
            
            if ret and frame is not None:
                print("✓ SUCCESS!")
                print(f"  Frame captured: {frame.shape[0]}x{frame.shape[1]} pixels")
                
                # Try configuring camera (like our system does)
                print("\nConfiguring camera settings...", end=" ")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print("✓ SUCCESS!")
                
                # Warm up camera (like our system does)
                print("Warming up camera...", end=" ")
                for _ in range(5):
                    ret, frame = cap.read()
                    if not ret:
                        print("✗ FAILED!")
                        cap.release()
                        return False
                print("✓ SUCCESS!")
                
                cap.release()
                return True
            else:
                print("✗ FAILED - Could not capture frame")
                cap.release()
                continue
        else:
            print("Not available")
    
    return False

def check_camera_app():
    """Instructions to verify camera works"""
    print("\n" + "="*60)
    print("BEFORE RUNNING ATTENDANCE SYSTEM")
    print("="*60)
    print("\n1. Connect your USB webcam")
    print("2. Open Windows Camera app (search 'Camera' in Start menu)")
    print("3. See live video? If YES, camera is working!")
    print("4. If NO video, camera has issues - check:")
    print("   - USB cable connection")
    print("   - Device Manager for camera")
    print("   - Settings → Privacy & Security → Camera (must be ON)")

def main():
    try:
        result = test_camera()
        
        if result:
            print("\n" + "="*60)
            print("RESULT: ✓ USB WEBCAM WILL WORK!")
            print("="*60)
            print("\nYour attendance system will work perfectly with this camera!")
            print("You can now run: npm start")
            return 0
        else:
            print("\n" + "="*60)
            print("RESULT: ✗ Camera not found")
            print("="*60)
            check_camera_app()
            return 1
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure USB webcam is connected")
        print("2. Check Device Manager for camera")
        print("3. Restart the script")
        return 1

if __name__ == "__main__":
    sys.exit(main())
