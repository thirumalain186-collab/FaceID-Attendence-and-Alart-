# Desktop Application Build Guide

This guide explains how to build the Smart Attendance System as a standalone Windows executable (.exe).

## Prerequisites

### 1. Install Node.js (Required for Electron)

Download and install Node.js from https://nodejs.org/ (LTS version recommended)

Verify installation:
```powershell
node --version
npm --version
```

### 2. Install Python Dependencies

Make sure all Python dependencies are installed:
```powershell
pip install -r requirements.txt
```

## Building the Desktop App

### Step 1: Navigate to Electron Directory

```powershell
cd electron
```

### Step 2: Install Electron Dependencies

```powershell
npm install
```

### Step 3: Test in Development Mode

Before building, test that everything works:

```powershell
npm start
```

This will open the desktop application window. The backend Flask server should be running separately on port 5000.

### Step 4: Build the .exe File

Build a portable executable (no installation needed):

```powershell
npm run build
```

Or build an installer:

```powershell
npm run build-installer
```

The .exe file will be created in `electron/dist/`

## Adding an App Icon (Optional)

1. Create a 256x256 PNG image for the icon
2. Convert to .ico format using an online tool or:
   ```powershell
   npm install -g png2icons
   png2icons icon.png
   ```
3. Place `icon.ico` and `icon.png` in the `electron/` folder

## Troubleshooting

### "electron-builder not found"

```powershell
npm install electron-builder --save-dev
```

### "Cannot find module 'electron'"

```powershell
npm install
```

### Build fails with memory error

```powershell
npm run build -- --max-old-space-size=4096
```

### Antivirus blocks the .exe

The executable may be flagged by some antivirus software. This is normal for Electron apps. You can:
1. Add the file to your antivirus exclusions
2. Sign the executable (requires code signing certificate)

## Running the Built Application

1. Copy the `dist/` folder contents to any Windows machine
2. Make sure Python 3.10+ is installed on the target machine
3. Install dependencies: `pip install -r requirements.txt`
4. Run the Flask backend: `python app.py`
5. Run the desktop app: `Smart Attendance System.exe`

## Architecture

The desktop app is a wrapper that:
1. Displays the Flask web dashboard in an Electron window
2. Provides native window controls (minimize, maximize, close)
3. Communicates with the backend API on localhost:5000
4. Uses electron-log for application logging
