"""Tests for DevicePool."""

import threading
import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from accfarm_device.device import DeviceStatus
from accfarm_device.exceptions import DeviceMutexTimeoutError, DeviceOfflineError
from accfarm_device.pool import DevicePool


class TestDevicePool:
    """Tests for DevicePool class."""

    def test_register_device(self, mock_adb_client):
        """Test registering a device to the pool."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()
            device = pool.register_device(
                serial="TEST_001",
                ip="192.168.1.100",
                port=5555,
                name="Test Phone",
            )

            assert device.serial == "TEST_001"
            assert device.name == "Test Phone"
            assert device.ip == "192.168.1.100"
            assert device.adb_port == 5555
            assert device.status == DeviceStatus.IDLE

            # Verify device is in pool
            assert device.id in pool._devices
            assert "TEST_001" in pool._serial_to_id

    def test_unregister_device(self, mock_adb_client):
        """Test unregistering a device from the pool."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()
            device = pool.register_device(serial="TEST_001", ip="192.168.1.100")

            pool.unregister_device("TEST_001")

            assert device.id not in pool._devices
            assert "TEST_001" not in pool._serial_to_id

    def test_list_devices(self, mock_adb_client):
        """Test listing all devices in the pool."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()
            pool.register_device(serial="TEST_001", ip="192.168.1.100")
            pool.register_device(serial="TEST_002", ip="192.168.1.101")

            devices = pool.list_devices()

            assert len(devices) == 2
            serials = {d.serial for d in devices}
            assert serials == {"TEST_001", "TEST_002"}

    def test_get_device(self, mock_adb_client):
        """Test getting a device by ID."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()
            device = pool.register_device(serial="TEST_001", ip="192.168.1.100")

            retrieved = pool.get_device(device.id)

            assert retrieved.serial == "TEST_001"

    def test_get_device_not_found(self, mock_adb_client):
        """Test getting a non-existent device raises KeyError."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()

            with pytest.raises(KeyError):
                pool.get_device(uuid4())

    def test_acquire_releases_lock(self, mock_adb_client, mock_device):
        """Test that acquire context manager releases lock on exit."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            with patch("accfarm_device.pool.u2.connect"):
                pool = DevicePool()
                pool._devices[mock_device.id] = mock_device
                pool._serial_to_id[mock_device.serial] = mock_device.id
                pool._device_locks[mock_device.id] = threading.Lock()

                # Mock clone methods
                mock_clone = MagicMock()
                mock_clone.package_name = "com.instagram.androidp1"
                mock_clone.is_foreground.return_value = True
                mock_clone.launch = MagicMock()
                mock_clone.force_close = MagicMock()
                mock_device.list_clones = MagicMock(return_value=[mock_clone])

                with pool.acquire(mock_device.id, "com.instagram.androidp1"):
                    # Lock should be held
                    lock = pool._device_locks[mock_device.id]
                    assert lock.locked()

                # Lock should be released after context exits
                assert not lock.locked()
                mock_clone.force_close.assert_called()

    def test_mutex_serializes_concurrent_access(self, mock_adb_client, mock_device):
        """Test that concurrent acquires are serialized."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            with patch("accfarm_device.pool.u2.connect"):
                pool = DevicePool()
                pool._devices[mock_device.id] = mock_device
                pool._serial_to_id[mock_device.serial] = mock_device.id
                pool._device_locks[mock_device.id] = threading.Lock()

                # Mock clone
                mock_clone = MagicMock()
                mock_clone.package_name = "com.instagram.androidp1"
                mock_clone.is_foreground.return_value = True
                mock_clone.launch = MagicMock()
                mock_clone.force_close = MagicMock()
                mock_device.list_clones = MagicMock(return_value=[mock_clone])

                execution_order = []

                def worker(worker_id):
                    with pool.acquire(mock_device.id, "com.instagram.androidp1"):
                        execution_order.append(f"{worker_id}_start")
                        time.sleep(0.1)
                        execution_order.append(f"{worker_id}_end")

                # Start two workers concurrently
                t1 = threading.Thread(target=worker, args=(1,))
                t2 = threading.Thread(target=worker, args=(2,))

                t1.start()
                time.sleep(0.01)  # Ensure t1 starts first
                t2.start()

                t1.join(timeout=5)
                t2.join(timeout=5)

                # Verify serialization: worker 2 should start after worker 1 ends
                assert execution_order.index("1_start") < execution_order.index("1_end")
                assert execution_order.index("2_start") < execution_order.index("2_end")
                # One of them must complete before the other starts
                assert (
                    execution_order.index("1_end") < execution_order.index("2_start")
                    or execution_order.index("2_end") < execution_order.index("1_start")
                )

    def test_mutex_timeout(self, mock_adb_client, mock_device):
        """Test that acquiring lock times out if held too long."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            with patch("accfarm_device.pool.u2.connect"):
                pool = DevicePool()
                pool._devices[mock_device.id] = mock_device
                pool._serial_to_id[mock_device.serial] = mock_device.id
                pool._device_locks[mock_device.id] = threading.Lock()

                # Mock clone
                mock_clone = MagicMock()
                mock_clone.package_name = "com.instagram.androidp1"
                mock_clone.is_foreground.return_value = True
                mock_clone.launch = MagicMock()
                mock_clone.force_close = MagicMock()
                mock_device.list_clones = MagicMock(return_value=[mock_clone])

                # Hold the lock
                lock = pool._device_locks[mock_device.id]
                lock.acquire()

                try:
                    # Try to acquire with short timeout
                    with pytest.raises(DeviceMutexTimeoutError):
                        with pool.acquire(mock_device.id, "com.instagram.androidp1", timeout_seconds=1):
                            pass
                finally:
                    lock.release()

    def test_killswitch(self, mock_adb_client, mock_device):
        """Test killswitch stops all activity on a device."""
        with patch("accfarm_device.pool.AdbClient", return_value=mock_adb_client):
            pool = DevicePool()
            pool._devices[mock_device.id] = mock_device
            pool._serial_to_id[mock_device.serial] = mock_device.id
            lock = threading.Lock()
            lock.acquire()  # Simulate held lock
            pool._device_locks[mock_device.id] = lock

            mock_device.force_close_all_instagram = MagicMock()

            pool.killswitch(mock_device.id)

            mock_device.force_close_all_instagram.assert_called()
            mock_adb_client.disconnect.assert_called_with(mock_device.serial)
            assert mock_device.status == DeviceStatus.IDLE
