const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods for window controls
contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('minimize-window'),
  maximize: () => ipcRenderer.send('maximize-window'),
  close: () => ipcRenderer.send('close-window'),
  
  // Get app info
  getAppVersion: () => require('electron').app.getVersion(),
  
  // Platform info
  platform: process.platform
});
