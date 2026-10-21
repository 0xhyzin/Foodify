"""MySQL DATETIME values are stored as UTC without timezone information."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
