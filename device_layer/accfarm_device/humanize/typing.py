"""Human-like typing implementation with typos, autocomplete, and variable speed."""

from __future__ import annotations

import random
import time


def get_qwerty_neighbors(char: str) -> list[str]:
    """Get adjacent keys on QWERTY keyboard for typo simulation."""
    keyboard = {
        'q': ['w', 'a', 'tab'],
        'w': ['q', 'e', 'a', 's'],
        'e': ['w', 'r', 's', 'd'],
        'r': ['e', 't', 'd', 'f'],
        't': ['r', 'y', 'f', 'g'],
        'y': ['t', 'u', 'g', 'h'],
        'u': ['y', 'i', 'h', 'j'],
        'i': ['u', 'o', 'j', 'k'],
        'o': ['i', 'p', 'k', 'l'],
        'p': ['o', 'l'],
        'a': ['q', 'w', 's', 'z', 'caps'],
        's': ['w', 'e', 'a', 'd', 'z', 'x'],
        'd': ['e', 'r', 's', 'f', 'x', 'c'],
        'f': ['r', 't', 'd', 'g', 'c', 'v'],
        'g': ['t', 'y', 'f', 'h', 'v', 'b'],
        'h': ['y', 'u', 'g', 'j', 'b', 'n'],
        'j': ['u', 'i', 'h', 'k', 'n', 'm'],
        'k': ['i', 'o', 'j', 'l', 'm'],
        'l': ['o', 'p', 'k'],
        'z': ['a', 's', 'x'],
        'x': ['s', 'd', 'z', 'c'],
        'c': ['d', 'f', 'x', 'v'],
        'v': ['f', 'g', 'c', 'b'],
        'b': ['g', 'h', 'v', 'n'],
        'n': ['h', 'j', 'b', 'm'],
        'm': ['j', 'k', 'n'],
    }
    return keyboard.get(char.lower(), [])


def human_type(
    u2_device,
    text: str,
    *,
    wpm_range: tuple[int, int] = (40, 80),
    typo_rate: float = 0.04,
    use_suggestions: bool = True,
    backspace_delay_ms: int = 300,
) -> None:
    """
    Type letter-by-letter at human speed with realistic patterns.

    Args:
        u2_device: uiautomator2.Device instance
        text: Text to type
        wpm_range: Words per minute range for typing speed
        typo_rate: Probability of typing a wrong character
        use_suggestions: Whether to use autocomplete suggestions
        backspace_delay_ms: Delay after backspace before correcting
    """
    import numpy as np

    words = text.split()
    current_word = []

    for i, char in enumerate(text):
        if char == ' ':
            # Space - end of word, maybe check for suggestion
            if use_suggestions and current_word and len(current_word) >= 2:
                # 15% chance to tap autocomplete suggestion
                if random.random() < 0.15:
                    _try_autocomplete(u2_device, current_word)
            current_word = []
            # Space is usually faster
            sleep_time = np.random.lognormal(np.log(0.08), 0.3)
            time.sleep(max(0.03, min(sleep_time, 0.2)))
            u2_device.press("space")
            continue

        # Calculate delay based on WPM
        avg_wpm = (wpm_range[0] + wpm_range[1]) / 2
        avg_delay_per_char = 60 / (avg_wpm * 5)  # 5 chars per word average

        # Log-normal distribution for natural variation
        mean_log = np.log(avg_delay_per_char)
        sigma = 0.4
        delay = np.random.lognormal(mean_log, sigma)
        delay = max(0.05, min(delay, 0.5))  # Clamp between 50ms and 500ms

        # Decide whether to make a typo
        if char.isalpha() and random.random() < typo_rate:
            neighbors = get_qwerty_neighbors(char)
            if neighbors:
                typo_char = random.choice(neighbors)
                if typo_char not in ['tab', 'caps']:
                    # Type the wrong character
                    u2_device.send_keys(typo_char)
                    time.sleep(delay)

                    # Wait, then backspace and correct
                    wait_before_fix = random.uniform(0.2, 0.6)
                    time.sleep(wait_before_fix)

                    u2_device.press("backspace")
                    time.sleep(backspace_delay_ms / 1000.0)

                    # Type correct character
                    u2_device.send_keys(char)
                    time.sleep(delay)
                    current_word.append(char)
                    continue

        # Normal typing
        if char == '\n':
            u2_device.press("enter")
        elif char.isalpha() or char.isdigit() or char in '.,!?@#$%&*()_+-=[]{}|;:,.<>?':
            u2_device.send_keys(char)
        else:
            # For special characters, try send_keys anyway
            u2_device.send_keys(char)

        current_word.append(char)
        time.sleep(delay)


def _try_autocomplete(u2_device, word_chars: list[str]) -> None:
    """Try to tap an autocomplete suggestion from the IME."""
    # Look for suggestion in the suggestion bar
    # This is IME-dependent; Gboard shows suggestions in a row above keyboard
    try:
        # Try to find suggestion text (uiautomator2 can sometimes see IME views)
        # Look for resource IDs common in Gboard
        suggestion_patterns = [
            {"resourceId": "com.google.android.inputmethod.latin:id/suggestion_strip"},
            {"text": "".join(word_chars)[:3]},  # Partial match
        ]

        for pattern in suggestion_patterns:
            try:
                elem = u2_device(**pattern)
                if elem.exists(timeout=0.5):
                    elem.click()
                    return
            except Exception:
                continue
    except Exception:
        pass


def calculate_typing_duration(
    text: str,
    wpm_range: tuple[int, int] = (40, 80),
    typo_rate: float = 0.04,
) -> float:
    """
    Estimate how long typing will take.
    Useful for progress indicators and timeouts.

    Returns:
        Estimated duration in seconds
    """
    import numpy as np

    avg_wpm = (wpm_range[0] + wpm_range[1]) / 2
    num_words = len(text.split())
    num_chars = len(text)

    # Base time from WPM
    base_time = num_words / avg_wpm * 60

    # Add time for typos (backspace + retype + delay)
    alpha_chars = sum(1 for c in text if c.isalpha())
    expected_typos = alpha_chars * typo_rate
    typo_penalty = expected_typos * 0.5  # ~500ms per typo on average

    return base_time + typo_penalty
