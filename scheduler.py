"""
Scheduler Module for Smart Attendance System v2
APScheduler for automated daily tasks
"""

import threading
import time
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

scheduler = None
_scheduler_lock = threading.Lock()


def start_attendance_mode():
    """Start camera in attendance marking mode (9:00 AM)."""
    logger.info("Starting ATTENDANCE mode (scheduled)")
    
    try:
        engine = attendance_engine.get_engine()
        engine.marked_today = set()
        engine.start_camera(mode="attendance")
        logger.info("Attendance mode active - marking students present")
    except Exception as e:
        logger.exception(f"Failed to start attendance mode: {e}")


def stop_attendance_send_report():
    """Stop attendance mode and send daily report (9:30 AM)."""
    logger.info("Stopping ATTENDANCE mode, sending daily report")
    
    try:
        engine = attendance_engine.get_engine()
        
        if engine.running:
            engine.stop_camera()
        
        time.sleep(2)
        engine.start_camera(mode="monitoring")
        
        csv_path = generate_csv_report()
        pdf_path = pdf_generator.generate_daily_report()
        email_sender.send_daily_report(csv_path, pdf_path)
        logger.info("Daily report sent successfully")
    except Exception as e:
        logger.exception(f"Error sending report: {e}")


def stop_camera_end_day():
    """Stop camera at end of day (4:30 PM)."""
    logger.info("End of day - stopping camera")
    
    try:
        engine = attendance_engine.get_engine()
        
        if engine.running:
            engine.stop_camera()
        
        pdf_path = pdf_generator.generate_end_of_day_report()
        logger.info(f"End of day report generated: {pdf_path}")
    except Exception as e:
        logger.exception(f"Error generating report: {e}")


def check_batch_expiry():
    """Check if batch is expiring and send reminders."""
    try:
        batch_progress = database.get_batch_progress()
        
        if not batch_progress:
            return
        
        if batch_progress['days_remaining'] == 5:
            logger.info("Batch expiring in 5 days - sending reminder")
            email_sender.send_batch_ending_reminder(5)
        
        elif batch_progress['days_remaining'] == 1:
            logger.info("Batch expiring tomorrow - sending reminder")
            email_sender.send_batch_ending_reminder(1)
    except Exception as e:
        logger.exception(f"Error in batch expiry check: {e}")


def handle_batch_expiry():
    """Handle 30-day batch expiry."""
    try:
        batch = database.get_active_batch()
        
        if not batch:
            return
        
        batch_status = batch.get('status', '')
        if not batch_status:
            return
        
        batch_progress = database.get_batch_progress()
        
        if batch_progress and batch_progress.get('is_last_day'):
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
            
            batch_id = batch.get('id')
            if batch_id:
                database.close_batch(batch_id)
                logger.info(f"Batch {batch_id} closed")
    except Exception as e:
        logger.exception(f"Error handling batch expiry: {e}")


def generate_csv_report():
    """Generate CSV report for today. Returns path or None on error."""
    import csv
    
    try:
        today = date.today()
        attendance = database.get_today_attendance()
        
        csv_path = config.REPORTS_DIR / f"attendance_{today.strftime('%Y%m%d')}.csv"
        csv_path.parent.mkdir(exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['S.No', 'Name', 'Roll No', 'Date', 'Time In', 'Status'])
            
            for i, record in enumerate(attendance, 1):
                name = record.get('name', '-') if isinstance(record, dict) else '-'
                roll = record.get('roll_number') if isinstance(record, dict) else '-'
                time_in = record.get('time_in', '-') if isinstance(record, dict) else '-'
                writer.writerow([i, name, roll, today.strftime('%Y-%m-%d'), time_in, 'Present'])
        
        logger.info(f"CSV report generated: {csv_path}")
        return str(csv_path)
    except Exception as e:
        logger.exception(f"Failed to generate CSV report: {e}")
        return None


def init_scheduler():
    """Initialize and start the scheduler."""
    global scheduler
    
    with _scheduler_lock:
        if scheduler and scheduler.running:
            logger.warning("Scheduler already running")
            return scheduler
        
        scheduler = BackgroundScheduler()
        
        try:
            attendance_start_hour, attendance_start_min = map(
                int, config.SCHEDULE_CONFIG.get("attendance_start", "09:00").split(':'))
            attendance_stop_hour, attendance_stop_min = map(
                int, config.SCHEDULE_CONFIG.get("attendance_stop", "09:30").split(':'))
            day_end_hour, day_end_min = map(
                int, config.SCHEDULE_CONFIG.get("day_end", "16:30").split(':'))
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Invalid schedule config, using defaults: {e}")
            attendance_start_hour, attendance_start_min = 9, 0
            attendance_stop_hour, attendance_stop_min = 9, 30
            day_end_hour, day_end_min = 16, 30
        
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
        logger.info(
            f"Schedule - Attendance: {config.SCHEDULE_CONFIG.get('attendance_start', '09:00')}"
            f"-{config.SCHEDULE_CONFIG.get('attendance_stop', '09:30')}, "
            f"Day ends: {config.SCHEDULE_CONFIG.get('day_end', '16:30')}"
        )
        
        return scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    with _scheduler_lock:
        if scheduler:
            try:
                scheduler.shutdown(wait=True, timeout=30)
                logger.info("Scheduler stopped gracefully")
            except Exception as e:
                logger.warning(f"Scheduler shutdown error: {e}")
            finally:
                scheduler = None


def get_scheduler_status():
    """Get scheduler status."""
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
    init_scheduler()
