"""
Utility helpers
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def truncate(text: str, max_len: int = 40) -> str:
    """Truncate *text* to *max_len* characters."""
    if not text:
        return ''
    return text if len(text) <= max_len else text[: max_len - 1] + '\u2026'


def safe_str(value: Any, default: str = '') -> str:
    """Convert *value* to string, returning *default* on None."""
    if value is None:
        return default
    return str(value)
