"""Tests for Clone class."""

from unittest.mock import MagicMock

import pytest

from accfarm_device.clone import Clone


class TestClone:
    """Tests for Clone class."""

    def test_clone_creation(self):
        """Test creating a clone with basic info."""
        clone = Clone(package_name="com.instagram.androidp1")

        assert clone.package_name == "com.instagram.androidp1"
        assert clone.label is None
        assert clone.version_name is None

    def test_detect_launch_activity_fallback(self, mock_device):
        """Test launch activity detection falls back to default."""
        clone = Clone(package_name="com.instagram.androidp1")

        # Mock adb client to return empty output
        mock_device._adb_client.shell.return_value = ""

        activity = clone._detect_launch_activity(mock_device)

        assert activity == "com.instagram.androidp1.activity.MainTabActivity"

    def test_detect_launch_activity_from_dumpsys(self, mock_device):
        """Test launch activity detection from dumpsys output."""
        clone = Clone(package_name="com.instagram.androidp1")

        # Mock dumpsys output with MAIN activity - format matches real output
        mock_device._adb_client.shell.return_value = """            android.intent.action.MAIN:
              2d2e3f4 com.instagram.androidp1.LaunchActivity filter 4a5b6c7
                Action: \"android.intent.action.MAIN\"
                Category: \"android.intent.category.LAUNCHER\"
"""

        activity = clone._detect_launch_activity(mock_device)

        assert activity == "com.instagram.androidp1.LaunchActivity"

    def test_force_close(self, mock_device):
        """Test force-closing a clone."""
        clone = Clone(package_name="com.instagram.androidp1")

        clone.force_close(mock_device)

        mock_device._adb_client.shell.assert_called_with(
            mock_device.serial,
            "am force-stop com.instagram.androidp1",
            timeout=10,
        )

    def test_is_foreground_true(self, mock_device):
        """Test is_foreground returns True when clone is in foreground."""
        clone = Clone(package_name="com.instagram.androidp1")

        # Mock mCurrentFocus output showing our package
        mock_device._adb_client.shell.return_value = (
            "mCurrentFocus=Window{com.instagram.androidp1/com.instagram.androidp1.activity.MainTabActivity}"
        )

        assert clone.is_foreground(mock_device) is True

    def test_is_foreground_false(self, mock_device):
        """Test is_foreground returns False when clone is not in foreground."""
        clone = Clone(package_name="com.instagram.androidp1")

        # Mock mCurrentFocus output showing different package
        mock_device._adb_client.shell.return_value = (
            "mCurrentFocus=Window{com.android.launcher3/com.android.launcher3.Launcher}"
        )

        assert clone.is_foreground(mock_device) is False

    def test_is_foreground_fallback_to_activities(self, mock_device):
        """Test is_foreground uses activities fallback."""
        clone = Clone(package_name="com.instagram.androidp1")

        # First call (window) returns nothing, second call (activities) shows our package
        def shell_side_effect(serial, cmd, timeout=10):
            if "mCurrentFocus" in cmd:
                return ""
            elif "mResumedActivity" in cmd:
                return "mResumedActivity: ActivityRecord{com.instagram.androidp1/.activity.MainTabActivity}"
            return ""

        mock_device._adb_client.shell.side_effect = shell_side_effect

        assert clone.is_foreground(mock_device) is True

    def test_clear_data(self, mock_device):
        """Test clearing clone data."""
        clone = Clone(package_name="com.instagram.androidp1")

        clone.clear_data(mock_device)

        mock_device._adb_client.shell.assert_called_with(
            mock_device.serial,
            "pm clear com.instagram.androidp1",
            timeout=10,
        )

    def test_refresh_info(self, mock_device):
        """Test refreshing clone information."""
        clone = Clone(package_name="com.instagram.androidp1")

        # Mock dumpsys output
        mock_device._adb_client.shell.return_value = """
            versionName=280.0.0.24.106
            label=Instagram Pro
        """

        clone.refresh_info(mock_device)

        assert clone.version_name == "280.0.0.24.106"
        assert clone.label == "Instagram Pro"
