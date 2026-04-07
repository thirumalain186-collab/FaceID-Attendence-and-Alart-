"""
Smart Attendance System - Web Dashboard
Optional Flask-based web interface for attendance management
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import io
import csv
import time
import shutil
from datetime import date, datetime, timedelta
from functools import wraps
from threading import Lock
from PIL import Image

import config
import database
import email_sender
from logger import get_logger

logger = get_logger()

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

CORS(app, resources={r"/api/*": {"origins": "*"}})

_rate_limit_store = {}
_rate_limit_lock = Lock()


def rate_limit(calls=30, period=60):
    """Rate limiting decorator - max calls per period seconds."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            key = f"{client_ip}:{f.__name__}"
            
            with _rate_limit_lock:
                now = time.time()
                if key in _rate_limit_store:
                    requests, first_call = _rate_limit_store[key]
                    if now - first_call < period:
                        if requests >= calls:
                            return jsonify({"error": "Rate limit exceeded"}), 429
                        _rate_limit_store[key] = (requests + 1, first_call)
                    else:
                        _rate_limit_store[key] = (1, now)
                else:
                    _rate_limit_store[key] = (1, now)
                
                for k in list(_rate_limit_store.keys()):
                    if now - _rate_limit_store[k][1] > 300:
                        del _rate_limit_store[k]
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def _sanitize_string(value, max_length=200):
    """Sanitize string input."""
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def _validate_mode(mode):
    """Validate camera mode."""
    return mode in ("attendance", "monitoring")


def require_json(f):
    """Decorator to require JSON content type."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "JSON body required"}), 400
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    """Dashboard home page."""
    stats = database.get_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/api/v1/health")
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    })


@app.route("/api/v1/stats")
def api_stats():
    """API endpoint for statistics."""
    return jsonify(database.get_stats())


@app.route("/api/v1/analytics/weekly")
@rate_limit(calls=30, period=60)
def api_analytics_weekly():
    """Get weekly attendance trends (last 7 days)."""
    return jsonify({
        "data": database.get_weekly_attendance(),
        "summary": {
            "avg_rate": round(sum(d['rate'] for d in database.get_weekly_attendance()) / 7, 1)
        }
    })


@app.route("/api/v1/analytics/monthly")
@rate_limit(calls=30, period=60)
def api_analytics_monthly():
    """Get monthly attendance trends (last 30 days)."""
    return jsonify({
        "data": database.get_monthly_attendance(),
        "summary": database.get_monthly_summary()
    })


@app.route("/api/v1/analytics/rates")
@rate_limit(calls=30, period=60)
def api_analytics_rates():
    """Get attendance rates for all students."""
    days = request.args.get("days", 30, type=int)
    days = max(7, min(90, days))
    return jsonify({
        "data": database.get_all_attendance_rates(days),
        "period_days": days
    })


@app.route("/api/v1/analytics/low-attendance")
@rate_limit(calls=30, period=60)
def api_analytics_low():
    """Get students with low attendance."""
    threshold = request.args.get("threshold", 75, type=int)
    days = request.args.get("days", 30, type=int)
    threshold = max(50, min(95, threshold))
    days = max(7, min(90, days))
    return jsonify({
        "data": database.get_low_attendance_students(threshold, days),
        "threshold": threshold,
        "period_days": days,
        "count": len(database.get_low_attendance_students(threshold, days))
    })


@app.route("/api/v1/analytics/person/<int:person_id>")
@rate_limit(calls=30, period=60)
def api_analytics_person(person_id):
    """Get attendance history for a specific person."""
    days = request.args.get("days", 30, type=int)
    days = max(7, min(90, days))
    person = database.get_person_by_id(person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    rate_data = database.get_person_attendance_rate(person_id, days)
    return jsonify({
        "person": {
            "id": person.get('id'),
            "name": person.get('name'),
            "roll": person.get('roll_number'),
            "role": person.get('role')
        },
        "statistics": rate_data
    })


@app.route("/api/v1/attendance/today")
@rate_limit(calls=60, period=60)
def api_today_attendance():
    """Get today's attendance records."""
    attendance = database.get_today_attendance()
    records = [
        {
            "id": r.get('id') if isinstance(r.get('id'), int) else None,
            "person_id": r.get('person_id') if isinstance(r.get('person_id'), int) else None,
            "name": _sanitize_string(r.get('name', '')),
            "roll": _sanitize_string(r.get('roll_number', '')),
            "date": r.get('date', ''),
            "time": r.get('time_in', ''),
            "status": r.get('status', '')
        }
        for r in attendance
    ]
    return jsonify({"data": records, "count": len(records)})


