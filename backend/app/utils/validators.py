"""Shared date/month validation and parsing utilities.

All datetime objects produced by this module are timezone-aware (UTC).
Consumers that need naive datetimes must strip tzinfo themselves.
"""

import re
from datetime import datetime, timezone
from typing import Tuple


def validate_month_format(month: str) -> Tuple[bool, str]:
    """Validate that *month* is a well-formed YYYY-MM string.

    Checks:
    - Matches the pattern ``YYYY-MM`` (exactly four digits, hyphen, two digits).
    - Month number is between 01 and 12.
    - Year is between 1900 and 2100.

    Returns:
        ``(True, "")`` on success or ``(False, <reason>)`` on failure.
    """
    if not re.match(r"^\d{4}-\d{2}$", month):
        return False, "Month must be in YYYY-MM format"

    try:
        year_int = int(month[:4])
        month_int = int(month[5:7])

        if not (1 <= month_int <= 12):
            return False, "Month must be between 01 and 12"

        if year_int < 1900 or year_int > 2100:
            return False, "Year must be between 1900 and 2100"

        return True, ""
    except ValueError:
        return False, "Invalid month format"


def parse_month(month: str) -> datetime:
    """Parse a YYYY-MM string into a timezone-aware UTC datetime.

    Returns the first instant of the given month at midnight UTC.

    Args:
        month: A string in YYYY-MM format (e.g. "2026-04").

    Returns:
        A timezone-aware ``datetime`` set to midnight on the first of
        the given month in UTC.
    """
    dt = datetime.strptime(month, "%Y-%m")
    return dt.replace(tzinfo=timezone.utc)


def get_month_range(month: str) -> Tuple[datetime, datetime]:
    """Return the half-open UTC datetime range [start, end) for *month*.

    ``start`` is midnight on the first day of the month.
    ``end`` is midnight on the first day of the following month.
    Both values are timezone-aware (UTC).

    Args:
        month: A string in YYYY-MM format (e.g. "2026-04").

    Returns:
        ``(start_date, end_date)`` as a tuple of timezone-aware datetimes.
    """
    start_date = parse_month(month)
    year, month_num = start_date.year, start_date.month

    if month_num == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month_num + 1, 1, tzinfo=timezone.utc)

    return start_date, end_date