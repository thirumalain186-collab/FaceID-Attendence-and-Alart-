# Smart Attendance System - Desktop App

## Quick Start

### 1. Install Dependencies
```bash
cd electron
npm install
```

### 2. Run the Desktop App
```bash
npm start
```

This will automatically:
- Start the Flask backend
- Open the desktop window
- Load your attendance dashboard

### 3. Build .exe (Optional)
```bash
# For portable .exe
npm run build

# For installer
npm run build-installer
```

The .exe will be in `electron/dist/`

## Features
- Auto-starts Flask backend
- Desktop UI (no browser needed)
- Error handling with user-friendly messages
- Loading screen while starting
- Window controls (minimize, maximize, close)

## Troubleshooting

### Port 5000 already in use
```powershell
# Find and kill the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Flask not starting
Make sure you have all Python dependencies:
```bash
pip install -r requirements.txt
```

### Build fails
Make sure electron-builder is installed:
```bash
npm install electron-builder
```
