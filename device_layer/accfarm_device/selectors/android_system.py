"""Selectors for Android system dialogs."""

# Android system dialog selectors for common prompts

# Proxy configuration prompt (when app requests proxy settings)
PROXY_PROMPT_SELECTORS = {
    "wifi_proxy_settings": {
        "resourceId": "android:id/wifi_proxy_settings",
    },
    "proxy_hostname": {
        "resourceId": "android:id/proxy_hostname",
    },
    "proxy_port": {
        "resourceId": "android:id/proxy_port",
    },
    "proxy_submit": {
        "text": "Save",
    },
}

# Install confirmation dialog (Package installer)
INSTALL_DIALOG_SELECTORS = {
    "package_installer": {
        "packageName": "com.android.packageinstaller",
    },
    "install_button": {
        "text": "Install",
    },
    "open_button": {
        "text": "Open",
    },
    "done_button": {
        "text": "Done",
    },
    "cancel_button": {
        "text": "Cancel",
    },
}

# Permission grant dialogs
PERMISSION_SELECTORS = {
    "permission_dialog": {
        "resourceId": "android:id/permission_message",
    },
    "allow_button": {
        "text": "Allow",
    },
    "deny_button": {
        "text": "Deny",
    },
    "while_using_button": {
        "text": "While using the app",
    },
    "only_this_time_button": {
        "text": "Only this time",
    },
}

# System update prompts
UPDATE_PROMPT_SELECTORS = {
    "system_update": {
        "textContains": "System update",
    },
    "update_later": {
        "text": "Later",
    },
    "update_now": {
        "text": "Update",
    },
}

# Network connection prompts
NETWORK_SELECTORS = {
    "wifi_picker": {
        "resourceId": "android:id/wifi_list",
    },
    "connect_button": {
        "text": "Connect",
    },
    "forget_button": {
        "text": "Forget",
    },
}

# ANR (App Not Responding) dialog
ANR_SELECTORS = {
    "anr_dialog": {
        "textContains": "isn't responding",
    },
    "wait_button": {
        "text": "Wait",
    },
    "close_button": {
        "text": "Close",
    },
    "ok_button": {
        "text": "OK",
    },
}

# Crash dialog
CRASH_SELECTORS = {
    "crash_dialog": {
        "textContains": "has stopped",
    },
    "report_button": {
        "text": "Report",
    },
}

# Low storage warning
STORAGE_SELECTORS = {
    "low_storage": {
        "textContains": "storage",
        "textContains2": "running out",
    },
    "free_up_space": {
        "text": "Free up space",
    },
    "dismiss": {
        "text": "Dismiss",
    },
}


def get_selector(selector_type: str, selector_name: str) -> dict:
    """Get a selector by type and name."""
    selectors_map = {
        "proxy": PROXY_PROMPT_SELECTORS,
        "install": INSTALL_DIALOG_SELECTORS,
        "permission": PERMISSION_SELECTORS,
        "update": UPDATE_PROMPT_SELECTORS,
        "network": NETWORK_SELECTORS,
        "anr": ANR_SELECTORS,
        "crash": CRASH_SELECTORS,
        "storage": STORAGE_SELECTORS,
    }

    selector_dict = selectors_map.get(selector_type, {})
    return selector_dict.get(selector_name, {})


def handle_install_dialog(u2_device) -> bool:
    """
    Handle package installer dialog - tap Install then Open/Done.
    Returns True if dialog was handled successfully.
    """
    try:
        # Wait for installer dialog
        install_btn = u2_device(text="Install")
        if install_btn.exists(timeout=5):
            install_btn.click()

            # Wait for installation to complete
            u2_device.sleep(3)

            # Tap Open or Done
            open_btn = u2_device(text="Open")
            if open_btn.exists(timeout=5):
                open_btn.click()
                return True

            done_btn = u2_device(text="Done")
            if done_btn.exists(timeout=5):
                done_btn.click()
                return True

        return False
    except Exception:
        return False


def handle_permission_dialog(u2_device, allow: bool = True) -> bool:
    """
    Handle permission dialog - tap Allow or Deny.
    Returns True if dialog was handled.
    """
    try:
        allow_btn = u2_device(text="Allow")
        deny_btn = u2_device(text="Deny")

        if allow:
            if allow_btn.exists(timeout=3):
                allow_btn.click()
                return True
            # Try "While using" variant
            while_using = u2_device(text="While using the app")
            if while_using.exists(timeout=3):
                while_using.click()
                return True
        else:
            if deny_btn.exists(timeout=3):
                deny_btn.click()
                return True

        return False
    except Exception:
        return False


def handle_anr_dialog(u2_device, wait: bool = True) -> bool:
    """
    Handle ANR dialog - tap Wait or Close.
    Returns True if dialog was handled.
    """
    try:
        if wait:
            btn = u2_device(text="Wait")
        else:
            btn = u2_device(text="Close")

        if btn.exists(timeout=3):
            btn.click()
            return True

        # Fallback to OK button
        ok_btn = u2_device(text="OK")
        if ok_btn.exists(timeout=3):
            ok_btn.click()
            return True

        return False
    except Exception:
        return False
