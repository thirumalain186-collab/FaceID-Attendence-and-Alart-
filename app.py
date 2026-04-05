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
from attendance_engine import AttendanceSystem
from email_alert import send_daily_report, test_email_connection
from register_faces import register_person, list_registered_people, remove_person

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

attendance_sys = None
camera_thread = None


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(str(config.DB_PATH))


def get_stats():
    """Get dashboard statistics"""
    today = date.today().isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    present_today = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM people")
    total_people = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM people WHERE role='student'")
    total_students = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND role='student'", (today,))
    present_students = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM alerts WHERE DATE(timestamp)=?", (today,))
    alerts_today = c.fetchone()[0] or 0
    
    conn.close()
    
    attendance_rate = round((present_students / total_students * 100), 1) if total_students > 0 else 0
    
    return {
        "present_today": present_today,
        "total_people": total_people,
        "total_students": total_students,
        "present_students": present_students,
        "alerts_today": alerts_today,
        "attendance_rate": attendance_rate,
        "date": today
    }


@app.route("/")
def index():
    """Dashboard home page"""
    stats = get_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/api/stats")
def api_stats():
    """API endpoint for statistics"""
    return jsonify(get_stats())


@app.route("/api/attendance/today")
def api_today_attendance():
    """Get today's attendance records"""
    today = date.today().isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, role, class_name, time_in, status
        FROM attendance WHERE date=? ORDER BY time_in
    """, (today,))
    records = [
        {"name": r[0], "role": r[1], "class": r[2], "time": r[3], "status": r[4]}
        for r in c.fetchall()
    ]
    conn.close()
    return jsonify(records)


@app.route("/api/people")
def api_people():
    """Get all registered people"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, role, roll_number, class_name, registered_at
        FROM people ORDER BY role, name
    """)
    people = [
        {"id": r[0], "name": r[1], "role": r[2], "roll": r[3], "class": r[4], "registered": r[5]}
        for r in c.fetchall()
    ]
    conn.close()
    return jsonify(people)


@app.route("/api/camera/start", methods=["POST"])
def start_camera():
    """Start camera in background thread"""
    global attendance_sys, camera_thread
    
    if attendance_sys and attendance_sys.running:
        return jsonify({"status": "already_running"})
    
    attendance_sys = AttendanceSystem()
    
    def run():
        attendance_sys.run_camera(display=False)
    
    camera_thread = threading.Thread(target=run, daemon=True)
    camera_thread.start()
    
    return jsonify({"status": "started"})


@app.route("/api/camera/stop", methods=["POST"])
def stop_camera():
    """Stop camera"""
    global attendance_sys
    
    if attendance_sys:
        attendance_sys.running = False
    
    return jsonify({"status": "stopped"})


@app.route("/api/reports/export")
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


@app.route("/api/email/test", methods=["POST"])
def api_test_email():
    """Test email configuration"""
    success = test_email_connection()
    return jsonify({"success": success})


@app.route("/api/email/send_report", methods=["POST"])
def api_send_report():
    """Send daily report"""
    success = send_daily_report()
    return jsonify({"success": success})


@app.route("/api/settings", methods=["GET"])
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


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    """Save email settings"""
    data = request.json
    
    config.EMAIL_CONFIG["sender_email"] = data.get("sender_email", "")
    config.EMAIL_CONFIG["sender_password"] = data.get("sender_password", "")
    config.EMAIL_CONFIG["class_advisor_email"] = data.get("advisor_email", "")
    config.EMAIL_CONFIG["hod_email"] = data.get("hod_email", "")
    config.EMAIL_CONFIG["enabled"] = data.get("enabled", False)
    config.ATTENDANCE_CONFIG["class_name"] = data.get("class_name", "")
    
    # Save to database
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
    print("\n" + "=" * 60)
    print("   SMART ATTENDANCE SYSTEM - Web Dashboard")
    print("=" * 60)
    print(f"   → Dashboard: http://localhost:{config.FLASK_PORT}")
    print(f"   → API: http://localhost:{config.FLASK_PORT}/api")
    print("=" * 60 + "\n")
    
    # Initialize database
    from attendance_engine import AttendanceRecorder
    AttendanceRecorder()
    
    app.run(
        debug=True,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        use_reloader=False
    )
