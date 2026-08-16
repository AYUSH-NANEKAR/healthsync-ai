"""
HealthSync AI - Date and Time Utilities

Provides consistent UTC timestamp handling for:

    - Database records
    - BLE readings
    - Device activity
    - Location history
    - Login sessions
    - AI reports

The application stores timestamps in UTC.
The UI can later convert them to the user's local time.
"""

from __future__ import annotations

from datetime import datetime, timezone


# ============================================================
# CURRENT UTC TIME
# ============================================================

def utc_now() -> datetime:
    """
    Return the current UTC datetime as a timezone-aware object.
    """

    return datetime.now(timezone.utc)


# ============================================================
# CURRENT UTC ISO TIMESTAMP
# ============================================================

def utc_now_iso() -> str:
    """
    Return the current UTC time as an ISO-8601 string.
    """

    return utc_now().isoformat()


# ============================================================
# DATETIME → ISO
# ============================================================

def datetime_to_iso(value: datetime) -> str:
    """
    Convert a datetime object into an ISO-8601 timestamp.
    """

    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime object.")

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.isoformat()


# ============================================================
# ISO → DATETIME
# ============================================================

def iso_to_datetime(value: str) -> datetime:
    """
    Convert an ISO-8601 timestamp into a datetime object.
    """

    if not isinstance(value, str):
        raise TypeError("value must be a string.")

    return datetime.fromisoformat(value)


# ============================================================
# UNIX TIMESTAMP
# ============================================================

def utc_timestamp() -> float:
    """
    Return the current UTC time as a Unix timestamp.
    """

    return utc_now().timestamp()


# ============================================================
# FORMAT FOR DISPLAY
# ============================================================

def format_datetime(
    value: datetime | str,
    format_string: str = "%d %b %Y, %I:%M %p",
) -> str:
    """
    Format a datetime for UI display.

    Example:
        16 Aug 2026, 03:20 PM
    """

    if isinstance(value, str):
        value = iso_to_datetime(value)

    if not isinstance(value, datetime):
        raise TypeError(
            "value must be a datetime or ISO timestamp."
        )

    return value.astimezone().strftime(format_string)


# ============================================================
# UTC CONVERSION
# ============================================================

def to_utc(value: datetime) -> datetime:
    """
    Convert a datetime to UTC.

    Naive datetime values are assumed to already represent UTC.
    """

    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime object.")

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "utc_now",
    "utc_now_iso",
    "datetime_to_iso",
    "iso_to_datetime",
    "utc_timestamp",
    "format_datetime",
    "to_utc",
]