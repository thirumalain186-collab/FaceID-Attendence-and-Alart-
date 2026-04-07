#!/usr/bin/env python3
"""
Non-interactive wrapper to run monitoring mode continuously
Perfect for Science Expo deployment - just run and it works!
"""

import sys
import time
import threading

def main():
    print("=" * 70)
    print("  SMART ATTENDANCE SYSTEM - MONITORING MODE")
    print("=" * 70)
    print("\nStarting continuous face recognition and monitoring...")
    print("  - Real-time face recognition")
    print("  - Automatic attendance marking")
    print("  - Unknown person detection")
    print("  - Email alerts to Class Advisor & HOD")
    print("  - Photo evidence collection")
    print("\nPress CTRL+C to stop\n")
    
    time.sleep(1)
    
    # Import and run monitoring directly (bypass interactive input)
    try:
        from monitoring_with_alerts import MonitoringEngine
        import config
        
        # Verify email is enabled
        if not config.EMAIL_CONFIG.get("enabled", False):
            print("[WARNING] Email alerts are DISABLED")
            print("Continuing without email notifications...")
        
        # Initialize and start monitoring
        engine = MonitoringEngine()
        if not engine.load_resources():
            print("[ERROR] Failed to load resources")
            return False
        
        print("[OK] Monitoring engine ready\n")
        
        # Start continuous monitoring (None = continuous)
        engine.start_monitoring(duration=None)
        
        # Keep the script alive by waiting for signals
        print("\n[OK] Monitoring is running in background")
        print("Press CTRL+C to stop the monitoring system\n")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n[OK] Monitoring stopped")
        return True
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
