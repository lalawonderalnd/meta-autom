# AccFarm Device Layer

The Device Layer is the boundary between the orchestrator and physical Android phones running App Cloner. It is the only place in the codebase that touches ADB or uiautomator2 directly.

## Features

- ADB connection pooling with retry/reconnect logic
- Per-phone mutex ensuring single-foreground-clone operation
- App Cloner clone discovery and launching
- Per-clone proxy injection at app launch
- Screenshot service
- WebSocket bridge to ws-scrcpy for live dashboard view
- Health checks (device reachability, clone responsiveness)
- Humanized automation (Bezier swipes, jittered taps, realistic typing)

## Installation

```bash
cd device_layer
uv sync
```

## Usage

```python
from accfarm_device.pool import DevicePool

pool = DevicePool()
device = pool.register_device(serial="ABC123", ip="192.168.1.100")

with pool.acquire(device.id, "com.instagram.androidp1") as session:
    session.tap_element(session.wait_for(text="Home"))
    session.screenshot()
```

## Architecture

See `02_DEVICE_LAYER.md` for full specification.
