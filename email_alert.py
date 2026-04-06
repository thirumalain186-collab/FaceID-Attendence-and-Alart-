"""
Email Alert System for Smart Attendance System
Sends PDF report alerts to Class Advisor and HOD
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.multipart import MIMEBase
from email.mime.image import MIMEImage
from email.encoders import encode_base64
from datetime import datetime, date
from pathlib import Path
import sqlite3
import config
import cv2
import numpy as np
from fpdf import FPDF
from logger import get_logger
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logger = get_logger()


def get_all_email_config():
    """Get email configuration from config"""
    email_config = {
        "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "sender_email": os.getenv("SENDER_EMAIL", ""),
        "sender_password": os.getenv("SENDER_PASSWORD", ""),
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587") or 587),
        "class_advisor_email": os.getenv("CLASS_ADVISOR_EMAIL", ""),
        "hod_email": os.getenv("HOD_EMAIL", ""),
    }
    return email_config


class IntruderAlertPDF(FPDF):
    """Custom PDF class for Intruder Alert Reports"""
    
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_fill_color(220, 53, 69)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'INTRUDER ALERT REPORT', 0, 1, 'C', fill=True)
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%d %b %Y %H:%M")}', 0, 0, 'R')


def create_intruder_report_pdf(image_path, timestamp, class_name, location="Main Entrance"):
    """
    Create a professional PDF report for intruder alerts
    
    Args:
        image_path: Path to the captured unknown person image
        timestamp: Detection timestamp
        class_name: Class/location name
        location: Specific location
    
    Returns:
        str: Path to the created PDF file
    """
    pdf = IntruderAlertPDF()
    pdf.add_page()
    
    # Report Title Section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(220, 53, 69)
    pdf.cell(0, 10, 'SECURITY BREACH NOTIFICATION', 0, 1, 'C')
    
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 8, 'Smart Attendance System - Automated Alert', 0, 1, 'C')
    pdf.ln(5)
    
    # Alert Details Box
    pdf.set_fill_color(255, 245, 238)
    pdf.set_draw_color(220, 53, 69)
    pdf.set_line_width(0.5)
    pdf.rect(10, pdf.get_y(), 190, 45, 'DF')
    
    pdf.set_xy(15, pdf.get_y() + 3)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    
    # Left column
    pdf.cell(90, 8, 'ALERT INFORMATION', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    
    pdf.cell(90, 7, f'  Date: {timestamp.strftime("%d %B %Y")}', 0, 1)
    pdf.cell(90, 7, f'  Time: {timestamp.strftime("%I:%M %p")}', 0, 1)
    pdf.cell(90, 7, f'  Location: {class_name}', 0, 1)
    pdf.cell(90, 7, f'  Alert ID: {timestamp.strftime("%Y%m%d%H%M%S")}', 0, 1)
    
    # Right column - Status
    pdf.set_xy(110, pdf.get_y() - 28)
    pdf.set_fill_color(220, 53, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(85, 10, '  STATUS: UNKNOWN PERSON', 0, 1, 'L', fill=True)
    
    pdf.set_xy(110, pdf.get_y())
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(85, 6, '  This individual is NOT registered in our attendance system.\n  Immediate verification required.')
    
    pdf.ln(15)
    
    # Captured Image Section
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, 'CAPTURED IMAGE (HIGH QUALITY)', 0, 1)
    
    # Add the captured image with MAXIMUM quality
    if os.path.exists(image_path):
        img = cv2.imread(image_path)
        if img is not None:
            # Improve image quality with contrast enhancement
            # Apply histogram equalization for better visibility
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Convert back to BGR for saving
            enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            # Save enhanced image at HIGH QUALITY
            enhanced_path = image_path.replace('.jpg', '_hq.jpg')
            cv2.imwrite(enhanced_path, enhanced_color, [cv2.IMWRITE_JPEG_QUALITY, 100])
            
            # Get original image dimensions
            height, width = img.shape[:2]
            
            # Calculate display size (fit to page but keep aspect ratio)
            max_display_width = 170
            max_display_height = 140
            
            aspect = width / height
            if width > height:
                display_width = min(width, max_display_width)
                display_height = int(display_width / aspect)
            else:
                display_height = min(height, max_display_height)
                display_width = int(display_height * aspect)
            
            # Center the image
            x_pos = (210 - display_width) / 2
            
            # Add to PDF
            pdf.image(enhanced_path, x=x_pos, w=display_width)
            
            # Add border
            pdf.rect(x_pos - 1, pdf.get_y() - display_height - 1, 
                    display_width + 2, display_height + 2, 'D')
            
            # Clean up
            if os.path.exists(enhanced_path):
                os.remove(enhanced_path)
                
            logger.info("High quality image added to PDF")
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(128)
        pdf.cell(0, 40, 'Image not available', 0, 1, 'C')
    
    pdf.ln(5)
    
    # Action Required Section
    pdf.ln(5)
    pdf.set_draw_color(255, 193, 7)
    pdf.set_fill_color(255, 243, 205)
    pdf.rect(10, pdf.get_y(), 190, 35, 'DF')
    
    pdf.set_xy(15, pdf.get_y() + 3)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(133, 100, 4)
    pdf.cell(0, 8, 'URGENT ACTION REQUIRED', 0, 1)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(180, 5, '1. Verify the identity of the person in the captured image.\n2. Take appropriate security measures.\n3. Report to security office if necessary.')
    
    pdf.ln(10)
    
    # Recipients Section
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 8, 'NOTIFICATION RECIPIENTS:', 0, 1)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, '  - Class Advisor', 0, 1)
    pdf.cell(0, 6, '  - Head of Department (HOD)', 0, 1)
    
    pdf.ln(10)
    
    # Disclaimer
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(128)
    pdf.cell(0, 5, 'This is an automated alert from the Smart Attendance System.', 0, 1, 'C')
    pdf.cell(0, 5, 'Do not reply to this email. Contact your system administrator for issues.', 0, 1, 'C')
    
    # Save PDF
    pdf_filename = f"intruder_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = config.UNKNOWN_DIR / pdf_filename
    pdf.output(str(pdf_path))
    
    return str(pdf_path)


def send_unknown_alert(image_path, person_label="Unknown"):
    """
    Send email alert with PDF report when unknown person is detected
    
    Args:
        image_path: Path to the captured unknown person image
        person_label: Label for the unknown person
    
    Returns:
        bool: True if email sent successfully
    """
    email_config = get_all_email_config()
    
    if not email_config["enabled"]:
        logger.info("Email alerts disabled")
        return False
    
    if not email_config["sender_email"] or email_config["sender_email"] == "your_email@gmail.com":
        logger.warning("Email not configured")
        return False
    
    recipients = []
    if email_config.get("class_advisor_email"):
        recipients.append(email_config["class_advisor_email"])
    if email_config.get("hod_email"):
        recipients.append(email_config["hod_email"])
    
    if not recipients:
        logger.warning("No recipients configured")
        return False
    
    timestamp = datetime.now()
    class_name = config.ATTENDANCE_CONFIG.get("class_name", "Class")
    
    # Create PDF report
    pdf_path = create_intruder_report_pdf(image_path, timestamp, class_name)
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = email_config["sender_email"]
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = f"INTRUDER ALERT: Unknown Person Detected in {class_name}"
    
    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">INTRUDER ALERT</h2>
            <p style="margin: 5px 0 0 0;">Unknown Person Detected - PDF Report Attached</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd;">
            <h3>Alert Summary</h3>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Date & Time:</strong></td>
                    <td>{timestamp.strftime('%d %B %Y, %I:%M %p')}</td>
                </tr>
                <tr>
                    <td><strong>Location:</strong></td>
                    <td>{class_name}</td>
                </tr>
                <tr>
                    <td><strong>Status:</strong></td>
                    <td style="color: red; font-weight: bold;">UNREGISTERED PERSON</td>
                </tr>
            </table>
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">
                <strong>Action Required:</strong>
                <p>Please review the attached PDF report containing the captured image of the unknown person and take appropriate security measures.</p>
            </div>
            
            <p style="margin-top: 20px;"><strong>Attached:</strong> Intruder_Report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf</p>
        </div>
        
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px;">
            <p style="margin: 0;">Smart Attendance System - Automated Alert</p>
            <p style="margin: 5px 0 0 0;">Recipients: Class Advisor & HOD</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))
    
    # Attach PDF report
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
            msg.attach(part)
    
    # Also attach original high-quality image
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_part = MIMEImage(f.read())
            img_part.add_header('Content-Disposition', 'attachment', 
                              filename=f"intruder_photo_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg")
            msg.attach(img_part)
        logger.info(f"Original image attached: {image_path}")
    
    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["sender_email"], email_config["sender_password"])
            server.sendmail(email_config["sender_email"], recipients, msg.as_string())
        
        logger.info(f"Intruder alert sent to: {', '.join(recipients)}")
        logger.info(f"PDF Report: {pdf_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")
        return False


def send_daily_report():
    """
    Send daily attendance report to Class Advisor and HOD
    
    Returns:
        bool: True if report sent successfully
    """
    email_config = get_all_email_config()
    
    if not email_config["enabled"]:
        logger.info("Email alerts disabled")
        return False
    
    if not email_config["sender_email"] or email_config["sender_email"] == "your_email@gmail.com":
        logger.warning("Email not configured")
        return False
    
    recipients = []
    if email_config.get("class_advisor_email"):
        recipients.append(email_config["class_advisor_email"])
    if email_config.get("hod_email"):
        recipients.append(email_config["hod_email"])
    
    if not recipients:
        logger.warning("No recipients configured")
        return False
    
    today = date.today().isoformat()
    class_name = config.ATTENDANCE_CONFIG.get("class_name", "Class")
    
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        c = conn.cursor()
        c.execute("""
            SELECT name, role, class_name, time_in, status, confidence
            FROM attendance WHERE date=? ORDER BY time_in
        """, (today,))
        records = c.fetchall()
        conn.close()
    except Exception as e:
        logger.exception(f"Database error: {e}")
        records = []
    
    # Statistics
    total_present = len(records)
    students_present = len([r for r in records if r[1] == 'student'])
    teachers_present = len([r for r in records if r[1] == 'teacher'])
    
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM people WHERE role='student'")
        total_students = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM people WHERE role='teacher'")
        total_teachers = c.fetchone()[0]
        conn.close()
    except:
        total_students = 0
        total_teachers = 0
    
    attendance_rate = (students_present / total_students * 100) if total_students > 0 else 0
    first_time = records[0][3] if records else "N/A"
    last_time = records[-1][3] if records else "N/A"
    
    # Create PDF Report
    class DailyReportPDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.set_fill_color(26, 35, 126)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, 'DAILY ATTENDANCE REPORT', 0, 1, 'C', fill=True)
            self.ln(3)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = DailyReportPDF()
    pdf.add_page()
    
    # Report Header
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(26, 35, 126)
    pdf.cell(0, 10, f'Class: {class_name}', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Date: {datetime.now().strftime("%d %B %Y")}', 0, 1, 'C')
    pdf.ln(5)
    
    # Statistics Box
    pdf.set_fill_color(232, 245, 233)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    
    pdf.set_xy(15, pdf.get_y() + 3)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'SUMMARY STATISTICS', 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 7, f'  Total Present: {total_present}', 0, 0)
    pdf.cell(95, 7, f'  Students: {students_present}/{total_students}', 0, 1)
    pdf.cell(95, 7, f'  Teachers: {teachers_present}/{total_teachers}', 0, 0)
    pdf.cell(95, 7, f'  Attendance Rate: {attendance_rate:.1f}%', 0, 1)
    
    pdf.ln(10)
    
    # Attendance Details
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'ATTENDANCE DETAILS', 0, 1)
    
    if records:
        # Table header
        pdf.set_fill_color(26, 35, 126)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(60, 8, 'Name', 1, 0, 'C', fill=True)
        pdf.cell(30, 8, 'Role', 1, 0, 'C', fill=True)
        pdf.cell(40, 8, 'Time In', 1, 0, 'C', fill=True)
        pdf.cell(30, 8, 'Status', 1, 1, 'C', fill=True)
        
        # Table rows
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0)
        
        for i, record in enumerate(records):
            fill = (i % 2 == 0)
            pdf.cell(60, 7, record[0][:25], 1, 0, 'L', fill=fill)
            pdf.cell(30, 7, record[1].title(), 1, 0, 'C', fill=fill)
            pdf.cell(40, 7, record[3], 1, 0, 'C', fill=fill)
            pdf.cell(30, 7, 'Present', 1, 1, 'C', fill=fill)
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 20, 'No attendance records for today', 0, 1, 'C')
    
    pdf.ln(10)
    
    # Footer
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(128)
    pdf.cell(0, 5, f'First Attendance: {first_time}  |  Last Attendance: {last_time}', 0, 1, 'C')
    pdf.cell(0, 5, 'Generated by Smart Attendance System', 0, 1, 'C')
    
    # Save PDF
    pdf_filename = f"attendance_report_{today}.pdf"
    pdf_path = config.ATTENDANCE_DIR / pdf_filename
    pdf.output(str(pdf_path))
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = email_config["sender_email"]
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = f"Daily Attendance Report - {class_name} ({today})"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1a237e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Daily Attendance Report</h2>
            <p style="margin: 5px 0 0 0;">{class_name} - {today}</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 20px; border: 1px solid #ddd;">
            <h3>Summary</h3>
            <table style="width: 100%;">
                <tr>
                    <td>Total Present:</td>
                    <td><strong>{total_present}</strong></td>
                    <td>Students:</td>
                    <td><strong>{students_present}/{total_students}</strong></td>
                </tr>
                <tr>
                    <td>Attendance Rate:</td>
                    <td><strong>{attendance_rate:.1f}%</strong></td>
                    <td>Teachers:</td>
                    <td><strong>{teachers_present}/{total_teachers}</strong></td>
                </tr>
            </table>
            
            <p style="margin-top: 15px;"><strong>Attached:</strong> {pdf_filename}</p>
        </div>
        
        <div style="background: #333; color: #aaa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px;">
            <p style="margin: 0;">Smart Attendance System - Automated Report</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))
    
    # Attach PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
            msg.attach(part)
    
    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["sender_email"], email_config["sender_password"])
            server.sendmail(email_config["sender_email"], recipients, msg.as_string())
        
        logger.info(f"Daily report sent to: {', '.join(recipients)}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to send report: {e}")
        return False


def test_email_connection():
    """Test email configuration"""
    email_config = get_all_email_config()
    
    if not email_config["sender_email"] or email_config["sender_email"] == "your_email@gmail.com":
        logger.warning("Email not configured")
        return False
    
    test_msg = MIMEMultipart()
    test_msg["Subject"] = "Smart Attendance System - Test Email"
    test_msg["From"] = email_config["sender_email"]
    test_msg["To"] = email_config["sender_email"]
    test_msg.attach(MIMEText("This is a test email from Smart Attendance System.", "plain"))
    
    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["sender_email"], email_config["sender_password"])
            server.send_message(test_msg)
        
        logger.info("Test email sent successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("  EMAIL ALERT SYSTEM - TEST MODE")
    print("=" * 50)
    print("\n1. Test email connection")
    print("2. Send daily report manually")
    print("3. Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        test_email_connection()
    elif choice == "2":
        send_daily_report()
