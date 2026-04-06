"""
PDF Generator Module for Smart Attendance System v2
Generates daily, monthly, and alert PDFs using ReportLab
"""

import os
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import cv2
import numpy as np
import config
import database
from logger import get_logger

logger = get_logger()


def get_reports_dir():
    """Get reports directory."""
    reports_dir = config.REPORTS_DIR
    try:
        reports_dir.mkdir(exist_ok=True)
    except OSError as e:
        logger.warning(f"Could not create reports dir: {e}")
    return reports_dir


def _enhance_image_for_pdf(image_path, max_width=6*inch, max_height=4*inch):
    """Enhance image quality for PDF embedding. Returns (path, width, height) or None."""
    if not Path(image_path).exists():
        return None
    
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        height, width = img.shape[:2]
        if height < 20 or width < 20:
            return None
        
        aspect = width / height
        
        if width > height:
            disp_width = min(width, max_width)
            disp_height = disp_width / aspect
        else:
            disp_height = min(height, max_height)
            disp_width = disp_height * aspect
        
        enhanced_path = str(Path(tempfile.gettempdir()) / f"sas_enhanced_{Path(image_path).name}")
        success = cv2.imwrite(enhanced_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if success:
            return enhanced_path, disp_width, disp_height
        return None
    except Exception as e:
        logger.warning(f"Could not enhance image: {e}")
        return None


def _parse_timestamp(ts_str):
    """Parse timestamp string, handling multiple formats."""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except (ValueError, TypeError):
            pass
    logger.warning(f"Could not parse timestamp: {ts_str}")
    return None


def generate_daily_report():
    """Generate daily attendance PDF report. Returns: path to saved PDF."""
    today = date.today()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG.get("class_name", "")
    college_name = database.get_setting("college_name") or config.ATTENDANCE_CONFIG.get("college_name", "")
    
    filename = f"daily_report_{today.strftime('%Y%m%d')}.pdf"
    filepath = get_reports_dir() / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    elements.append(Paragraph(college_name or '', header_style))
    elements.append(Paragraph("Daily Attendance Report", title_style))
    elements.append(Paragraph(f"Class: {class_name or ''} | Date: {today.strftime('%d %B %Y')}", header_style))
    elements.append(Spacer(1, 20))
    
    attendance = database.get_today_attendance()
    stats = database.get_stats()
    movement = database.get_today_movement()
    
    summary_data = [
        ['Total Present', str(stats['present_today'])],
        ['Students', f"{stats['present_students']}/{stats['total_students']}"],
        ['Attendance Rate', f"{stats['attendance_rate']}%"],
        ['Movement Events', str(len(movement))]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8eaf6')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Attendance Details", styles['Heading2']))
    
    if attendance:
        table_data = [['S.No', 'Name', 'Roll No', 'Time In', 'Status']]
        for i, record in enumerate(attendance, 1):
            name = str(record.get('name', '-'))[:30]
            roll = str(record.get('roll_number') or '-')
            time_in = str(record.get('time_in', '-'))
            status = str(record.get('status', 'present'))
            table_data.append([str(i), name, roll, time_in, status])
        
        attendance_table = Table(table_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 1*inch, 1*inch])
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        elements.append(attendance_table)
    else:
        elements.append(Paragraph("No attendance records for today.", styles['Normal']))
    
    if movement:
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Movement Log", styles['Heading2']))
        
        mov_data = [['Time', 'Name', 'Role', 'Event']]
        for record in movement[:20]:
            ts = _parse_timestamp(str(record.get('timestamp', '')))
            ts_str = ts.strftime('%H:%M:%S') if ts else '-'
            name = str(record.get('name', '-'))[:25]
            role = str(record.get('role', '-'))
            event = 'Entry' if record.get('event_type') == 'entry' else 'Exit'
            mov_data.append([ts_str, name, role, event])
        
        mov_table = Table(mov_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch])
        mov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(mov_table)
    
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    elements.append(Paragraph(
        f"Generated by Smart Attendance System on {datetime.now().strftime('%d %b %Y at %I:%M %p')}",
        footer_style
    ))
    
    doc.build(elements)
    return str(filepath)


