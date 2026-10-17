// synthetic_electron_app/renderer.js
// Renderer script consuming contextBridge API

document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('vault-status');
  if (window.vaultAPI && statusEl) {
    try {
      const res = await window.vaultAPI.getStatus();
      statusEl.textContent = `Status: ${res.status} (${res.records_count} records)`;
    } catch (err) {
      statusEl.textContent = `Error: ${err.message}`;
    }
  }
});
