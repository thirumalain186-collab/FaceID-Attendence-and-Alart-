# Deployment Guide

## System Requirements

### Minimum Requirements
- Python 3.10+
- 4GB RAM
- 2GB Storage
- Webcam (USB or built-in)
- Internet connection (for email alerts)

### Recommended Requirements
- Python 3.11+
- 8GB RAM
- 10GB Storage
- 720p+ Webcam
- Stable internet connection

### Software Dependencies
- Windows 10/11, macOS 10.14+, or Ubuntu 20.04+
- OpenCV 4.8+
- SQLite3

---

## Local Installation

### 1. Clone the Repository
```bash
git clone https://github.com/thirumalain186-collab/FaceID-Attendence-and-Alart-.git
cd FaceID-Attendence-and-Alart-
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 4. Configure Environment
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings
notepad .env
```

### 5. Run Database Migration
```bash
python -c "import database; database.init_database()"
```

### 6. Start the Application
```bash
# CLI mode
python main.py

# Web dashboard
python app.py
```

---

## Docker Deployment

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Quick Start
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables for Docker
Create a `.env` file:
```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
CLASS_ADVISOR_EMAIL=advisor@college.edu
HOD_EMAIL=hod@college.edu
CLASS_NAME=CS-A
COLLEGE_NAME=Your College
CAMERA_INDEX=0
FLASK_PORT=5000
```

### Access the Application
- Web Dashboard: http://localhost:5000
- API: http://localhost:5000/api

---

## Production Checklist

### Security
- [ ] Change default SECRET_KEY in `.env`
- [ ] Use HTTPS for web access
- [ ] Configure firewall rules
- [ ] Enable email encryption (TLS/SSL)
- [ ] Review .gitignore excludes sensitive files

### Performance
- [ ] Enable database indexes
- [ ] Configure log rotation
- [ ] Set up monitoring
- [ ] Test with multiple users

### Backup
- [ ] Set up automated database backups
- [ ] Backup face images regularly
- [ ] Store backups in separate location

### Monitoring
- [ ] Set up log monitoring
- [ ] Configure alerts for errors
- [ ] Monitor disk space
- [ ] Monitor memory usage

---

## Troubleshooting

### Camera Not Detected
```bash
# Check camera index
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# Try different index
# Edit config.py: CAMERA_INDEX = 1
```

### Email Not Sending
```bash
# Test email configuration
python email_sender.py

# Check app password (not regular password)
# Enable 2FA and create App Password in Google Account
```

### Database Errors
```bash
# Reset database
del attendance.db
python -c "import database; database.init_database()"
```

---

## Systemd Service (Linux)

Create `/etc/systemd/system/attendance.service`:
```ini
[Unit]
Description=Smart Attendance System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/attendance
ExecStart=/home/pi/attendance/venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable attendance
sudo systemctl start attendance
sudo systemctl status attendance
```
