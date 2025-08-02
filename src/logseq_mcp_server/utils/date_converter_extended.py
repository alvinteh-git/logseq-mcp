"""Extended date converter with multiple format support."""

from datetime import date, datetime
from .date_converter import date_to_journal_format as original_converter


def date_to_journal_format_abbreviated(input_date: str | date | datetime) -> str:
    """Convert date to abbreviated month format (e.g., 'Aug 1st, 2025')."""
    # First get the standard format
    full_format = original_converter(input_date)
    
    # Convert to abbreviated month
    month_map = {
        "January": "Jan", "February": "Feb", "March": "Mar",
        "April": "Apr", "May": "May", "June": "Jun",
        "July": "Jul", "August": "Aug", "September": "Sep",
        "October": "Oct", "November": "Nov", "December": "Dec"
    }
    
    for full, abbr in month_map.items():
        if full_format.startswith(full):
            return full_format.replace(full, abbr, 1)
    
    return full_format


def try_multiple_journal_formats(input_date: str | date | datetime) -> list[str]:
    """Generate multiple possible journal formats to try."""
    formats = []
    
    try:
        # Full month name
        formats.append(original_converter(input_date))
        
        # Abbreviated month
        formats.append(date_to_journal_format_abbreviated(input_date))
        
        # If it's already a string that looks like a date
        if isinstance(input_date, str):
            formats.append(input_date)
    except:
        pass
    
    return formats