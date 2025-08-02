"""Date conversion utilities for Logseq journal pages.

This module provides functions to convert various date formats into
Logseq's journal page naming format.
"""

import re
from datetime import date, datetime


def date_to_journal_format(input_date: str | date | datetime) -> str:
    """Convert a date to Logseq's journal page format.

    Logseq uses abbreviated month format for journal pages like "Dec 25th, 2023".
    This function converts various date inputs to that format.

    Args:
        input_date: Date input in various formats:
            - ISO string: "2023-12-25"
            - Date string: "12/25/2023", "25-12-2023"
            - Python date or datetime object
            - Already formatted: "Dec 25th, 2023"

    Returns:
        Formatted journal page name (e.g., "Dec 25th, 2023")

    Raises:
        ValueError: If the date format cannot be parsed

    Examples:
        >>> date_to_journal_format("2023-12-25")
        "Dec 25th, 2023"

        >>> date_to_journal_format(datetime(2023, 12, 25))
        "Dec 25th, 2023"

        >>> date_to_journal_format("Dec 25th, 2023")
        "Dec 25th, 2023"
    """
    # If already a date/datetime object
    if isinstance(input_date, datetime):
        dt = input_date.date()
    elif isinstance(input_date, date):
        dt = input_date
    else:
        # Try to parse string input
        date_str = str(input_date).strip()

        # Check if already in journal format (abbreviated month)
        journal_pattern = r"^[A-Za-z]{3} \d{1,2}(st|nd|rd|th), \d{4}$"
        if re.match(journal_pattern, date_str):
            return date_str

        # Try various date formats
        formats = [
            "%Y-%m-%d",  # ISO format
            "%Y/%m/%d",  # Alternative ISO
            "%m/%d/%Y",  # US format
            "%d/%m/%Y",  # EU format
            "%m-%d-%Y",  # US with dashes
            "%d-%m-%Y",  # EU with dashes
            "%Y%m%d",  # Compact format
            "%B %d, %Y",  # Full month name
            "%b %d, %Y",  # Abbreviated month
        ]

        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue

        if dt is None:
            raise ValueError(f"Cannot parse date: {input_date}")

    # Format to Logseq journal format
    day = dt.day

    # Add ordinal suffix
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format: "Dec 25th, 2023" (abbreviated month)
    return dt.strftime(f"%b {day}{suffix}, %Y")


def journal_format_to_date(journal_name: str) -> date:
    """Convert Logseq journal format back to a Python date object.

    Args:
        journal_name: Journal page name (e.g., "Dec 25th, 2023")

    Returns:
        Python date object

    Raises:
        ValueError: If the format cannot be parsed

    Examples:
        >>> journal_format_to_date("Dec 25th, 2023")
        datetime.date(2023, 12, 25)
    """
    import re

    # Remove ordinal suffixes
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", journal_name)

    # Parse the cleaned date (abbreviated month format)
    try:
        return datetime.strptime(cleaned, "%b %d, %Y").date()
    except ValueError as e:
        raise ValueError(f"Cannot parse journal format: {journal_name}") from e
