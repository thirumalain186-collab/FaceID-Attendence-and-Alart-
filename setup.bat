@echo off
title Smart Attendance System - Setup
echo ====================================
echo  Smart Attendance System Setup
echo ====================================
echo.

echo [1/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo.
echo [2/4] Installing Python dependencies...
pip install opencv-python numpy Pillow pandas flask
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Creating directories...
if not exist "dataset" mkdir dataset
if not exist "trainer" mkdir trainer
if not exist "unknown_faces" mkdir unknown_faces
if not exist "attendance_logs" mkdir attendance_logs
if not exist "known_faces" mkdir known_faces

echo.
echo [4/4] Checking Haar Cascade file...
if exist "haarcascade_frontalface_default.xml" (
    echo [OK] Haar Cascade file found
) else (
    echo [WARNING] Haar Cascade file not found!
    echo Please download from:
    echo https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
)

echo.
echo ====================================
echo  Setup Complete!
echo ====================================
echo.
echo Quick Start:
echo 1. python main.py              - Run main menu
echo 2. python register_faces.py   - Register people
echo 3. python train.py             - Train model
echo.
echo Documentation: See README.md
echo.
pause
