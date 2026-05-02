"""Test configuration and fixtures."""

import os
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_u2_device():
    """Mock uiautomator2.Device for testing."""
    mock = MagicMock()
    mock.info = {"displayWidth": 1080, "displayHeight": 1920}
    mock.screenshot.return_value = MagicMock(tobytes=lambda: b"fake_png_data")
    mock.dump_hierarchy.return_value = "<hierarchy><node text=\"Home\"/></hierarchy>"
    mock.touch.down = MagicMock()
    mock.touch.move = MagicMock()
    mock.touch.up = MagicMock()
    mock.click = MagicMock()
    mock.press = MagicMock()
    mock.send_keys = MagicMock()
    mock.sleep = lambda x: None  # No-op sleep for tests
    mock.set_fastinput_ime = MagicMock()
    
    # Mock element finding
    def find_element(**kwargs):
        elem_mock = MagicMock()
        elem_mock.exists.return_value = True
        elem_mock.wait = MagicMock(return_value=elem_mock)
        elem_mock.click = MagicMock()
        elem_mock.info = {
            "bounds": {"left": 100, "top": 200, "right": 300, "bottom": 400}
        }
        return elem_mock
    
    mock.__call__ = find_element
    return mock


@pytest.fixture
def mock_adb_client():
    """Mock AdbClient for testing."""
    mock = MagicMock()
    mock.connect.return_value = True
    mock.disconnect = MagicMock()
    mock.shell.return_value = "ok"
    mock.list_devices.return_value = []
    mock.check_connection.return_value = True
    mock.reconnect.return_value = True
    return mock


@pytest.fixture
def mock_device(mock_adb_client):
    """Mock Device for testing."""
    from uuid import uuid4
    from accfarm_device.device import Device, DeviceStatus
    
    device = Device(
        id=uuid4(),
        serial="TEST_SERIAL_001",
        name="Test Device",
        ip="192.168.1.100",
        adb_port=5555,
        status=DeviceStatus.IDLE,
    )
    device.set_adb_client(mock_adb_client)
    return device


@pytest.fixture
def real_phone_ip():
    """Get real phone IP from environment for integration tests."""
    ip = os.environ.get("ACCFARM_TEST_PHONE_IP")
    if not ip:
        pytest.skip("ACCFARM_TEST_PHONE_IP not set, skipping integration test")
    return ip
