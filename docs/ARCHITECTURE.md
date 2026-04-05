# System Architecture

## Overview

The Smart Attendance System uses a modular architecture with Python, SQLite, and OpenCV for face recognition.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Smart Attendance System                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CLI    │  │   Web    │  │ Scheduler│  │   API    │        │
│  │  (main)  │  │  (app)   │  │(schedul) │  │ (app)    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│  ┌────▼─────────────▼─────────────▼─────────────▼────┐         │
│  │              Core Modules                          │         │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │         │
│  │  │Attendance│ │Register │ │ Train   │ │  Email  │  │         │
│  │  │Engine   │ │Faces    │ │ Model   │ │Sender   │  │         │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │         │
│  └───────┼───────────┼───────────┼───────────┼───────┘         │
│          │           │           │           │                 │
│  ┌───────▼───────────▼───────────▼───────────▼──────┐         │
│  │                   Database                         │         │
│  │    ┌─────────────────────────────────────────┐    │         │
│  │    │  SQLite: batches, people, attendance,   │    │         │
│  │    │          alerts, movement_log, settings │    │         │
│  │    └─────────────────────────────────────────┘    │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions

### Core Modules

| Module | Description |
|--------|-------------|
| `main.py` | CLI entry point with menu interface |
| `app.py` | Flask web dashboard |
| `attendance_engine.py` | Camera control and face recognition |
| `register_faces.py` | Face capture and registration |
| `train.py` | LBPH model training |
| `database.py` | SQLite database operations |
| `email_sender.py` | Email notifications |
| `pdf_generator.py` | Report PDF generation |
| `scheduler.py` | Automated task scheduling |
| `config.py` | Configuration management |
| `logger.py` | Structured logging |

### Data Modules

| Module | Description |
|--------|-------------|
| `attendance_engine.py` | Face detection, recognition, attendance marking |
| `scheduler.py` | APScheduler for automated tasks |

---

## Data Flow

### Face Registration Flow
```
User Input → Validate → Capture Images → Save to Dataset → Add to DB → Train Model
```

### Attendance Marking Flow
```
Camera → Detect Face → Extract Features → LBPH Recognition → Match → Mark Attendance
```

### Alert Flow
```
Unknown Detection → Capture Image → Generate PDF → Send Email → Log Alert
```

---

## Database Schema

```
┌─────────────┐
│   batches   │
├─────────────┤
│ id (PK)     │
│ start_date  │
│ end_date    │
│ class_name  │
│ status      │
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐      ┌─────────────┐
│   people    │      │ attendance  │
├─────────────┤      ├─────────────┤
│ id (PK)     │◄────│ person_id   │
│ name        │      │ name        │
│ role        │      │ date        │
│ roll_number │      │ time_in     │
│ email       │      │ status      │
│ class_name  │      └─────────────┘
│ batch_id    │
│ active      │
└─────────────┘
```

### Tables

| Table | Purpose |
|-------|---------|
| `batches` | 30-day registration periods |
| `people` | Registered students/teachers |
| `attendance` | Daily attendance records |
| `movement_log` | Entry/exit tracking |
| `alerts` | Security alert history |
| `settings` | Application settings |

---

## Configuration Structure

```python
# config.py
ATTENDANCE_CONFIG = {
    "confidence_threshold": 80,  # Recognition threshold
    "camera_index": 0,           # Webcam device
    "samples_per_person": 30,    # Images to capture
    "class_name": "CS-A"        # Class identifier
}

SCHEDULE_CONFIG = {
    "attendance_start": "09:00",  # Start attendance marking
    "attendance_stop": "09:30",   # Stop marking
    "day_end": "16:30"           # Stop camera
}

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "...",
    # Credentials loaded from .env
}
```

---

## Design Patterns

### Singleton Pattern
- `AttendanceEngine` - Single instance across app
- `Logger` - Centralized logging

### Factory Pattern
- `get_engine()` - Factory for engine instance
- `get_logger()` - Factory for logger instance

### Observer Pattern
- `APScheduler` triggers scheduled events
- Email notifications triggered by alerts

### Repository Pattern
- Database functions in `database.py`
- Abstracts SQL operations

---

## Security Considerations

1. **Credentials**: Stored in `.env`, never in code
2. **Input Validation**: All user inputs validated
3. **SQL Injection**: Parameterized queries used
4. **File Access**: Paths validated before use
5. **Logging**: Sensitive data excluded from logs
