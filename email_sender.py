"""
Email Sender Module for Smart Attendance System v2
All email sending functions with threading support
"""

import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from pathlib import Path
from datetime import datetime, date
import config
import database
from logger import get_logger

logger = get_logger()


def send_email_async(func):
    """Decorator to run email functions in background thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    wrapper.__wrapped__ = func
    return wrapper


def get_email_config():
    """Get email configuration"""
    email_config = config.EMAIL_CONFIG.copy()
    
    # Override with database settings if available
    sender = database.get_setting("smtp_user")
    if sender:
        email_config["sender_email"] = sender
    
    password = database.get_setting("smtp_pass")
    if password:
        email_config["sender_password"] = password
    
    advisor = database.get_setting("advisor_email")
    if advisor:
        email_config["class_advisor_email"] = advisor
    
    hod = database.get_setting("hod_email")
    if hod:
        email_config["hod_email"] = hod
    
    return email_config


def get_recipients():
    """Get email recipients list"""
    recipients = []
    email_config = get_email_config()
    
    if email_config.get("class_advisor_email"):
        recipients.append(email_config["class_advisor_email"])
    if email_config.get("hod_email"):
        recipients.append(email_config["hod_email"])
    
    return recipients


def create_email_message(subject, recipients, html_body, attachments=None):
    """Create email message with attachments"""
    email_config = get_email_config()
    
    msg = MIMEMultipart()
    msg['From'] = email_config["sender_email"]
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))
    
    if attachments:
        for filepath, filename in attachments:
            if Path(filepath).exists():
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(part)
    
    return msg


def send_email(msg):
    """Send email via SMTP"""
    email_config = get_email_config()
    
    if not email_config["enabled"]:
        logger.warning("Email disabled")
        return False
    
    if not email_config["sender_email"] or email_config["sender_email"] == "your_email@gmail.com":
        logger.warning("Email not configured")
        return False
    
    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["sender_email"], email_config["sender_password"])
            server.send_message(msg)
        logger.info("Email sent successfully")
        return True
    except Exception as e:
        logger.exception(f"Email error: {e}")
        return False


@send_email_async
def send_unknown_alert(image_path, pdf_path=None):
    """
    Send instant alert email when unknown person detected
    """
    recipients = get_recipients()
    if not recipients:
        logger.warning("No email recipients configured")
        return
    
    timestamp = datetime.now()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG["class_name"]
    
    # Save alert to database
    alert_db_id, alert_id = database.save_alert(image_path, pdf_path or "", class_name)
    
    subject = f"ALERT: Unauthorized Person in {class_name} - {timestamp.strftime('%I:%M %p')}"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">SECURITY ALERT</h2>
            <p style="margin: 5px 0 0;">Unauthorized Person Detected</p>
        </div>
        <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd;">
            <table style="width: 100%;">
                <tr><td><strong>Date:</strong></td><td>{timestamp.strftime('%d %B %Y')}</td></tr>
                <tr><td><strong>Time:</strong></td><td>{timestamp.strftime('%I:%M %p')}</td></tr>
                <tr><td><strong>Location:</strong></td><td>{class_name}</td></tr>
                <tr><td><strong>Alert ID:</strong></td><td>{alert_id}</td></tr>
            </table>
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">
                <strong>Action Required:</strong>
                <p>Please review the attached photo and take appropriate action.</p>
            </div>
        </div>
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; font-size: 12px;">
            Smart Attendance System - Automated Alert
        </div>
    </body>
    </html>
    """
    
    attachments = []
    if image_path and Path(image_path).exists():
        attachments.append((image_path, f"intruder_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"))
    if pdf_path and Path(pdf_path).exists():
        attachments.append((pdf_path, f"alert_report_{alert_id}.pdf"))
    
    msg = create_email_message(subject, recipients, html_body, attachments)
    
    if send_email(msg):
        database.mark_alert_sent(alert_db_id)
        logger.info(f"Security alert sent to {', '.join(recipients)}")
    else:
        logger.error("Failed to send security alert")


