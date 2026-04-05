@echo off
echo ====================================
echo  RESET SMART ATTENDANCE SYSTEM
echo ====================================
echo.
echo This will DELETE:
echo  - All registered faces
echo  - Trained model
echo  - Attendance records
echo  - Database
echo.
set /p confirm="Are you sure? (yes/no): "
if /i not "%confirm%"=="yes" exit

echo.
echo Removing data...

del attendance.db 2>nul
del attendance.csv 2>nul
del /s /q dataset\*.* 2>nul
del /s /q trainer\*.* 2>nul
del /s /q known_faces\*.* 2>nul
del /s /q attendance_logs\*.* 2>nul
del /s /q unknown_faces\*.* 2>nul

rmdir dataset 2>nul
rmdir trainer 2>nul
rmdir known_faces 2>nul
rmdir attendance_logs 2>nul
rmdir unknown_faces 2>nul

mkdir dataset
mkdir trainer
mkdir known_faces
mkdir attendance_logs
mkdir unknown_faces

echo.
echo ====================================
echo  ALL DATA REMOVED!
echo ====================================
echo.
echo You can now start fresh.
pause
