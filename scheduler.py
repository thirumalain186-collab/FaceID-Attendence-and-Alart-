"""
Scheduler Module for Smart Attendance System v2
APScheduler for automated daily tasks
"""

import threading
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import config
import database
import email_sender
import pdf_generator
import attendance_engine


# Global scheduler instance
scheduler = None


def start_attendance_mode():
    """Start camera in attendance marking mode (9:00 AM)"""
    print("\n" + "="*50)
    print("[SCHEDULER] Starting ATTENDANCE mode (9:00 AM)")
    print("="*50)
    
    engine = attendance_engine.get_engine()
    engine.marked_today = set()  # Reset marked list
    engine.start_camera(mode="attendance")
    
    print("[SCHEDULER] Attendance mode active - will mark students present")


def stop_attendance_send_report():
    """Stop attendance mode and send daily report (9:30 AM)"""
    print("\n" + "="*50)
    print("[SCHEDULER] Stopping ATTENDANCE mode (9:30 AM)")
    print("[SCHEDULER] Sending daily report...")
    print("="*50)
    
    engine = attendance_engine.get_engine()
    
    # Stop attendance mode
    if engine.running:
        engine.stop_camera()
    
    # Switch to monitoring mode
    threading.Event().wait(2)  # Brief pause
    engine.start_camera(mode="monitoring")
    
    # Generate and send daily report
    try:
        csv_path = generate_csv_report()
        pdf_path = pdf_generator.generate_daily_report()
        email_sender.send_daily_report(csv_path, pdf_path)
        print("[SCHEDULER] Daily report sent successfully")
    except Exception as e:
        print(f"[SCHEDULER] Error sending report: {e}")


def stop_camera_end_day():
    """Stop camera at end of day (4:30 PM)"""
    print("\n" + "="*50)
    print("[SCHEDULER] End of day (4:30 PM)")
    print("[SCHEDULER] Stopping camera...")
    print("="*50)
    
    engine = attendance_engine.get_engine()
    
    if engine.running:
        engine.stop_camera()
    
    # Generate end of day report
    try:
        pdf_path = pdf_generator.generate_end_of_day_report()
        print(f"[SCHEDULER] End of day report: {pdf_path}")
    except Exception as e:
        print(f"[SCHEDULER] Error generating report: {e}")


def check_batch_expiry():
    """Check if batch is expiring and send reminders"""
    batch_progress = database.get_batch_progress()
    
    if not batch_progress:
        return
    
    # Send reminder at 5 days remaining
    if batch_progress['days_remaining'] == 5:
        print("[SCHEDULER] Batch expiring in 5 days - sending reminder")
        email_sender.send_batch_ending_reminder(5)
    
    # Send reminder at 1 day remaining
    elif batch_progress['days_remaining'] == 1:
        print("[SCHEDULER] Batch expiring tomorrow - sending reminder")
        email_sender.send_batch_ending_reminder(1)


def handle_batch_expiry():
    """Handle 30-day batch expiry"""
    batch = database.get_active_batch()
    
    if not batch or not batch[4]:  # No active batch
        return
    
    batch_progress = database.get_batch_progress()
    
    if batch_progress and batch_progress['is_last_day']:
        print("\n" + "="*50)
        print("[SCHEDULER] 30-DAY BATCH EXPIRED!")
        print("[SCHEDULER] Generating monthly report...")
        print("="*50)
        
        # Stop camera if running
        engine = attendance_engine.get_engine()
        if engine.running:
            engine.stop_camera()
        
        # Generate monthly report
        try:
            pdf_path = pdf_generator.generate_monthly_report()
            if pdf_path:
                email_sender.send_monthly_report(pdf_path)
                print("[SCHEDULER] Monthly report sent")
        except Exception as e:
            print(f"[SCHEDULER] Error generating monthly report: {e}")
        
        # Send renewal reminder
        try:
            email_sender.send_renewal_reminder()
            print("[SCHEDULER] Renewal reminder sent")
        except Exception as e:
            print(f"[SCHEDULER] Error sending renewal reminder: {e}")
        
        # Close batch
        database.close_batch(batch[0])
        print("[SCHEDULER] Batch closed")


def generate_csv_report():
    """Generate CSV report for today"""
    from pathlib import Path
    import csv
    
    today = date.today()
    attendance = database.get_today_attendance()
    
    csv_path = config.REPORTS_DIR / f"attendance_{today.strftime('%Y%m%d')}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['S.No', 'Name', 'Roll No', 'Date', 'Time In', 'Status'])
        
        for i, record in enumerate(attendance, 1):
            writer.writerow([
                i,
                record[2],
                record[3] or '-',
                today.strftime('%Y-%m-%d'),
                record[5],
                'Present'
            ])
    
    return str(csv_path)


def init_scheduler():
    """Initialize and start the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        print("[SCHEDULER] Already running")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # Parse schedule times
    attendance_start_hour, attendance_start_min = map(int, config.SCHEDULE_CONFIG["attendance_start"].split(':'))
    attendance_stop_hour, attendance_stop_min = map(int, config.SCHEDULE_CONFIG["attendance_stop"].split(':'))
    day_end_hour, day_end_min = map(int, config.SCHEDULE_CONFIG["day_end"].split(':'))
    
    # Schedule attendance start (9:00 AM)
    scheduler.add_job(
        start_attendance_mode,
        CronTrigger(hour=attendance_start_hour, minute=attendance_start_min),
        id='start_attendance',
        name='Start Attendance Mode'
    )
    
    # Schedule attendance stop and report (9:30 AM)
    scheduler.add_job(
        stop_attendance_send_report,
        CronTrigger(hour=attendance_stop_hour, minute=attendance_stop_min),
        id='stop_attendance',
        name='Stop Attendance & Send Report'
    )
    
    # Schedule end of day (4:30 PM)
    scheduler.add_job(
        stop_camera_end_day,
        CronTrigger(hour=day_end_hour, minute=day_end_min),
        id='end_day',
        name='End of Day'
    )
    
    # Check batch expiry (every day at 8:00 AM)
    scheduler.add_job(
        handle_batch_expiry,
        CronTrigger(hour=8, minute=0),
        id='check_batch',
        name='Check Batch Expiry'
    )
    
    # Check batch reminders (every day at 8:30 AM)
    scheduler.add_job(
        check_batch_expiry,
        CronTrigger(hour=8, minute=30),
        id='batch_reminder',
        name='Batch Reminder Check'
    )
    
    scheduler.start()
    print("[SCHEDULER] APScheduler started")
    print(f"[SCHEDULER] Attendance starts: {config.SCHEDULE_CONFIG['attendance_start']}")
    print(f"[SCHEDULER] Attendance stops: {config.SCHEDULE_CONFIG['attendance_stop']}")
    print(f"[SCHEDULER] Day ends: {config.SCHEDULE_CONFIG['day_end']}")
    
    return scheduler


def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        print("[SCHEDULER] Stopped")


def get_scheduler_status():
    """Get scheduler status"""
    if not scheduler:
        return {'running': False, 'jobs': []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        'running': scheduler.running,
        'jobs': jobs
    }


if __name__ == "__main__":
    print("Scheduler Module Ready")
    init_scheduler()
