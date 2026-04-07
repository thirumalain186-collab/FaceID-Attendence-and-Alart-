# Science Expo - Face Recognition Attendance System
## Complete Deployment & Operations Guide

**Status**: ✅ PRODUCTION READY  
**Date**: April 8, 2026  
**System Version**: v3 (Optimized)

---

## 📋 Quick Start

### 1. Verify System Status
```bash
python science_expo_ready.py
```
This checks all components and confirms deployment readiness.

### 2. Start the System (Recommended - Electron UI)
```bash
cd electron
npm start
```

### 3. Alternative: Direct Python + Flask
```bash
python app.py
# Then open browser: http://127.0.0.1:5000
```

---

## 🎯 System Overview

### Registered Students (7 Total)
- **Aizen** (Roll: 01)
- **Thiru** (Roll: 02)
- **Raj** (Roll: 03)
- **Priya** (Roll: 04)
- **Vikram** (Roll: 05)
- **Neha** (Roll: 06)
- **Arjun** (Roll: 07)

### Key Features
✅ Real-time face recognition  
✅ Multi-face detection (2-5 people simultaneously)  
✅ Automatic attendance marking  
✅ Display student names on camera feed  
✅ Confidence-based filtering  
✅ Database persistence  
✅ Multiple operation modes  
✅ Web dashboard & Electron UI  

---

## 🔧 Operation Modes

### Mode 1: ATTENDANCE (Primary)
**Purpose**: Mark attendance automatically  
**When to use**: Main expo activity, registration desk

**How it works**:
1. Student stands in front of camera
2. System detects face within 0.5-2 seconds
3. Face is recognized against trained model
4. Name appears on screen with confidence score
5. Attendance is automatically marked in database

**Commands**:
```bash
python test_camera_attendance.py    # Quick 15-second test
```

**Expected Output**:
- Face detection: Detected: 1-3 faces
- Recognition: [RECOGNIZED] Aizen (01)
- Attendance: Attendance marked: Aizen
- Display: Student names on camera feed in green boxes

---

### Mode 2: MONITORING
**Purpose**: Track faces without marking attendance  
**When to use**: Security, crowd monitoring, analytics

**How it works**:
1. System detects and logs all faces
2. NO attendance is marked
3. Useful for counting visitors or security

**Usage**: Available via Electron UI "Start Monitoring" button

---

### Mode 3: DEMO
**Purpose**: Demonstrate system capabilities  
**When to use**: Explaining to visitors, system showcase

**How it works**:
1. Shows registered student count
2. Displays confidence scores
3. Can play pre-recorded demos

**Usage**: Available via Electron UI "Demo Mode" button

---

### Mode 4: HEADLESS
**Purpose**: Run without GUI display  
**When to use**: Background processing, server mode

**How it works**:
1. Processes camera frames without displaying
2. Logs all detections to database
3. Silent operation

**Usage**: Available via Electron UI "Headless Mode" button

---

## 🎥 Camera Settings

- **Resolution**: 640x480 @ 30 FPS (auto-adjusted)
- **Face Size**: 80x80 to 200x200 pixels
- **Processing**: Real-time Haar cascade detection
- **Recognition Model**: LBPH (Local Binary Patterns Histograms)
- **Confidence Threshold**: 60.0 (faces with score > 60 are unknown)

---

## 📊 Attendance Records

### View Today's Attendance
```bash
python check_attendance.py
```

### Clear Today's Records (for testing)
```bash
python clear_attendance.py
```

### Database File
- Location: `attendance.db`
- Type: SQLite3
- Tables: people, attendance, movement_log, alerts

---

## ➕ Register New Students

### Quick Registration
```bash
python register_quick.py
```

**Steps**:
1. Enter student name (e.g., "Ravi")
2. Enter roll number (e.g., "08")
3. Stand 30-50cm from camera
4. Press SPACE to capture photos (need 20 photos)
5. Press Q when done
6. System automatically retrains model

**Tips**:
- Ensure good lighting
- Vary angles and distances
- Minimize head movements during capture
- Wait 2 seconds between captures for variety

---

## 🛠️ Troubleshooting

### Issue: Face not being recognized

**Solution 1**: Ensure good lighting
- Avoid backlighting
- Position student toward light source
- Avoid harsh shadows

**Solution 2**: Increase confidence threshold
- Open `config.py`
- Find `CONFIDENCE_THRESHOLD` (default: 60.0)
- Reduce to 50.0 or lower for more matches
- Be aware: Lower values = more false positives

**Solution 3**: Retrain model
- Register student again with more varied poses
- Different angles, distances, lighting conditions

### Issue: Multiple faces detected but only some recognized

**Solution**: This is expected behavior
- System tracks each face independently
- Unknown faces appear as "Unknown" or are skipped
- Multiple faces are processed in real-time

