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
from logger import get_logger

logger = get_logger()


# Global scheduler instance
scheduler = None


def start_attendance_mode():
    """Start camera in attendance marking mode (9:00 AM)"""
    logger.info("Starting ATTENDANCE mode (scheduled)")
    
    engine = attendance_engine.get_engine()
    engine.marked_today = set()
    engine.start_camera(mode="attendance")
    
    logger.info("Attendance mode active - marking students present")


def stop_attendance_send_report():
    """Stop attendance mode and send daily report (9:30 AM)"""
    logger.info("Stopping ATTENDANCE mode, sending daily report")
    
    engine = attendance_engine.get_engine()
    
    if engine.running:
        engine.stop_camera()
    
    threading.Event().wait(2)
    engine.start_camera(mode="monitoring")
    
    try:
        csv_path = generate_csv_report()
        pdf_path = pdf_generator.generate_daily_report()
        email_sender.send_daily_report(csv_path, pdf_path)
        logger.info("Daily report sent successfully")
    except Exception as e:
        logger.exception(f"Error sending report: {e}")


def stop_camera_end_day():
    """Stop camera at end of day (4:30 PM)"""
    logger.info("End of day - stopping camera")
    
    engine = attendance_engine.get_engine()
    
    if engine.running:
        engine.stop_camera()
    
    try:
        pdf_path = pdf_generator.generate_end_of_day_report()
        logger.info(f"End of day report generated: {pdf_path}")
    except Exception as e:
        logger.exception(f"Error generating report: {e}")


def check_batch_expiry():
    """Check if batch is expiring and send reminders"""
    batch_progress = database.get_batch_progress()
    
    if not batch_progress:
        return
    
    if batch_progress['days_remaining'] == 5:
        logger.info("Batch expiring in 5 days - sending reminder")
        email_sender.send_batch_ending_reminder(5)
    
    elif batch_progress['days_remaining'] == 1:
        logger.info("Batch expiring tomorrow - sending reminder")
        email_sender.send_batch_ending_reminder(1)


def handle_batch_expiry():
    """Handle 30-day batch expiry"""
    batch = database.get_active_batch()
    
    if not batch or not batch[4]:
        return
    
    batch_progress = database.get_batch_progress()
    
    if batch_progress and batch_progress['is_last_day']:
        logger.warning("30-DAY BATCH EXPIRED!")
        
        engine = attendance_engine.get_engine()
        if engine.running:
            engine.stop_camera()
        
        try:
            pdf_path = pdf_generator.generate_monthly_report()
            if pdf_path:
                email_sender.send_monthly_report(pdf_path)
                logger.info("Monthly report sent")
        except Exception as e:
            logger.exception(f"Error generating monthly report: {e}")
        
        try:
            email_sender.send_renewal_reminder()
            logger.info("Renewal reminder sent")
        except Exception as e:
            logger.exception(f"Error sending renewal reminder: {e}")
        
        database.close_batch(batch[0])
        logger.info("Batch closed")


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
        logger.warning("Scheduler already running")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    attendance_start_hour, attendance_start_min = map(int, config.SCHEDULE_CONFIG["attendance_start"].split(':'))
    attendance_stop_hour, attendance_stop_min = map(int, config.SCHEDULE_CONFIG["attendance_stop"].split(':'))
    day_end_hour, day_end_min = map(int, config.SCHEDULE_CONFIG["day_end"].split(':'))
    
    scheduler.add_job(
        start_attendance_mode,
        CronTrigger(hour=attendance_start_hour, minute=attendance_start_min),
        id='start_attendance',
        name='Start Attendance Mode'
    )
    
    scheduler.add_job(
        stop_attendance_send_report,
        CronTrigger(hour=attendance_stop_hour, minute=attendance_stop_min),
        id='stop_attendance',
        name='Stop Attendance & Send Report'
    )
    
    scheduler.add_job(
        stop_camera_end_day,
        CronTrigger(hour=day_end_hour, minute=day_end_min),
        id='end_day',
        name='End of Day'
    )
    
    scheduler.add_job(
        handle_batch_expiry,
        CronTrigger(hour=8, minute=0),
        id='check_batch',
        name='Check Batch Expiry'
    )
    
    scheduler.add_job(
        check_batch_expiry,
        CronTrigger(hour=8, minute=30),
        id='batch_reminder',
        name='Batch Reminder Check'
    )
    
    scheduler.start()
    logger.info("APScheduler started")
    logger.info(f"Schedule - Attendance: {config.SCHEDULE_CONFIG['attendance_start']}-{config.SCHEDULE_CONFIG['attendance_stop']}, Day ends: {config.SCHEDULE_CONFIG['day_end']}")
    
    return scheduler


def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler stopped")


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
    logger.info("Scheduler module ready")
    init_scheduler()
