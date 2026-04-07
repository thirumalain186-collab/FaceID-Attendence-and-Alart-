# How to Register New Students

## Quick Guide for Science Expo

### Method 1: Using Command Line (FASTEST)

```bash
python register_optimized.py
```

**Follow these steps:**

1. **Enter name when prompted**
   ```
   Enter your name: Raj Kumar
   ```

2. **Enter roll number**
   ```
   Enter roll number: 02
   ```

3. **Camera window opens with face detection**
   - Green box around detected face = GOOD
   - Red text means: move closer/better lighting

4. **Press SPACE to capture each photo**
   - Capture 15-20 photos minimum
   - Move slightly between captures (left, center, right angles)
   - Face should be large in the frame

5. **Press Q to finish**
   - System automatically trains the model
   - Takes 5-10 seconds
   - Success message appears

**Total time: 2-3 minutes per student**

---

## Step-by-Step Instructions

### Before You Start
- Good lighting (bright room or near window)
- Webcam working
- Student ready to look at camera

### Registration Process

#### Step 1: Run Registration Script
```bash
python register_optimized.py
```

Output will show:
```
============================================================
FACE REGISTRATION - OPTIMIZED VERSION
============================================================

IMPORTANT: Stand 30-50cm from camera for best results
Keep lighting bright and face centered

Enter your name: 
```

#### Step 2: Enter Student Details
```
Enter your name: Priya Singh
Enter roll number: 03
```

Camera window opens with live feed showing:
- Green rectangles = face detection working
- Photo counter in top-left corner
- Instructions on screen

#### Step 3: Capture Photos

**What to do:**
1. Position face in the green detection box
2. Press SPACE to capture
3. Move slightly and repeat
4. Capture at different angles:
   - Face centered (5 photos)
   - Face tilted left (5 photos)
   - Face tilted right (5 photos)
   - Face slightly up/down (5 photos)

**Good captures:**
- Face centered in frame
- Good lighting on face
- Face is LARGE (not tiny)
- Eyes clearly visible

**Poor captures:**
- Face too small (too far)
- Face blurry
- Bad lighting (too dark/shadowy)
- Side profile (90 degrees)

#### Step 4: Finish Registration
- Once you have 15+ photos, press 'Q'
- System automatically trains
- See success message:
```
============================================================
Captured 20 photos!
Saved to: dataset/priya_singh_03_student

Training model...
... (training progress) ...

✓ REGISTRATION COMPLETE!
Name: Priya Singh
Roll: 03
Photos captured: 20

You are now registered!
Run 'python app.py' and use Electron to test attendance
```

---

## Verification After Registration

### Check 1: Verify Files Created
```bash
# List training images
dir dataset\priya_singh_03_student

# Should show 20 images like:
# - priya_singh_03_0.jpg
# - priya_singh_03_1.jpg
# - ... etc
```

### Check 2: Check Database
```bash
python check_db.py
```

Should show:
```
Registered people: 2
  Name: Aizen, Roll: 01
  Name: Priya Singh, Roll: 03
```

### Check 3: Test Recognition on Training Images
```bash
python diagnose_training.py
```

Should show:
```
Label map: {0: 'Aizen (01)', 1: 'Priya Singh (03)'}
Testing image: dataset\priya_singh_03_student\priya_singh_03_0.jpg
Faces detected: 1
Recognition: label=1, confidence=0.0
Display name: Priya Singh (03)
Recognition quality: 100.0%
```

---

## Register Multiple Students at Once

To register several students quickly:

```bash
python register_optimized.py
# Register Student 1
# Press Q to finish

python register_optimized.py
# Register Student 2
# Press Q to finish

# Repeat for each student...
```

**Note:** Each registration creates a new model automatically, so you don't need to train separately.

---

## Troubleshooting Registration

### Problem: "Face not detected" / Green box not appearing

**Solution:**
- Move closer to camera (30-50cm away)
- Improve lighting (face should be well-lit)
- Check if camera is working: `python test_camera.py`

### Problem: "Multiple faces detected"

**Solution:**
- Only one person should be in front of camera
- Ask others to move away
- Try again when alone

### Problem: "Not enough photos"

**Solution:**
- You need at least 10 photos minimum
- Run registration again
- Capture 15-20 photos this time

### Problem: "ERROR: Cannot open camera!"

**Solution:**
1. Check camera is connected to USB
2. Check no other app is using camera
3. Restart the script
4. Try: `python test_camera.py`

### Problem: Recognition not working after registration

**Solution:**
1. Re-run registration with better lighting
2. Capture more photos (20+)
3. Lower confidence threshold in attendance_engine.py
4. Contact support

---

## Best Practices

✅ **DO:**
- Capture photos in the same lighting as Science Expo will be
- Vary angles (face left, center, right)
- Keep face large in frame (fill most of the box)
- Use minimum 15 photos, better with 20+
- Test recognition after registration

❌ **DON'T:**
- Capture in bad lighting
- Hold camera too far away
- Wear sunglasses/hat during capture
- Capture only straight-on photos
- Rush - take time to get good variety

---

## Quick Registration Checklist

Before registering each student:

- [ ] Student name ready
- [ ] Roll number ready
- [ ] Camera working
- [ ] Good lighting
- [ ] Student ready to stand still for 2-3 minutes

During registration:
- [ ] Face centered in green box
- [ ] Capture 15+ photos minimum
- [ ] Include different angles
- [ ] Photos are large and clear

After registration:
- [ ] Success message appears
- [ ] Check database: `python check_db.py`
- [ ] Test: `python final_test.py`

---

## For Science Expo Demo

**Show this to visitors:**

1. **Live Registration Demo**
   ```bash
   python register_optimized.py
   ```
   Let a volunteer register while audience watches

2. **Show Face Recognition**
   ```bash
   python app.py
   # Then open Electron
   ```
   Have registered student look at camera, see attendance marked

3. **Show Database**
   ```bash
   python check_db.py
   ```
   Display all registered students and attendance

This demonstrates:
- How face recognition works
- Real-time detection
- Automatic training
- Database storage

---

## Contact & Support

If you have issues:
1. Run diagnostic: `python final_test.py`
2. Check troubleshooting section above
3. Verify camera is working: `python test_camera.py`