### Issue: Camera not working

**Solution 1**: Check device
- Verify camera is connected
- Check if another app is using camera
- Restart application

**Solution 2**: Test camera
```bash
python camera_test.py
```

**Solution 3**: Try different camera index
- Edit `attendance_engine.py` line 173
- Change `cap = cv2.VideoCapture(0)` to 1, 2, etc.

### Issue: System slow or laggy

**Solution**: Reduce frame processing
- Edit `config.py`
- Increase `FRAME_SKIP` (default: 1, try: 2 or 3)
- Reduces processing frequency, increases speed

### Issue: False positives (wrong student recognized)

**Solution**: Increase confidence threshold
- Edit `config.py`
- Increase `CONFIDENCE_THRESHOLD` (default: 60.0, try: 65-70)
- Higher values = stricter matching

---

## 📈 Performance Metrics

### Expected Performance
- Face detection: 200-300ms per frame
- Face recognition: 50-100ms per face
- Throughput: 5-10 faces per second
- Real-time display: 30 FPS

### System Requirements
- **CPU**: Any modern CPU (Intel/AMD)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB free space
- **Camera**: USB webcam, 640x480 minimum
- **Python**: 3.8+ (3.11 currently used)

---

## 🔐 Database Tables

### people
```
id              - Student ID
name            - Student name
roll_number     - Roll/ID number
role            - Role (usually "student")
registered_at   - Registration timestamp
```

### attendance
```
id              - Record ID
person_id       - FK to people
date            - Date of attendance
time            - Time of attendance
confidence      - Recognition confidence score
```

### movement_log
```
id              - Record ID
person_id       - FK to people
timestamp       - Detection timestamp
location        - Camera location/zone
```

### alerts
```
id              - Record ID
person_id       - FK to people
alert_type      - Type of alert
timestamp       - Alert timestamp
```

---

## 🚀 Deployment Checklist

Before the Science Expo:

- [ ] Run `python science_expo_ready.py` - verify all components
- [ ] Test with live camera: `python test_camera_attendance.py`
- [ ] Clear attendance: `python clear_attendance.py`
- [ ] Verify all 7 students in database
- [ ] Test model training is up to date
- [ ] Test Electron UI: `cd electron && npm start`
- [ ] Verify Flask server starts
- [ ] Check camera positioning and lighting
- [ ] Test registration process: `python register_quick.py`
- [ ] Prepare backup of attendance.db
- [ ] Print quick reference guide

---

## 📝 API Endpoints (Direct Flask)

If running Flask directly (not Electron):

```
GET  /                      Homepage/Dashboard
GET  /api/attendance        Get today's attendance records
GET  /api/students          Get list of all students
POST /api/start_camera      Start camera in attendance mode
POST /api/stop_camera       Stop camera
POST /api/register          Register new student
GET  /api/export            Export attendance to CSV
```

---

## 💾 Backup & Recovery

### Backup Database
```bash
copy attendance.db attendance.db.backup
```

### Restore from Backup
```bash
copy attendance.db.backup attendance.db
```

### Backup Model
```bash
copy trainer/trainer.yml trainer/trainer.yml.backup
copy trainer/label_map.pkl trainer/label_map.pkl.backup
```

---

## 📞 Support & Contact

For issues or questions:
1. Check Troubleshooting section above
2. Review system logs: `logs/` directory
3. Run `python science_expo_ready.py` to diagnose
4. Check camera: `python camera_test.py`
5. Verify database: `python check_db.py`

---

## 🎓 Educational Notes

### How It Works

**1. Face Detection**
- Uses Haar Cascade Classifier
- Identifies face regions in camera feed
- Real-time processing at 30 FPS

**2. Face Recognition**
- Uses LBPH (Local Binary Patterns Histograms)
- Compares face patterns against trained model
- Returns confidence score (0-100)

**3. Matching**
- If confidence < threshold: Unknown face
- If confidence >= threshold: Match found
- Attendance automatically marked

**4. Tracking**
- Faces tracked across frames using position hash
- Prevents double-counting same person
- Tracks multiple people simultaneously

---

## Version History

- **v3** (Current) - Production Ready
  - Optimized face detection
  - Multi-face support
  - Electron UI integration
  - 7 registered students

- **v2** - Core System
  - Single face recognition
  - Basic attendance marking
  - Flask API

- **v1** - Initial
  - Proof of concept
  - Command-line only

---

## License & Credits

**Project**: Face Recognition Attendance System  
**Purpose**: Science Expo Demonstration  
**Built with**: Python, OpenCV, TensorFlow, Flask, Electron  
**Status**: Ready for Production

---

**Last Updated**: April 8, 2026  
**Deployment Status**: ✅ READY FOR SCIENCE EXPO
