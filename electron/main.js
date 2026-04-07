const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
log.transports.file.maxSize = 5 * 1024 * 1024;
log.info('Application starting...');

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log.error('Uncaught Exception:', error);
  dialog.showErrorBox('Error', `Uncaught Exception: ${error.message}`);
  app.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled Rejection:', reason);
});

let mainWindow;
let flaskProcess = null;
let flaskReady = false;
const FLASK_PORT = 5000;
const FLASK_URL = `http://127.0.0.1:${FLASK_PORT}`;

// Get the app root directory (where main.py is)
const APP_ROOT = path.join(__dirname, '..');
const PYTHON_PATH = "C:\\Users\\thiru\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
const PYTHON_CMD = process.platform === 'win32' ? PYTHON_PATH : 'python3';

function startFlaskServer() {
  return new Promise((resolve, reject) => {
    log.info('Starting Flask server...');
    
    flaskProcess = spawn(PYTHON_CMD, ['app.py'], {
      cwd: APP_ROOT,
      shell: true,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONPATH: APP_ROOT }
    });

    flaskProcess.stdout.on('data', (data) => {
      const output = data.toString();
      log.info('Flask:', output);
      
      // Check if Flask is ready
      if (output.includes('Running on') || output.includes('127.0.0.1') || output.includes('localhost')) {
        flaskReady = true;
        resolve();
      }
    });

    flaskProcess.stderr.on('data', (data) => {
      log.warn('Flask warning:', data.toString());
    });

    flaskProcess.on('error', (error) => {
      log.error('Failed to start Flask:', error);
      reject(error);
    });

    flaskProcess.on('exit', (code) => {
      log.info(`Flask exited with code ${code}`);
      flaskReady = false;
      if (code !== 0 && code !== null) {
        dialog.showErrorBox('Flask Error', `Flask server crashed with exit code ${code}`);
      }
    });

    // Timeout - if Flask doesn't start in 30 seconds
    setTimeout(() => {
      if (!flaskReady) {
        log.warn('Flask startup timeout, proceeding anyway...');
        resolve(); // Proceed anyway - Flask might still be starting
      }
    }, 30000);
  });
}

function stopFlaskServer() {
  if (flaskProcess) {
    log.info('Stopping Flask server...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', flaskProcess.pid, '/f', '/t'], { shell: true });
    } else {
      flaskProcess.kill('SIGTERM');
    }
    flaskProcess = null;
    flaskReady = false;
  }
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'Smart Attendance System',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false // Don't show until ready
  });

  // Show loading screen
  mainWindow.loadURL(`data:text/html,
    <html>
      <body style="display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#1a237e;font-family:Arial,sans-serif;">
        <div style="text-align:center;color:white;">
          <h1>Smart Attendance System</h1>
          <p>Loading...</p>
          <p>Starting Flask server...</p>
        </div>
      </body>
    </html>
  `);

  try {
    // Start Flask
    await startFlaskServer();
    
    // Load the app
    log.info(`Loading Flask app from ${FLASK_URL}`);
    await mainWindow.loadURL(FLASK_URL);
    
    // Show window when ready
    mainWindow.once('ready-to-show', () => {
      mainWindow.show();
      log.info('Window shown');
    });

  } catch (error) {
    log.error('Failed to start:', error);
    dialog.showErrorBox('Startup Error', `Failed to start application: ${error.message}`);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  log.info('Main window created');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopFlaskServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopFlaskServer();
});

// IPC handlers for window controls
ipcMain.on('minimize-window', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('maximize-window', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('close-window', () => {
  if (mainWindow) mainWindow.close();
});

// IPC to check Flask status
ipcMain.handle('flask-status', () => {
  return {
    running: flaskReady,
    url: FLASK_URL
  };
});

// Restart Flask
ipcMain.on('restart-flask', async () => {
  stopFlaskServer();
  await startFlaskServer();
  if (mainWindow && flaskReady) {
    mainWindow.loadURL(FLASK_URL);
  }
});

// Open face detection page
ipcMain.on('open-face-detection', () => {
  if (mainWindow) {
    const faceDetectionPath = path.join(__dirname, 'face-detection.html');
    mainWindow.loadFile(faceDetectionPath);
  }
});

log.info('App initialized');
