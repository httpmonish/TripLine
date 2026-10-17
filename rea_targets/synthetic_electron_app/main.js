// synthetic_electron_app/main.js
// Synthetic Electron main process for REA static analysis validation in TripLine Phase R1

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 650,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.loadFile('index.html');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers for synthetic vault features
ipcMain.handle('vault:status', async (_event) => {
  return { status: 'locked', records_count: 42, policy_version: '1.0' };
});

ipcMain.handle('vault:verify-token', async (_event, token) => {
  if (typeof token !== 'string') {
    throw new Error('Invalid token parameter');
  }
  return { valid: token.startsWith('TRPL-') };
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
