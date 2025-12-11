"""Database utilities and helper functions."""

from datetime import datetime


def current_timestamp() -> datetime:
    """Get current timestamp for database defaults."""
    return datetime.now()
