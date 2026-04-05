"""
Main Entry Point for Smart Attendance System v2
"""

import sys
from datetime import datetime, date
import config
import database
import attendance_engine
import scheduler
import email_sender
import pdf_generator
from logger import get_logger

logger = get_logger()


def show_menu():
    """Display main menu"""
    stats = database.get_stats()
    batch = database.get_batch_progress()
    
    print("\n" + "="*60)
    print("   SMART ATTENDANCE SYSTEM v2")
    print("="*60)
    
    if batch:
        print(f"Batch: Day {batch['days_elapsed']}/30 | Ends: {batch['end_date']}")
    else:
        print("Batch: No active batch")
    
    engine = attendance_engine.get_engine()
    print(f"Registered: {stats['total_people']} | Present: {stats['present_today']}")
    print(f"Mode: {engine.mode.upper()}")
    print("="*60)
    
    print("\n1. Start Attendance Mode")
    print("2. Start Monitoring Mode")
    print("3. Stop Camera")
    print("4. Register New Person")
    print("5. Train Model")
    print("6. Send Daily Report")
    print("7. Send Monthly Report")
    print("8. View Today's Attendance")
    print("9. View Alerts")
    print("10. Test Email")
    print("11. Exit")


def view_today():
    """View today's attendance"""
    attendance = database.get_today_attendance()
    stats = database.get_stats()
    
    print("\n" + "="*60)
    print(f"  TODAY'S ATTENDANCE - {date.today().strftime('%d %b %Y')}")
    print("="*60)
    
    if not attendance:
        print("No records today.")
        return
    
    print(f"Present: {stats['present_today']} | Rate: {stats['attendance_rate']}%\n")
    
    for i, record in enumerate(attendance, 1):
        print(f"{i}. {record[2]} ({record[3] or '-'}) - {record[5]}")


def view_alerts():
    """View recent alerts"""
    alerts = database.get_recent_alerts(10)
    
    print("\n" + "="*60)
    print("  RECENT ALERTS")
    print("="*60)
    
    if not alerts:
        print("No alerts.")
        return
    
    for alert in alerts:
        ts = datetime.strptime(alert[1], "%Y-%m-%dT%H:%M:%S.%f")
        print(f"[{ts.strftime('%d %b %H:%M')}] {alert[7] or 'ALERT'} - {'SENT' if alert[6] else 'FAILED'}")


def main():
    """Main application"""
    logger.info("Starting Smart Attendance System v2")
    
    database.init_database()
    
    batch = database.get_active_batch()
    if not batch:
        batch_id = database.create_batch()
        logger.info(f"New batch created (ID: {batch_id})")
    
    scheduler.init_scheduler()
    logger.info("Scheduler started")
    
    engine = attendance_engine.get_engine()
    logger.info(f"Engine ready ({len(engine.label_names)} registered)")
    
    while True:
        try:
            show_menu()
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                engine.marked_today = set()
                engine.start_camera(mode="attendance")
            elif choice == '2':
                engine.start_camera(mode="monitoring")
            elif choice == '3':
                engine.stop_camera()
            elif choice == '4':
                from register_faces import register_person_webcam
                register_person_webcam()
            elif choice == '5':
                from train import train_model
                train_model()
            elif choice == '6':
                pdf_path = pdf_generator.generate_daily_report()
                email_sender.send_daily_report(None, pdf_path)
            elif choice == '7':
                pdf_path = pdf_generator.generate_monthly_report()
                if pdf_path:
                    email_sender.send_monthly_report(pdf_path)
            elif choice == '8':
                view_today()
            elif choice == '9':
                view_alerts()
            elif choice == '10':
                email_sender.test_email()
            elif choice == '11':
                scheduler.stop_scheduler()
                engine.stop_camera()
                logger.info("Shutting down")
                break
            
            input("\nPress Enter...")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            scheduler.stop_scheduler()
            engine.stop_camera()
            break


if __name__ == "__main__":
    main()
