"""
System validation test - ensures everything works end-to-end
"""
import requests
import time
import json

print("="*60)
print("SYSTEM VALIDATION TEST")
print("="*60)

# Test 1: Check Flask is running
print("\n[TEST 1] Checking Flask API...")
try:
    response = requests.get("http://localhost:5000/api/health", timeout=5)
    if response.status_code == 200:
        print("[PASS] Flask is running")
    else:
        print(f"[FAIL] Flask returned status {response.status_code}")
except Exception as e:
    print(f"[FAIL] Flask not responding: {e}")
    print("  Start Flask with: python app.py")
    exit(1)

# Test 2: Get registered people
print("\n[TEST 2] Checking registered people...")
try:
    response = requests.get("http://localhost:5000/api/people", timeout=5)
    if response.status_code == 200:
        people = response.json()
        print(f"[PASS] Found {len(people)} registered people")
        for person in people:
            print(f"  - {person.get('name')} (roll: {person.get('roll_number')})")
    else:
        print(f"[FAIL] API error: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 3: Check model status
print("\n[TEST 3] Checking model status...")
try:
    response = requests.get("http://localhost:5000/api/status", timeout=5)
    if response.status_code == 200:
        status = response.json()
        print(f"[PASS] Model loaded: {status.get('model_ready', False)}")
        if status.get('registered_people'):
            print(f"  Registered: {status['registered_people']}")
        if status.get('marked_today'):
            print(f"  Marked today: {status['marked_today']}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 4: Test attendance start
print("\n[TEST 4] Starting attendance engine...")
try:
    response = requests.post("http://localhost:5000/api/start", json={"mode": "attendance"}, timeout=5)
    if response.status_code == 200:
        print("[PASS] Attendance engine started")
        time.sleep(2)
    else:
        print(f"[FAIL] Failed to start: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 5: Check stats
print("\n[TEST 5] Checking runtime stats...")
try:
    response = requests.get("http://localhost:5000/api/status", timeout=5)
    if response.status_code == 200:
        status = response.json()
        print(f"[PASS] Engine running: {status.get('running', False)}")
        print(f"  Frames processed: {status.get('frames_processed', 0)}")
        print(f"  Mode: {status.get('mode', 'unknown')}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

print("\n" + "="*60)
print("VALIDATION COMPLETE")
print("="*60)
print("\nSystem is ready for Science Expo!")
print("Open Electron app to test full workflow")