@app.route("/api/v1/people")
@rate_limit(calls=60, period=60)
def api_people():
    """Get all registered people."""
    people = database.get_active_people()
    records = [
        {
            "id": p.get('id') if isinstance(p.get('id'), int) else None,
            "name": _sanitize_string(p.get('name', '')),
            "role": p.get('role', ''),
            "roll": _sanitize_string(p.get('roll_number', '')),
            "class": _sanitize_string(p.get('class_name', '')),
            "registered": p.get('registered_at', '')
        }
        for p in people
    ]
    return jsonify({"data": records, "count": len(records)})


@app.route("/api/v1/camera/start", methods=["POST"])
@require_json
@rate_limit(calls=10, period=60)
def start_camera():
    """Start camera in background thread."""
    from attendance_engine import get_engine
    
    engine = get_engine()
    
    if engine.running:
        return jsonify({"status": "already_running"})
    
    data = request.json
    raw_mode = data.get("mode", "attendance")
    mode = _sanitize_string(raw_mode, 20)
    
    if not _validate_mode(mode):
        mode = "attendance"
    
    demo_mode = bool(data.get("demo", False))
    headless = bool(data.get("headless", False))
    
    engine.start_camera(mode=mode, demo_mode=demo_mode, headless=headless)
    
    status = engine.get_status()
    
    return jsonify({
        "status": "started",
        "mode": status.get('mode', mode),
        "demo": status.get('demo_mode', False),
        "headless": status.get('headless', False)
    })


@app.route("/api/v1/camera/stop", methods=["POST"])
def stop_camera():
    """Stop camera."""
    from attendance_engine import get_engine
    
    engine = get_engine()
    engine.stop_camera()
    
    return jsonify({"status": "stopped"})


@app.route("/api/v1/camera/status")
def camera_status():
    """Get camera status."""
    from attendance_engine import get_engine
    engine = get_engine()
    return jsonify(engine.get_status())


@app.route("/api/v1/reports/export")
def export_report():
    """Export attendance to CSV."""
    start = request.args.get("start", (date.today() - timedelta(days=7)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    
    if len(start) != 10 or len(end) != 10:
        return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400
    
    attendance = database.get_attendance_by_date_range(start, end)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Roll Number", "Date", "Time In", "Status"])
    
    for r in attendance:
        writer.writerow([
            r.get('name', ''),
            r.get('roll_number', ''),
            r.get('date', ''),
            r.get('time_in', ''),
            r.get('status', '')
        ])
    
    safe_start = start.replace('-', '')
    safe_end = end.replace('-', '')
    filename = f"attendance_{safe_start}_to_{safe_end}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment;filename={filename}",
            "X-Content-Type-Options": "nosniff"
        }
    )


@app.route("/api/v1/email/test", methods=["POST"])
def api_test_email():
    """Test email configuration."""
    success = email_sender.test_email()
    return jsonify({"success": success, "message": "Email sent" if success else "Email failed"})


@app.route("/api/v1/email/send-report", methods=["POST"])
def api_send_report():
    """Send daily report."""
    import pdf_generator
    pdf_path = pdf_generator.generate_daily_report()
    email_sender.send_daily_report(None, pdf_path)
    return jsonify({"success": True, "message": "Report queued for sending"})


@app.route("/api/v1/settings", methods=["GET"])
def api_get_settings():
    """Get settings (without passwords)."""
    settings = {
        "sender_email": config.EMAIL_CONFIG.get("sender_email", ""),
        "advisor_email": config.EMAIL_CONFIG.get("class_advisor_email", ""),
        "hod_email": config.EMAIL_CONFIG.get("hod_email", ""),
        "enabled": config.EMAIL_CONFIG.get("enabled", False),
        "class_name": config.ATTENDANCE_CONFIG.get("class_name", "")
    }
    return jsonify(settings)


