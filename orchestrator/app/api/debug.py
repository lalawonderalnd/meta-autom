"""
Local Web Debug UI for Meta Autom Farm.

Provides a simple web interface for debugging with:
- Live ADB logs from devices
- Screen mirroring via ws-scrcpy
- Manual command execution
- Account state inspection
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

# Active WebSocket connections
active_connections: Dict[int, List[WebSocket]] = {}


@router.get("/", response_class=HTMLResponse)
async def debug_ui():
    """Render the debug UI."""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Meta Autom Debug Console</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #00d9ff; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { background: #16213e; border-radius: 8px; padding: 15px; }
        .panel h2 { color: #e94560; margin-bottom: 10px; font-size: 16px; }
        select, input, button { 
            background: #0f3460; border: 1px solid #e94560; 
            color: #eee; padding: 8px; border-radius: 4px; margin: 5px 0;
        }
        button { cursor: pointer; background: #e94560; }
        button:hover { background: #ff6b6b; }
        .log-viewer { 
            background: #0a0a15; border-radius: 4px; padding: 10px; 
            height: 400px; overflow-y: auto; font-size: 12px;
        }
        .log-line { margin: 2px 0; padding: 2px; border-left: 3px solid transparent; }
        .log-line.info { border-color: #00d9ff; }
        .log-line.warn { border-color: #ffa500; }
        .log-line.error { border-color: #ff4444; }
        .device-status { padding: 10px; margin: 5px 0; background: #0f3460; border-radius: 4px; }
        .device-status.online { border-left: 4px solid #00ff88; }
        .device-status.offline { border-left: 4px solid #ff4444; }
        #scrcpy-container { width: 100%; height: 500px; background: #000; }
        .tabs { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab { padding: 8px 16px; background: #0f3460; border-radius: 4px; cursor: pointer; }
        .tab.active { background: #e94560; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Meta Autom Debug Console</h1>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('logs')">ADB Logs</div>
            <div class="tab" onclick="showTab('screen')">Screen Mirror</div>
            <div class="tab" onclick="showTab('commands')">Commands</div>
            <div class="tab" onclick="showTab('accounts')">Accounts</div>
        </div>
        
        <div id="logs-tab" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Device Selection</h2>
                    <select id="device-select" onchange="connectLogs()">
                        <option value="">Select a device...</option>
                    </select>
                    <div id="device-list"></div>
                </div>
                <div class="panel">
                    <h2>Live ADB Logs</h2>
                    <div id="log-viewer" class="log-viewer"></div>
                    <button onclick="clearLogs()">Clear</button>
                </div>
            </div>
        </div>
        
        <div id="screen-tab" class="tab-content" style="display:none;">
            <div class="panel">
                <h2>Screen Mirror (ws-scrcpy)</h2>
                <select id="screen-device-select" onchange="connectScreen()">
                    <option value="">Select a device...</option>
                </select>
                <div id="scrcpy-container"></div>
            </div>
        </div>
        
        <div id="commands-tab" class="tab-content" style="display:none;">
            <div class="panel">
                <h2>Execute ADB Command</h2>
                <select id="cmd-device-select">
                    <option value="">Select a device...</option>
                </select>
                <input type="text" id="adb-command" placeholder="e.g., shell pm list packages | grep instagram" style="width: 100%;">
                <button onclick="executeCommand()">Execute</button>
                <div id="command-output" class="log-viewer" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        <div id="accounts-tab" class="tab-content" style="display:none;">
            <div class="panel">
                <h2>Account States</h2>
                <div id="account-list"></div>
            </div>
        </div>
    </div>
    
    <script>
        let logSocket = null;
        
        function showTab(name) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(name + '-tab').style.display = 'block';
            event.target.classList.add('active');
        }
        
        async function loadDevices() {
            const resp = await fetch('/api/devices?status=all');
            const data = await resp.json();
            const selects = ['device-select', 'screen-device-select', 'cmd-device-select'];
            
            selects.forEach(id => {
                const el = document.getElementById(id);
                el.innerHTML = '<option value="">Select a device...</option>';
                data.devices.forEach(d => {
                    el.innerHTML += `<option value="${d.id}">${d.name} (${d.adb_address})</option>`;
                });
            });
        }
        
        function connectLogs() {
            const deviceId = document.getElementById('device-select').value;
            if (!deviceId) return;
            
            if (logSocket) logSocket.close();
            
            logSocket = new WebSocket(`ws://${location.host}/debug/logs/${deviceId}`);
            logSocket.onmessage = (event) => {
                const viewer = document.getElementById('log-viewer');
                const line = document.createElement('div');
                line.className = 'log-line info';
                line.textContent = event.data;
                viewer.appendChild(line);
                viewer.scrollTop = viewer.scrollHeight;
            };
        }
        
        function clearLogs() {
            document.getElementById('log-viewer').innerHTML = '';
        }
        
        async function executeCommand() {
            const deviceId = document.getElementById('cmd-device-select').value;
            const cmd = document.getElementById('adb-command').value;
            if (!deviceId || !cmd) return;
            
            const output = document.getElementById('command-output');
            output.innerHTML = 'Executing...';
            
            const resp = await fetch(`/api/devices/${deviceId}/execute`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd})
            });
            const data = await resp.json();
            output.innerHTML = data.output || data.error;
        }
        
        async function loadAccounts() {
            const resp = await fetch('/api/accounts?limit=50');
            const data = await resp.json();
            const container = document.getElementById('account-list');
            container.innerHTML = data.accounts.map(a => `
                <div class="device-status ${a.status.toLowerCase()}">
                    <strong>${a.username}</strong> - Status: ${a.status} | 
                    Device: ${a.device_id || 'None'} | 
                    Warmup Day: ${a.current_warmup_day || 0}/7
                </div>
            `).join('');
        }
        
        // Auto-refresh
        loadDevices();
        loadAccounts();
        setInterval(loadDevices, 30000);
        setInterval(loadAccounts, 10000);
    </script>
</body>
</html>
""")


@router.websocket("/logs/{device_id}")
async def websocket_logs(websocket: WebSocket, device_id: int):
    """WebSocket endpoint for streaming ADB logs."""
    await websocket.accept()
    
    if device_id not in active_connections:
        active_connections[device_id] = []
    active_connections[device_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_text("ping")
    except WebSocketDisconnect:
        pass
    finally:
        if device_id in active_connections:
            active_connections[device_id].remove(websocket)


@router.get("/devices/{device_id}/scrcpy")
async def scrcpy_stream(device_id: int):
    """Return ws-scrcpy embed URL for screen mirroring."""
    # This would integrate with actual ws-scrcpy instance
    return {"stream_url": f"ws://localhost:8910/device/{device_id}"}


async def broadcast_log(device_id: int, message: str, level: str = "info"):
    """Broadcast a log message to all connected clients for a device."""
    if device_id not in active_connections:
        return
    
    formatted = f"[{level.upper()}] {message}"
    for ws in active_connections[device_id]:
        try:
            await ws.send_text(formatted)
        except:
            pass


# Health check
@router.get("/health")
async def debug_health():
    """Debug UI health check."""
    return {
        "status": "ok",
        "active_connections": sum(len(conns) for conns in active_connections.values())
    }
