"""
Generate Linux Setup Guide PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from pathlib import Path

def create_linux_setup_pdf():
    doc = SimpleDocTemplate(
        "Linux_Setup_Guide.pdf",
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1a237e')
    )
    
    heading1 = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#1a237e')
    )
    
    heading2 = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#303f9f')
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=10,
        fontName='Courier',
        backColor=colors.HexColor('#f5f5f5'),
        borderColor=colors.HexColor('#ddd'),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=5,
        spaceAfter=5
    )
    
    normal = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=5,
        spaceAfter=5
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Smart Attendance System", title_style))
    story.append(Paragraph("Linux Setup Guide", title_style))
    story.append(Spacer(1, 30))
    
    # Step 1
    story.append(Paragraph("Step 1: Update System", heading1))
    story.append(Paragraph("<code>sudo apt update &&amp;&amp; sudo apt upgrade -y</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 2
    story.append(Paragraph("Step 2: Install Git", heading1))
    story.append(Paragraph("<code>sudo apt install git -y</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 3
    story.append(Paragraph("Step 3: Clone Repository", heading1))
    story.append(Paragraph("<code>git clone https://github.com/thirumalain186-collab/FaceID-Attendence-and-Alart-.git</code>", code_style))
    story.append(Paragraph("<code>cd FaceID-Attendence-and-Alart-</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 4
    story.append(Paragraph("Step 4: Install Python & Pip", heading1))
    story.append(Paragraph("<code>sudo apt install python3 python3-pip python3-venv -y</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 5
    story.append(Paragraph("Step 5: Create Virtual Environment", heading1))
    story.append(Paragraph("<code>python3 -m venv venv</code>", code_style))
    story.append(Paragraph("<code>source venv/bin/activate</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 6
    story.append(Paragraph("Step 6: Install System Dependencies", heading1))
    story.append(Paragraph("<code>sudo apt install libopencv-dev python3-opencv libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 -y</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 7
    story.append(Paragraph("Step 7: Install Python Dependencies", heading1))
    story.append(Paragraph("<code>pip install -r requirements.txt</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Page Break
    story.append(PageBreak())
    
    # Step 8
    story.append(Paragraph("Step 8: Create Environment File", heading1))
    story.append(Paragraph("<code>cp .env.example .env</code>", code_style))
    story.append(Paragraph("<code>nano .env</code>", code_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Add these lines to .env file:", normal))
    env_content = """
    SENDER_EMAIL=your_email@gmail.com
    SENDER_PASSWORD=your_16char_app_password
    CLASS_ADVISOR_EMAIL=advisor@college.edu
    HOD_EMAIL=hod@college.edu
    CLASS_NAME=CS-A
    COLLEGE_NAME=Your College Name
    EMAIL_ENABLED=true
    """
    story.append(Paragraph(env_content.replace('\n', '<br/>'), code_style))
    story.append(Spacer(1, 15))
    
    # Step 9
    story.append(Paragraph("Step 9: Initialize Database", heading1))
    story.append(Paragraph('<code>python3 -c "import database; database.init_database()"</code>', code_style))
    story.append(Spacer(1, 15))
    
    # Step 10
    story.append(Paragraph("Step 10: Run Tests (Optional)", heading1))
    story.append(Paragraph("<code>pip install pytest pytest-cov</code>", code_style))
    story.append(Paragraph("<code>pytest tests/ -v</code>", code_style))
    story.append(Spacer(1, 15))
    
    # Step 11
    story.append(Paragraph("Step 11: Run the Application", heading1))
    story.append(Paragraph("<b>Option A - CLI Mode:</b>", normal))
    story.append(Paragraph("<code>python3 main.py</code>", code_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Option B - Web Dashboard:</b>", normal))
    story.append(Paragraph("<code>python3 app.py</code>", code_style))
    story.append(Paragraph("Access at: http://localhost:5000", normal))
    story.append(Spacer(1, 20))
    
    # Troubleshooting
    story.append(Paragraph("Quick Test Commands", heading1))
    story.append(Paragraph("<code># Test camera</code>", code_style))
    story.append(Paragraph('<code>python3 -c "import cv2; cap = cv2.VideoCapture(0); print(\'OK\' if cap.isOpened() else \'FAIL\')"</code>', code_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<code># Test imports</code>", code_style))
    story.append(Paragraph('<code>python3 -c "import cv2; import flask; import reportlab; print(\'All OK\')"</code>', code_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<code># Test database</code>", code_style))
    story.append(Paragraph('<code>python3 -c "import database; database.init_database(); print(\'DB OK\')"</code>', code_style))
    story.append(Spacer(1, 20))
    
    # Docker Method
    story.append(Paragraph("Docker Method (Alternative)", heading1))
    story.append(Paragraph("<code>sudo apt install docker.io docker-compose -y</code>", code_style))
    story.append(Paragraph("<code>sudo systemctl start docker</code>", code_style))
    story.append(Paragraph("<code>sudo systemctl enable docker</code>", code_style))
    story.append(Paragraph("<code>sudo docker-compose up -d</code>", code_style))
    story.append(Paragraph("Access at: http://localhost:5000", normal))
    story.append(Spacer(1, 20))
    
    # Troubleshooting
    story.append(Paragraph("Troubleshooting", heading1))
    story.append(Paragraph("<b>Camera Permission:</b>", normal))
    story.append(Paragraph("<code>sudo usermod -aG video $USER</code>", code_style))
    story.append(Paragraph("<code>newgrp video</code>", code_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>OpenCV Error:</b>", normal))
    story.append(Paragraph("<code>pip uninstall opencv-python opencv-contrib-python</code>", code_style))
    story.append(Paragraph("<code>pip install opencv-contrib-python==4.8.0.74</code>", code_style))
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 40))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)
    story.append(Paragraph("Smart Attendance System v2 - Linux Setup Guide", footer_style))
    story.append(Paragraph("GitHub: github.com/thirumalain186-collab/FaceID-Attendence-and-Alart-", footer_style))
    
    doc.build(story)
    print("PDF created: Linux_Setup_Guide.pdf")

if __name__ == "__main__":
    create_linux_setup_pdf()
