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


def _parse_timestamp(ts_str):
    """Parse timestamp string, handling multiple formats."""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except (ValueError, TypeError):
            pass
    return None


def show_menu():
    """Display main menu."""
    try:
        stats = database.get_stats()
        batch = database.get_batch_progress()
    except Exception as e:
        logger.warning(f"Could not fetch stats: {e}")
        stats = {}
        batch = None
    
    print("\n" + "="*60)
    print("   SMART ATTENDANCE SYSTEM v2")
    print("="*60)
    
    if batch:
        print(f"Batch: Day {batch.get('days_elapsed', '?')}/30 | Ends: {batch.get('end_date', 'N/A')}")
    else:
        print("Batch: No active batch")
    
    try:
        engine = attendance_engine.get_engine()
        mode = engine.mode.upper()
        registered = engine.get_status().get('registered', 0)
    except Exception:
        mode = "N/A"
        registered = 0
    
    print(f"Registered: {registered} | Present: {stats.get('present_today', 0)}")
    print(f"Mode: {mode}")
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
    """View today's attendance."""
    try:
        attendance = database.get_today_attendance()
        stats = database.get_stats()
    except Exception as e:
        logger.error(f"Could not fetch attendance: {e}")
        return
    
    print("\n" + "="*60)
    print(f"  TODAY'S ATTENDANCE - {date.today().strftime('%d %b %Y')}")
    print("="*60)
    
    if not attendance:
        print("No records today.")
        return
    
    print(f"Present: {stats.get('present_today', 0)} | Rate: {stats.get('attendance_rate', 0)}%\n")
    
    for i, record in enumerate(attendance, 1):
        name = record.get('name', '-') if isinstance(record, dict) else '-'
        roll = record.get('roll_number') if isinstance(record, dict) else '-'
        time_in = record.get('time_in', '-') if isinstance(record, dict) else '-'
        print(f"{i}. {name} ({roll or '-'}) - {time_in}")


def view_alerts():
    """View recent alerts."""
    try:
        alerts = database.get_recent_alerts(10)
    except Exception as e:
        logger.error(f"Could not fetch alerts: {e}")
        return
    
    print("\n" + "="*60)
    print("  RECENT ALERTS")
    print("="*60)
    
    if not alerts:
        print("No alerts.")
        return
    
    for alert in alerts:
        ts_str = alert.get('timestamp', '') if isinstance(alert, dict) else ''
        alert_id = alert.get('alert_id', '') if isinstance(alert, dict) else ''
        sent = alert.get('alert_sent', 0) if isinstance(alert, dict) else 0
        
        ts = _parse_timestamp(ts_str)
        ts_str_fmt = ts.strftime('%d %b %H:%M') if ts else ts_str[:16]
        print(f"[{ts_str_fmt}] {alert_id or 'ALERT'} - {'SENT' if sent else 'FAILED'}")


def main():
    """Main application."""
    logger.info("Starting Smart Attendance System v2")
    
    try:
        database.init_database()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    try:
        batch = database.get_active_batch()
        if not batch:
            batch_id = database.create_batch()
            logger.info(f"New batch created (ID: {batch_id})")
    except Exception as e:
        logger.error(f"Could not create batch: {e}")
    
    try:
        scheduler.init_scheduler()
        logger.info("Scheduler started")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")
    
    try:
        engine = attendance_engine.get_engine()
        status = engine.get_status()
        logger.info(f"Engine ready ({status.get('registered', 0)} registered)")
    except Exception as e:
        logger.error(f"Could not initialize engine: {e}")
        engine = None
    
    while True:
        try:
            show_menu()
            choice = input("\nChoice: ").strip()
            
            if choice not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'):
                print("Invalid choice. Please enter 1-11.")
                input("\nPress Enter...")
                continue
            
            if choice == '1':
                if engine:
                    engine.marked_today = set()
                    engine.start_camera(mode="attendance")
            elif choice == '2':
                if engine:
                    engine.start_camera(mode="monitoring")
            elif choice == '3':
                if engine:
                    engine.stop_camera()
            elif choice == '4':
                from register_faces import register_person_webcam
                register_person_webcam()
            elif choice == '5':
                from train import train_model
                train_model()
            elif choice == '6':
                try:
                    pdf_path = pdf_generator.generate_daily_report()
                    email_sender.send_daily_report(None, pdf_path)
                except Exception as e:
                    logger.error(f"Daily report failed: {e}")
            elif choice == '7':
                try:
                    pdf_path = pdf_generator.generate_monthly_report()
                    if pdf_path:
                        email_sender.send_monthly_report(pdf_path)
                except Exception as e:
                    logger.error(f"Monthly report failed: {e}")
            elif choice == '8':
                view_today()
            elif choice == '9':
                view_alerts()
            elif choice == '10':
                email_sender.test_email()
            elif choice == '11':
                if engine:
                    engine.stop_camera()
                scheduler.stop_scheduler()
                logger.info("Shutting down")
                break
            
            input("\nPress Enter...")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            if engine:
                engine.stop_camera()
            scheduler.stop_scheduler()
            break
        except EOFError:
            break
        except Exception as e:
            logger.exception(f"Menu error: {e}")
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