def generate_monthly_report():
    """Generate 30-day monthly attendance report. Returns: path to saved PDF or None."""
    today = date.today()
    batch = database.get_active_batch()
    
    if not batch:
        logger.warning("No active batch found for monthly report")
        return None
    
    start_date_str = batch.get('start_date', '')
    end_date_str = batch.get('end_date', '')
    batch_id = batch.get('id', 0)
    batch_status = batch.get('status', 'active')
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid batch dates: {e}")
        return None
    
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG.get("class_name", "")
    college_name = database.get_setting("college_name") or config.ATTENDANCE_CONFIG.get("college_name", "")
    
    filename = f"monthly_report_{start_date.strftime('%Y%m')}.pdf"
    filepath = get_reports_dir() / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#1a237e'), spaceAfter=30)
    
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph(college_name or '', title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Monthly Attendance Report", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Class: {class_name or ''}", styles['Heading2']))
    elements.append(Paragraph(
        f"Period: {start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 30))
    
    batch_info = [
        ['Batch ID', str(batch_id)],
        ['Start Date', start_date_str],
        ['End Date', end_date_str],
        ['Status', batch_status]
    ]
    
    batch_table = Table(batch_info, colWidths=[1.5*inch, 3*inch])
    batch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(batch_table)
    elements.append(PageBreak())
    elements.append(Paragraph("Attendance Summary", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    attendance = database.get_attendance_by_date_range(start_date_str, end_date_str)
    people = database.get_active_people()
    
    days_total = (end_date - start_date).days + 1
    
    summary_data = [['S.No', 'Name', 'Roll No', 'Days Present', 'Days Absent', 'Attendance %']]
    
    for i, person in enumerate(people, 1):
        if isinstance(person, dict):
            person_name = str(person.get('name', ''))
            person_roll = person.get('roll_number') or '-'
        else:
            person_name = str(person[1]) if len(person) > 1 else ''
            person_roll = person[3] if len(person) > 3 else '-'
        
        present_dates = set()
        for r in attendance:
            r_name = r.get('name', '') if isinstance(r, dict) else (r[2] if len(r) > 2 else '')
            if r_name.lower() == person_name.lower():
                r_date = r.get('date', '') if isinstance(r, dict) else (r[4] if len(r) > 4 else '')
                if r_date:
                    present_dates.add(r_date)
        
        present_days = len(present_dates)
        absent_days = max(0, days_total - present_days)
        attendance_pct = round((present_days / days_total) * 100, 1) if days_total > 0 else 0
        
        summary_data.append([
            str(i),
            person_name[:30],
            str(person_roll),
            str(present_days),
            str(absent_days),
            f"{attendance_pct}%"
        ])
    
    summary_table = Table(summary_data, colWidths=[0.4*inch, 2*inch, 1*inch, 1*inch, 1*inch, 1.1*inch])
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]
    
    for i, row in enumerate(summary_data[1:], 1):
        pct_str = row[5].replace('%', '')
        try:
            if float(pct_str) < 75:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffcdd2')))
                table_style.append(('TEXTCOLOR', (-1, i), (-1, i), colors.HexColor('#c62828')))
        except ValueError:
            pass
    
    summary_table.setStyle(TableStyle(table_style))
    elements.append(summary_table)
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Security Alerts", styles['Heading2']))
    
    alerts = database.get_recent_alerts(50)
    alerts_in_batch = []
    
    for alert in alerts:
        ts_str = alert.get('timestamp', '') if isinstance(alert, dict) else alert[1]
        try:
            ts = _parse_timestamp(ts_str)
            if ts and ts.date() >= start_date:
                alerts_in_batch.append(alert)
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    
    if alerts_in_batch:
        alert_data = [['Date', 'Time', 'Alert ID', 'Status']]
        for alert in alerts_in_batch[:20]:
            ts_str = alert.get('timestamp', '') if isinstance(alert, dict) else alert[1]
            alert_id = alert.get('alert_id', '') if isinstance(alert, dict) else (alert[7] or f"ALERT-{alert[0]}")
            sent = alert.get('alert_sent', 0) if isinstance(alert, dict) else alert[6]
            
            ts = _parse_timestamp(ts_str)
            date_str = ts.strftime('%d %b') if ts else '-'
            time_str = ts.strftime('%H:%M') if ts else '-'
            alert_data.append([date_str, time_str, str(alert_id), 'Sent' if sent else 'Failed'])
        
        alert_table = Table(alert_data, colWidths=[1.2*inch, 1*inch, 2*inch, 1*inch])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(alert_table)
    else:
        elements.append(Paragraph("No security alerts in this period.", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    elements.append(Paragraph(
        f"Generated by Smart Attendance System on {datetime.now().strftime('%d %b %Y at %I:%M %p')}",
        footer_style
    ))
    
    doc.build(elements)
    return str(filepath)


def generate_alert_pdf(image_path):
    """Generate security alert PDF with intruder photo. Returns: path to saved PDF."""
    timestamp = datetime.now()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG.get("class_name", "")
    college_name = database.get_setting("college_name") or config.ATTENDANCE_CONFIG.get("college_name", "")
    alert_id = f"ALERT-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    filename = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_reports_dir() / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle('AlertHeader', parent=styles['Heading1'], fontSize=20,
                                   alignment=TA_CENTER, textColor=colors.white, spaceAfter=10)
    
    header_table = Table([[Paragraph("SECURITY ALERT", header_style)]], colWidths=[6*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dc3545')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20)
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 30))
    
    info_data = [
        ['ALERT INFORMATION'],
        [f'Date: {timestamp.strftime("%d %B %Y")}'],
        [f'Time: {timestamp.strftime("%I:%M %p")}'],
        [f'Location: {class_name or "Unknown"}'],
        [f'Alert ID: {alert_id}'],
        ['Status: UNKNOWN PERSON DETECTED']
    ]
    
    info_table = Table(info_data, colWidths=[5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff3f3')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#dc3545'))
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Captured Image", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    enhanced_path = None
    try:
        if Path(image_path).exists():
            result = _enhance_image_for_pdf(image_path)
            if result:
                enhanced_path, img_width, img_height = result
                img = Image(enhanced_path, width=img_width, height=img_height)
                img_table = Table([[img]], colWidths=[6*inch])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#dc3545'))
                ]))
                elements.append(img_table)
            else:
                elements.append(Paragraph("Image could not be processed", styles['Normal']))
        else:
            elements.append(Paragraph("Image file not found", styles['Normal']))
    except Exception as e:
        logger.warning(f"Error adding image to PDF: {e}")
        elements.append(Paragraph("Image not available", styles['Normal']))
    finally:
        if enhanced_path:
            try:
                Path(enhanced_path).unlink(missing_ok=True)
            except OSError:
                pass
    
    elements.append(Spacer(1, 30))
    
    action_data = [
        ['URGENT ACTION REQUIRED'],
        ['1. Review the captured image above'],
        ['2. Attempt to identify the individual'],
        ['3. Take appropriate security measures'],
        ['4. Report to security office if necessary']
    ]
    
    action_table = Table(action_data, colWidths=[5*inch])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff8e1')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107'))
    ]))
    
    elements.append(action_table)
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    elements.append(Paragraph(f"Generated by Smart Attendance System | Alert ID: {alert_id}", footer_style))
    
    doc.build(elements)
    return str(filepath)


