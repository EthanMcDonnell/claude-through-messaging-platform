"""
Security: sender validation, input sanitization, rate limiting.
"""

import re
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)

# Characters that could be dangerous if interpolated into shell commands or AppleScript
_APPLESCRIPT_ESCAPE_RE = re.compile(r'([\\"])')


def sanitize_for_applescript(text: str) -> str:
    """Escape backslashes and double-quotes for AppleScript string literals."""
    return _APPLESCRIPT_ESCAPE_RE.sub(r"\\\1", text)


def sanitize_prompt(text: str) -> str:
    """
    Sanitize user message before passing to Claude CLI.
    We pass text as a subprocess argument (not shell=True), so shell injection
    is already prevented. This does light cleaning for safety.
    """
    # Remove null bytes
    text = text.replace("\x00", "")
    # Truncate to 8000 chars to prevent token abuse
    return text[:8000]


def validate_sender(chat_identifier: str, allowed_sender: str) -> bool:
    """
    Check that the message came from the configured self-chat.
    chat_identifier is the phone number or email of the chat (normalized by macOS).
    """
    # Normalize: strip spaces, lowercase for email comparison
    def norm(s: str) -> str:
        return s.strip().lower().replace(" ", "")

    return norm(chat_identifier) == norm(allowed_sender)


class RateLimiter:
    """
    Sliding window rate limiter.
    Tracks events in a time window and rejects if limit exceeded.
    """

    def __init__(self, max_count: int, window_seconds: int):
        self.max_count = max_count
        self.window = window_seconds
        self._timestamps: deque[float] = deque()

    def allow(self) -> bool:
        """Return True if the event is allowed, False if rate limit exceeded."""
        now = time.time()
        # Evict old entries
        while self._timestamps and self._timestamps[0] < now - self.window:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_count:
            logger.warning(
                "Rate limit exceeded: %d events in %ds window",
                self.max_count,
                self.window,
            )
            return False

        self._timestamps.append(now)
        return True