@app.route("/api/v1/settings", methods=["POST"])
@require_json
def api_save_settings():
    """Save settings to database."""
    data = request.json
    
    sender_email = _sanitize_string(data.get("sender_email", ""), 100)
    advisor_email = _sanitize_string(data.get("advisor_email", ""), 100)
    hod_email = _sanitize_string(data.get("hod_email", ""), 100)
    class_name = _sanitize_string(data.get("class_name", ""), 50)
    enabled = bool(data.get("enabled", False))
    
    settings = [
        ("smtp_user", sender_email),
        ("advisor_email", advisor_email),
        ("hod_email", hod_email),
        ("class_name", class_name),
        ("email_enabled", "1" if enabled else "0")
    ]
    
    for key, value in settings:
        database.set_setting(key, value)
    
    return jsonify({"success": True, "message": "Settings saved"})


@app.route("/register")
def register_page():
    """Registration page."""
    return render_template("register.html")


@app.route("/analytics")
def analytics_page():
    """Analytics dashboard page."""
    return render_template("analytics.html")


@app.route("/api/v1/register/upload", methods=["POST"])
def api_register_upload():
    """Handle registration with image upload."""
    try:
        name = _sanitize_string(request.form.get("name", ""), 50)
        roll = _sanitize_string(request.form.get("roll", ""), 30)
        role = request.form.get("role", "student")
        email = _sanitize_string(request.form.get("email", ""), 100)
        
        if not name or not roll:
            return jsonify({"success": False, "error": "Name and roll number required"})
        
        if role not in ("student", "teacher"):
            role = "student"
        
        people = database.get_active_people()
        for p in people:
            if p.get('name', '').lower() == name.lower():
                return jsonify({"success": False, "error": f"Name '{name}' already registered"})
            if (p.get('roll_number') or '').lower() == roll.lower():
                return jsonify({"success": False, "error": f"Roll number '{roll}' already registered"})
        
        person_id = database.add_person(name, role, roll, email if email else None)
        if person_id is None:
            return jsonify({"success": False, "error": "Failed to add person to database"})
        
        safe_name = name.replace(" ", "_").lower()
        person_dir = config.DATASET_DIR / f"{safe_name}_{roll}_{role}"
        person_dir.mkdir(exist_ok=True)
        
        images = request.files.getlist("images")
        saved_count = 0
        
        for i, img_file in enumerate(images[:50]):
            if img_file and img_file.filename:
                try:
                    img_bytes = img_file.read()
                    img = Image.open(io.BytesIO(img_bytes)).convert('L')
                    img = img.resize((200, 200))
                    
                    filename = f"{safe_name}_{roll}_{i}.jpg"
                    filepath = person_dir / filename
                    img.save(str(filepath), "JPEG")
                    saved_count += 1
                    logger.info(f"Saved image: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to save image {i}: {e} - {img_file.filename}")
        
        if saved_count < 5:
            database.remove_person(name)
            shutil.rmtree(person_dir, ignore_errors=True)
            return jsonify({"success": False, "error": f"Need at least 5 images, got {saved_count}"})
        
        import train
        training_success = train.train_model()
        
        try:
            engine = attendance_engine.get_engine()
            engine.reload_faces()
        except:
            pass
        
        return jsonify({
            "success": True,
            "name": name,
            "person_id": person_id,
            "image_count": saved_count,
            "training": training_success
        })
        
    except Exception as e:
        logger.exception(f"Registration error: {e}")
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Smart Attendance System - Web Dashboard")
    print("\n" + "=" * 60)
    print("   SMART ATTENDANCE SYSTEM - Web Dashboard")
    print("=" * 60)
    print(f"   -> Dashboard: http://localhost:{config.FLASK_PORT}")
    print(f"   -> API: http://localhost:{config.FLASK_PORT}/api")
    print(f"   -> Debug: {config.FLASK_DEBUG}")
    print("=" * 60 + "\n")
    
    database.init_database()
    
    run_debug = config.FLASK_DEBUG and not config.FLASK_HOST == "0.0.0.0"
    
    app.run(
        debug=run_debug,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        use_reloader=False,
        threaded=True
    )
