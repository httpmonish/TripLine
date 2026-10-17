// synthetic_electron_app/preload.js
// Preload script exposing safe contextBridge APIs for synthetic Electron application

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('vaultAPI', {
  getStatus: () => ipcRenderer.invoke('vault:status'),
  verifyToken: (token) => ipcRenderer.invoke('vault:verify-token', token),
});
