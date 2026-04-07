# QUICK REGISTRATION STEPS

## Register New Student in 3 Simple Steps

### STEP 1: Run Registration Script
```bash
python register_quick.py
```

### STEP 2: Enter Student Information
```
Student Name: Raj Kumar
Roll Number: 02
```

### STEP 3: Capture Photos
- Stand 30-50cm from camera
- Press SPACE to capture each photo
- Capture 15-20 photos from different angles
- Press Q when done

**That's it! Model trains automatically.**

---

## Example Registration Session

```
================== REGISTER NEW STUDENT ==================

Student Name: Priya Singh
Roll Number: 03

Registering: Priya Singh (03)
Stand 30-50cm from camera
Press SPACE to capture, Q to finish

[Camera window opens with face detection]

Captured: 1/20
Captured: 2/20
Captured: 3/20
...
Captured: 20/20

[Student presses Q]

✓ Captured 20 photos
Training model...

[Training in progress...]

✓ Priya Singh is now registered!
```

---

## Available Registration Options

| Script | Speed | Use Case |
|--------|-------|----------|
| `register_quick.py` | ⚡ FASTEST | Best for Science Expo |
| `register_optimized.py` | ⚡⚡ MEDIUM | Better instructions |
| Electron UI | ⚡⚡⚡ SLOWEST | Professional interface |

---

## After Registration - Verify It Worked

**Check 1: Database**
```bash
python check_db.py
```
Should show new student in list

**Check 2: Model**
```bash
python final_test.py
```
All 25 tests should pass

**Check 3: Recognition**
```bash
python test_live_recognition.py
```
Live camera should recognize them

---

## Register Multiple Students

Simply repeat for each student:

```bash
python register_quick.py
# Student 1 - Enter name, capture photos, done

python register_quick.py
# Student 2 - Enter name, capture photos, done

python register_quick.py
# Student 3 - Enter name, capture photos, done

# Check all registered:
python check_db.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No face detected" | Move closer (30-50cm) |
| "Multiple faces" | Ask others to leave |
| "Camera not available" | Check USB connection |
| "Need 10 photos" | Capture more photos |

---

## Pro Tips for Best Results

1. **Lighting** - Bright, well-lit room
2. **Distance** - Stand 30-50cm from camera
3. **Angles** - Capture from multiple angles
4. **Quantity** - 20 photos is better than 10
5. **Quality** - Clear, centered face photos

---

## Next: Start Using the System

After registering students:

```bash
# 1. Start backend
python app.py

# 2. Open Electron UI (new terminal)
cd electron
npm start

# 3. Click "Start Attendance"
# 4. Have students look at camera
# 5. Watch attendance marked automatically
```

---

Made simple for Science Expo!
