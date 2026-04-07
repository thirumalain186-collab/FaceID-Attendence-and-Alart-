const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods for window controls
contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.send('minimize-window'),
  maximize: () => ipcRenderer.send('maximize-window'),
  close: () => ipcRenderer.send('close-window'),
  
  // Flask status
  getFlaskStatus: () => ipcRenderer.invoke('flask-status'),
  restartFlask: () => ipcRenderer.send('restart-flask'),
  
  // Face detection page
  openFaceDetection: () => ipcRenderer.send('open-face-detection'),
  
  // Get app info
  getAppVersion: () => require('electron').app.getVersion(),
  
  // Platform info
  platform: process.platform
});
