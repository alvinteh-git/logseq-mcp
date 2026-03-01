"""Extended date converter with multiple format support."""

from datetime import date, datetime

from .date_converter import date_to_journal_format


def date_to_journal_format_full_month(input_date: str | date | datetime) -> str:
    """Convert date to full month format (e.g., 'August 1st, 2025').

    This is an alternative to the default abbreviated format used by some
    Logseq configurations.
    """
    abbreviated = date_to_journal_format(input_date)

    month_map = {
        "Jan": "January",
        "Feb": "February",
        "Mar": "March",
        "Apr": "April",
        "May": "May",
        "Jun": "June",
        "Jul": "July",
        "Aug": "August",
        "Sep": "September",
        "Oct": "October",
        "Nov": "November",
        "Dec": "December",
    }

    for abbr, full in month_map.items():
        if abbreviated.startswith(abbr + " "):
            return abbreviated.replace(abbr, full, 1)

    return abbreviated


def try_multiple_journal_formats(input_date: str | date | datetime) -> list[str]:
    """Generate multiple possible journal page names for a given date.

    Different Logseq installations use different journal naming formats.
    This returns all known variants so callers can try each one.
    """
    formats: list[str] = []

    try:
        # Abbreviated month (default): "Dec 25th, 2023"
        abbreviated = date_to_journal_format(input_date)
        formats.append(abbreviated)

        # Full month name: "December 25th, 2023"
        full = date_to_journal_format_full_month(input_date)
        if full != abbreviated:
            formats.append(full)

        # Raw string passthrough (user may have already formatted the date)
        if isinstance(input_date, str) and input_date not in formats:
            formats.append(input_date)
    except Exception:
        if isinstance(input_date, str):
            formats.append(input_date)

    return formats
