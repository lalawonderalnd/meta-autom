"""Exceptions for the Instagram bot."""

from __future__ import annotations


class CheckpointDetectedError(Exception):
    """Raised when Instagram shows a checkpoint/verification screen."""

    def __init__(self, kind: str, message: str | None = None):
        self.kind = kind
        self.message = message or f"Checkpoint detected: {kind}"
        super().__init__(self.message)


class RateLimitError(Exception):
    """Raised when Instagram rate-limits the account (soft warning)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(message)


class AccountBannedError(Exception):
    """Raised when Instagram has banned/disabled the account."""

    def __init__(self, message: str = "Account has been disabled"):
        self.message = message
        super().__init__(message)


class NotLoggedInError(Exception):
    """Raised when the account is not logged in to Instagram."""

    def __init__(self, message: str = "Not logged in"):
        self.message = message
        super().__init__(message)


class SelectorNotFoundError(Exception):
    """Raised when a required UI selector cannot be found."""

    def __init__(self, selector_name: str, ig_version: str | None = None):
        self.selector_name = selector_name
        self.ig_version = ig_version
        msg = f"Selector '{selector_name}' not found"
        if ig_version:
            msg += f" (IG version: {ig_version})"
        super().__init__(msg)


class ActionFailedError(Exception):
    """Raised when an action fails to complete."""

    def __init__(self, action_name: str, reason: str | None = None):
        self.action_name = action_name
        self.reason = reason
        msg = f"Action '{action_name}' failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
