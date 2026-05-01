"""Custom exception hierarchy for the Device Layer."""


class DeviceLayerError(Exception):
    """Base exception for all device layer errors."""


class DeviceOfflineError(DeviceLayerError):
    """Phone is unreachable via ADB."""


class CloneNotFoundError(DeviceLayerError):
    """The com.instagram.androidX package doesn't exist on the phone."""


class CloneNotForegroundError(DeviceLayerError):
    """Our clone isn't the foreground app — something else stole focus."""


class ProxyError(DeviceLayerError):
    """Proxy is not reachable or returns wrong country."""


class CheckpointDetectedError(DeviceLayerError):
    """IG threw a verification screen — escalate to human."""


class DeviceMutexTimeoutError(DeviceLayerError):
    """Couldn't acquire the per-phone mutex within timeout."""
