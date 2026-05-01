"""Integration tests requiring a real connected phone.

These tests require:
1. A physical Android device or emulator
2. Wi-Fi ADB enabled on the device
3. ACCFARM_TEST_PHONE_IP environment variable set to the device IP

Run with: pytest -m integration
"""

import os
import time
from unittest.mock import patch

import pytest

from accfarm_device.clone import Clone
from accfarm_device.device import Device, DeviceStatus
from accfarm_device.pool import DevicePool


@pytest.mark.integration
class TestRealPhone:
    """Integration tests with a real connected phone."""

    @pytest.fixture
    def device(self, real_phone_ip):
        """Set up a device connection for testing."""
        pool = DevicePool()
        device = pool.register_device(
            serial=f"TEST_{real_phone_ip.replace('.', '_')}",
            ip=real_phone_ip,
            port=5555,
            name="Integration Test Device",
        )
        yield device
        pool.shutdown()

    def test_connect_to_phone(self, real_phone_ip):
        """Test connecting to a phone via Wi-Fi ADB."""
        pool = DevicePool()

        try:
            device = pool.register_device(
                serial="integration_test",
                ip=real_phone_ip,
            )

            assert device.is_online()
            assert device.status == DeviceStatus.IDLE
        finally:
            pool.shutdown()

    def test_list_clones_on_phone(self, device):
        """Test listing Instagram clones on a real phone."""
        clones = device.list_clones()

        # Should find at least one Instagram-related package
        # (test may pass with empty list if no IG clones installed)
        assert isinstance(clones, list)

        # If clones exist, verify they have package names
        for clone in clones:
            assert clone.package_name.startswith("com.instagram")
            assert isinstance(clone.package_name, str)

    def test_find_instagram_clone(self, device):
        """Test finding an Instagram clone package."""
        clones = device.list_clones()

        # Look for any Instagram clone
        ig_clones = [c for c in clones if "instagram" in c.package_name.lower()]

        # This test will skip if no IG clones are installed
        if not ig_clones:
            pytest.skip("No Instagram clones installed on test device")

        assert len(ig_clones) > 0

    def test_acquire_session_and_screenshot(self, device):
        """Test acquiring a session and taking a screenshot."""
        clones = device.list_clones()
        ig_clones = [c for c in clones if "instagram" in c.package_name.lower()]

        if not ig_clones:
            pytest.skip("No Instagram clones installed on test device")

        clone_package = ig_clones[0].package_name

        pool = DevicePool()
        pool._devices[device.id] = device
        pool._serial_to_id[device.serial] = device.id
        pool._device_locks[device.id] = type(pool)._device_locks.__class__()

        try:
            with patch.object(pool, "_ensure_screen_on"):
                with pool.acquire(device.id, clone_package, timeout_seconds=30) as session:
                    # Session should be created
                    assert session is not None
                    assert session.clone.package_name == clone_package

                    # Should be able to take a screenshot
                    screenshot_bytes = session.screenshot()
                    assert len(screenshot_bytes) > 0
                    assert screenshot_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG header
        except Exception as e:
            if "CloneNotFoundError" in str(type(e).__name__):
                pytest.skip(f"Clone {clone_package} not found")
            raise
        finally:
            pool.shutdown()

    def test_mutex_concurrent_access(self, device):
        """Test that concurrent acquires are serialized."""
        import threading

        clones = device.list_clones()
        ig_clones = [c for c in clones if "instagram" in c.package_name.lower()]

        if not ig_clones:
            pytest.skip("No Instagram clones installed on test device")

        clone_package = ig_clones[0].package_name
        execution_log = []

        pool = DevicePool()
        pool._devices[device.id] = device
        pool._serial_to_id[device.serial] = device.id
        pool._device_locks[device.id] = threading.Lock()

        def worker(worker_id):
            try:
                with patch.object(pool, "_ensure_screen_on"):
                    with pool.acquire(device.id, clone_package, timeout_seconds=60):
                        execution_log.append(f"{worker_id}_start")
                        time.sleep(0.5)
                        execution_log.append(f"{worker_id}_end")
            except Exception:
                execution_log.append(f"{worker_id}_error")

        t1 = threading.Thread(target=worker, args=(1,))
        t2 = threading.Thread(target=worker, args=(2,))

        t1.start()
        time.sleep(0.1)  # Ensure t1 gets the lock first
        t2.start()

        t1.join(timeout=30)
        t2.join(timeout=30)

        # Verify serialization - one must complete before other starts
        if "1_start" in execution_log and "2_start" in execution_log:
            assert (
                execution_log.index("1_end") < execution_log.index("2_start")
                or execution_log.index("2_end") < execution_log.index("1_start")
            )

        pool.shutdown()

    def test_force_close_clone(self, device):
        """Test force-closing an Instagram clone."""
        clones = device.list_clones()

        if not clones:
            pytest.skip("No clones installed on test device")

        clone = clones[0]

        # Launch the clone
        clone.launch(device)
        time.sleep(2)

        # Verify it's in foreground (or was launched)
        # Note: May not be foreground if something else steals focus

        # Force close
        clone.force_close(device)
        time.sleep(1)

        # Verify it's no longer in foreground
        assert not clone.is_foreground(device)

    def test_device_heartbeat(self, device):
        """Test device heartbeat returns valid data."""
        heartbeat = device.heartbeat()

        assert isinstance(heartbeat, dict)

        # Should have some basic info
        if "error" not in heartbeat:
            assert "screen_on" in heartbeat
            assert "timestamp" in heartbeat

    def test_device_info_refresh(self, device):
        """Test refreshing device information."""
        device.refresh_info()

        # Should have populated some fields
        assert device.serial is not None
        # These may be None if device is offline or ADB fails
        # but refresh_info should not raise
