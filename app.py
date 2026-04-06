"""
Smart Attendance System - Web Dashboard
Optional Flask-based web interface for attendance management
"""

from flask import Flask, render_template, jsonify, request, Response
import threading
import sqlite3
import os
import io
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import config
import database
import email_sender
from logger import get_logger

logger = get_logger()

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

attendance_sys = None
camera_thread = None


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(str(config.DB_PATH))


def get_stats():
    """Get dashboard statistics"""
    return database.get_stats()


@app.route("/")
def index():
    """Dashboard home page"""
    stats = get_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/api/v1/health")
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/api/v1/stats")
def api_stats():
    """API endpoint for statistics"""
    return jsonify(get_stats())


@app.route("/api/v1/attendance/today")
def api_today_attendance():
    """Get today's attendance records"""
    today = date.today().isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, roll_number, date, time_in, status
        FROM attendance WHERE date=? ORDER BY time_in
    """, (today,))
    records = [
        {"name": r[0], "roll": r[1], "date": r[2], "time": r[3], "status": r[4]}
        for r in c.fetchall()
    ]
    conn.close()
    return jsonify({"data": records, "count": len(records)})


@app.route("/api/v1/people")
def api_people():
    """Get all registered people"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, role, roll_number, class_name, registered_at
        FROM people WHERE active=1 ORDER BY role, name
    """)
    people = [
        {"id": r[0], "name": r[1], "role": r[2], "roll": r[3], "class": r[4], "registered": r[5]}
        for r in c.fetchall()
    ]
    conn.close()
    return jsonify({"data": people, "count": len(people)})


@app.route("/api/v1/camera/start", methods=["POST"])
def start_camera():
    """Start camera in background thread"""
    from attendance_engine import get_engine
    
    engine = get_engine()
    
    if engine.running:
        return jsonify({"status": "already_running"})
    
    mode = request.json.get("mode", "attendance")
    demo_mode = request.json.get("demo", False)
    headless = request.json.get("headless", False)
    
    if headless:
        engine.start_camera(mode=mode, demo_mode=True)
        engine.demo_mode = "headless"
    elif demo_mode:
        engine.start_camera(mode=mode, demo_mode=True)
    else:
        engine.start_camera(mode=mode, demo_mode=False)
    
    return jsonify({
        "status": "started", 
        "mode": mode, 
        "demo": engine.demo_mode == True,
        "headless": engine.demo_mode == "headless"
    })


@app.route("/api/v1/camera/stop", methods=["POST"])
def stop_camera():
    """Stop camera"""
    from attendance_engine import get_engine
    
    engine = get_engine()
    engine.stop_camera()
    
    return jsonify({"status": "stopped"})


@app.route("/api/v1/reports/export")
def export_report():
    """Export attendance to CSV"""
    start = request.args.get("start", (date.today() - timedelta(days=7)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, role, class_name, date, time_in, status
        FROM attendance WHERE date BETWEEN ? AND ? ORDER BY date, time_in
    """, (start, end))
    records = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Role", "Class", "Date", "Time", "Status"])
    writer.writerows(records)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{start}_to_{end}.csv"}
    )


@app.route("/api/v1/email/test", methods=["POST"])
def api_test_email():
    """Test email configuration"""
    success = email_sender.test_email()
    return jsonify({"success": success})


@app.route("/api/v1/email/send-report", methods=["POST"])
def api_send_report():
    """Send daily report"""
    import pdf_generator
    pdf_path = pdf_generator.generate_daily_report()
    email_sender.send_daily_report(None, pdf_path)
    return jsonify({"success": True})


@app.route("/api/v1/settings", methods=["GET"])
def api_get_settings():
    """Get email settings"""
    settings = {
        "sender_email": config.EMAIL_CONFIG.get("sender_email", ""),
        "advisor_email": config.EMAIL_CONFIG.get("class_advisor_email", ""),
        "hod_email": config.EMAIL_CONFIG.get("hod_email", ""),
        "enabled": config.EMAIL_CONFIG.get("enabled", False),
        "class_name": config.ATTENDANCE_CONFIG.get("class_name", "")
    }
    return jsonify(settings)


@app.route("/api/v1/settings", methods=["POST"])
def api_save_settings():
    """Save email settings"""
    data = request.json
    
    config.EMAIL_CONFIG["sender_email"] = data.get("sender_email", "")
    config.EMAIL_CONFIG["sender_password"] = data.get("sender_password", "")
    config.EMAIL_CONFIG["class_advisor_email"] = data.get("advisor_email", "")
    config.EMAIL_CONFIG["hod_email"] = data.get("hod_email", "")
    config.EMAIL_CONFIG["enabled"] = data.get("enabled", False)
    config.ATTENDANCE_CONFIG["class_name"] = data.get("class_name", "")
    
    conn = get_db_connection()
    c = conn.cursor()
    settings = [
        ("smtp_user", data.get("sender_email", "")),
        ("advisor_email", data.get("advisor_email", "")),
        ("hod_email", data.get("hod_email", ""))
    ]
    for key, value in settings:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


if __name__ == "__main__":
    logger.info("Starting Smart Attendance System - Web Dashboard")
    print("\n" + "=" * 60)
    print("   SMART ATTENDANCE SYSTEM - Web Dashboard")
    print("=" * 60)
    print(f"   -> Dashboard: http://localhost:{config.FLASK_PORT}")
    print(f"   -> API: http://localhost:{config.FLASK_PORT}/api")
    print("=" * 60 + "\n")
    
    database.init_database()
    
    app.run(
        debug=True,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        use_reloader=False
    )
