# API Documentation

## REST API Endpoints

### Base URL
```
http://localhost:5000/api
```

### Health Check

#### GET /api/v1/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T16:00:00Z"
}
```

---

### Attendance Endpoints

#### GET /api/v1/attendance/today
Get today's attendance records.

**Response:**
```json
{
  "data": [
    {
      "name": "John Doe",
      "role": "student",
      "roll": "CS001",
      "time": "09:15:30",
      "status": "present"
    }
  ],
  "count": 1
}
```

#### GET /api/v1/attendance/stats
Get attendance statistics.

**Response:**
```json
{
  "present_today": 25,
  "total_people": 30,
  "total_students": 25,
  "total_teachers": 5,
  "alerts_today": 0,
  "present_students": 22,
  "attendance_rate": 88.0,
  "date": "2026-04-05"
}
```

#### GET /api/v1/attendance/export
Export attendance records to CSV.

**Query Parameters:**
- `start` (optional): Start date (YYYY-MM-DD)
- `end` (optional): End date (YYYY-MM-DD)

**Response:** CSV file download

---

### People Endpoints

#### GET /api/v1/people
Get all registered people.

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "role": "student",
      "roll": "CS001",
      "class": "CS-A",
      "registered": "2026-04-01T10:00:00"
    }
  ],
  "count": 1
}
```

---

### Camera Endpoints

#### POST /api/v1/camera/start
Start the camera.

**Request Body:**
```json
{
  "mode": "attendance"
}
```

**Response:**
```json
{
  "status": "started",
  "mode": "attendance"
}
```

#### POST /api/v1/camera/stop
Stop the camera.

**Response:**
```json
{
  "status": "stopped"
}
```

---

### Email Endpoints

#### POST /api/v1/email/test
Test email configuration.

**Response:**
```json
{
  "success": true
}
```

#### POST /api/v1/email/send-report
Send daily attendance report.

**Response:**
```json
{
  "success": true
}
```

---

### Settings Endpoints

#### GET /api/v1/settings
Get current settings.

**Response:**
```json
{
  "sender_email": "sender@gmail.com",
  "advisor_email": "advisor@college.edu",
  "hod_email": "hod@college.edu",
  "enabled": true,
  "class_name": "CS-A"
}
```

#### POST /api/v1/settings
Update settings.

**Request Body:**
```json
{
  "sender_email": "new_email@gmail.com",
  "advisor_email": "new_advisor@college.edu",
  "hod_email": "new_hod@college.edu",
  "enabled": true,
  "class_name": "CS-B"
}
```

**Response:**
```json
{
  "success": true
}
```

---

## Usage Examples

### Mark Attendance via API
```python
import requests

response = requests.post(
    'http://localhost:5000/api/v1/camera/start',
    json={"mode": "attendance"}
)
print(response.json())
```

### Get Today's Attendance
```python
import requests

response = requests.get('http://localhost:5000/api/v1/attendance/today')
data = response.json()
print(f"Present today: {len(data['data'])}")
```

### Export Report
```bash
curl -O http://localhost:5000/api/v1/attendance/export?start=2026-04-01&end=2026-04-05
```

---

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
