"""Selectors module."""

from accfarm_device.selectors.android_system import (
    ANR_SELECTORS,
    CRASH_SELECTORS,
    INSTALL_DIALOG_SELECTORS,
    PERMISSION_SELECTORS,
    PROXY_PROMPT_SELECTORS,
    STORAGE_SELECTORS,
    UPDATE_PROMPT_SELECTORS,
    handle_anr_dialog,
    handle_install_dialog,
    handle_permission_dialog,
)

__all__ = [
    "ANR_SELECTORS",
    "CRASH_SELECTORS",
    "INSTALL_DIALOG_SELECTORS",
    "PERMISSION_SELECTORS",
    "PROXY_PROMPT_SELECTORS",
    "STORAGE_SELECTORS",
    "UPDATE_PROMPT_SELECTORS",
    "handle_anr_dialog",
    "handle_install_dialog",
    "handle_permission_dialog",
]