@send_email_async
def send_daily_report(csv_path=None, pdf_path=None):
    """
    Send daily attendance report email
    """
    recipients = get_recipients()
    if not recipients:
        logger.warning("No email recipients configured")
        return
    
    today = date.today()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG["class_name"]
    
    # Get today's stats
    stats = database.get_stats()
    attendance = database.get_today_attendance()
    
    subject = f"Daily Attendance Report - {class_name} ({today.strftime('%d %b %Y')})"
    
    # Build attendance table
    rows_html = ""
    for i, record in enumerate(attendance, 1):
        rows_html += f"<tr><td>{i}</td><td>{record[2]}</td><td>{record[3] or '-'}</td><td>{record[5]}</td><td>Present</td></tr>"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial; max-width: 800px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a237e, #3949ab); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Daily Attendance Report</h2>
            <p style="margin: 5px 0 0;">{class_name} - {today.strftime('%d %B %Y')}</p>
        </div>
        <div style="background: #f9f9f9; padding: 20px;">
            <h3>Summary</h3>
            <table style="width: 100%;">
                <tr><td>Total Present:</td><td><strong>{stats['present_today']}</strong></td></tr>
                <tr><td>Students:</td><td><strong>{stats['present_students']}/{stats['total_students']}</strong></td></tr>
                <tr><td>Attendance Rate:</td><td><strong>{stats['attendance_rate']}%</strong></td></tr>
            </table>
            <h3>Present Students</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #1a237e; color: white;">
                    <th style="padding: 10px;">S.No</th>
                    <th style="padding: 10px;">Name</th>
                    <th style="padding: 10px;">Roll No</th>
                    <th style="padding: 10px;">Time</th>
                    <th style="padding: 10px;">Status</th>
                </tr>
                {rows_html or '<tr><td colspan="5" style="padding: 20px; text-align: center;">No attendance records</td></tr>'}
            </table>
        </div>
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; font-size: 12px;">
            Smart Attendance System - Automated Report
        </div>
    </body>
    </html>
    """
    
    attachments = []
    if csv_path and Path(csv_path).exists():
        attachments.append((csv_path, f"attendance_{today.strftime('%Y%m%d')}.csv"))
    if pdf_path and Path(pdf_path).exists():
        attachments.append((pdf_path, f"attendance_report_{today.strftime('%Y%m%d')}.pdf"))
    
    msg = create_email_message(subject, recipients, html_body, attachments)
    
    if send_email(msg):
        logger.info(f"Daily report sent to {', '.join(recipients)}")
    else:
        logger.error("Failed to send daily report")


@send_email_async
def send_monthly_report(pdf_path):
    """
    Send 30-day monthly report email
    """
    recipients = get_recipients()
    if not recipients:
        logger.warning("No email recipients configured")
        return
    
    if not pdf_path or not Path(pdf_path).exists():
        logger.error("PDF path not provided or file not found")
        return
    
    today = date.today()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG["class_name"]
    batch = database.get_active_batch()
    
    if batch:
        start_date = datetime.strptime(batch[1], "%Y-%m-%d").date()
        month_name = start_date.strftime("%B %Y")
    else:
        month_name = today.strftime("%B %Y")
    
    subject = f"Monthly Attendance Report - {class_name} ({month_name})"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a237e, #3949ab); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Monthly Attendance Report</h2>
            <p style="margin: 5px 0 0;">{class_name} - {month_name}</p>
        </div>
        <div style="background: #f9f9f9; padding: 20px;">
            <p>Please find attached the comprehensive monthly attendance report for {month_name}.</p>
            <p>The report includes:</p>
            <ul>
                <li>Full attendance table with present/absent days</li>
                <li>Attendance percentage per student</li>
                <li>Security alerts log</li>
                <li>Movement summary</li>
            </ul>
            <p><strong>Note:</strong> Students with attendance below 75% are highlighted in red.</p>
        </div>
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; font-size: 12px;">
            Smart Attendance System - Monthly Report
        </div>
    </body>
    </html>
    """
    
    msg = create_email_message(subject, recipients, html_body, [(pdf_path, f"monthly_report_{today.strftime('%Y%m')}.pdf")])
    
    if send_email(msg):
        logger.info(f"Monthly report sent to {', '.join(recipients)}")
    else:
        logger.error("Failed to send monthly report")


@send_email_async
def send_renewal_reminder():
    """
    Send 30-day batch renewal reminder email
    """
    recipients = get_recipients()
    if not recipients:
        logger.warning("No email recipients configured")
        return
    
    today = date.today()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG["class_name"]
    
    subject = f"Registration Reminder - {class_name}"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #ff9800, #f57c00); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Registration Period Ending</h2>
            <p style="margin: 5px 0 0;">Action Required</p>
        </div>
        <div style="background: #f9f9f9; padding: 20px;">
            <p>Dear Class Advisor,</p>
            <p>The current 30-day registration batch is ending today ({today.strftime('%d %B %Y')}).</p>
            <p><strong>Action Required:</strong></p>
            <ol>
                <li>Log in to the Smart Attendance System dashboard</li>
                <li>Register new students for the next 30-day cycle</li>
                <li>Remove any students who have left</li>
            </ol>
            <p>The system will automatically create a new batch when you register the first new student.</p>
            <p>Dashboard URL: http://localhost:{config.FLASK_PORT}</p>
        </div>
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; font-size: 12px;">
            Smart Attendance System - Automated Reminder
        </div>
    </body>
    </html>
    """
    
    msg = create_email_message(subject, recipients, html_body)
    
    if send_email(msg):
        logger.info(f"Renewal reminder sent to {', '.join(recipients)}")
    else:
        logger.error("Failed to send renewal reminder")


@send_email_async
def send_batch_ending_reminder(days_remaining=5):
    """
    Send reminder email when batch is ending soon
    """
    recipients = get_recipients()
    if not recipients:
        return
    
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG["class_name"]
    
    subject = f"Attendance Batch Ending Soon - {days_remaining} Days Remaining"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto;">
        <div style="background: #ffc107; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; color: #333;">Reminder: Registration Period Ending</h2>
        </div>
        <div style="background: #f9f9f9; padding: 20px;">
            <p>The current attendance batch will end in <strong>{days_remaining} days</strong>.</p>
            <p>Please ensure all students are registered before the batch ends.</p>
            <p>Dashboard: http://localhost:{config.FLASK_PORT}</p>
        </div>
    </body>
    </html>
    """
    
    msg = create_email_message(subject, recipients, html_body)
    send_email(msg)


def test_email():
    """Test email configuration"""
    email_config = get_email_config()
    
    if not email_config["sender_email"] or email_config["sender_email"] == "your_email@gmail.com":
        logger.warning("Email not configured")
        return False
    
    msg = MIMEMultipart()
    msg['Subject'] = "Smart Attendance System - Test Email"
    msg['From'] = email_config["sender_email"]
    msg['To'] = email_config["sender_email"]
    msg.attach(MIMEText("This is a test email from Smart Attendance System v2.", "plain"))
    
    return send_email(msg)


if __name__ == "__main__":
    test_email()