def generate_end_of_day_report():
    """Generate end-of-day summary with movement report. Returns: path to saved PDF."""
    today = date.today()
    class_name = database.get_setting("class_name") or config.ATTENDANCE_CONFIG.get("class_name", "")
    
    filename = f"end_of_day_{today.strftime('%Y%m%d')}.pdf"
    filepath = get_reports_dir() / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#1a237e'))
    elements.append(Paragraph("End of Day Report", title_style))
    elements.append(Paragraph(f"Class: {class_name or ''} | Date: {today.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    movement = database.get_today_movement()
    elements.append(Paragraph("Movement Summary", styles['Heading2']))
    
    if movement:
        mov_data = [['Time', 'Name', 'Role', 'Event']]
        for record in movement:
            ts = _parse_timestamp(str(record.get('timestamp', '')))
            ts_str = ts.strftime('%H:%M:%S') if ts else '-'
            name = str(record.get('name', '-'))[:30]
            role = str(record.get('role', '-'))
            event = 'Entry' if record.get('event_type') == 'entry' else 'Exit'
            mov_data.append([ts_str, name, role, event])
        
        mov_table = Table(mov_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1*inch])
        mov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(mov_table)
    else:
        elements.append(Paragraph("No movement recorded today.", styles['Normal']))
    
    doc.build(elements)
    return str(filepath)


if __name__ == "__main__":
    print("PDF Generator Module Ready")
