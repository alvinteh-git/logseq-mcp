"""Tests for date conversion utilities."""

import pytest
from datetime import date, datetime

from logseq_mcp_server.utils.date_converter import date_to_journal_format, journal_format_to_date


class TestDateToJournalFormat:
    """Test date_to_journal_format function."""
    
    def test_iso_date_string(self):
        """Test conversion from ISO date string."""
        assert date_to_journal_format("2023-12-25") == "Dec 25th, 2023"
        assert date_to_journal_format("2023-01-01") == "Jan 1st, 2023"
        assert date_to_journal_format("2023-02-02") == "Feb 2nd, 2023"
        assert date_to_journal_format("2023-03-03") == "Mar 3rd, 2023"
        assert date_to_journal_format("2023-04-04") == "Apr 4th, 2023"
        assert date_to_journal_format("2023-12-11") == "Dec 11th, 2023"
        assert date_to_journal_format("2023-12-21") == "Dec 21st, 2023"
        assert date_to_journal_format("2023-12-22") == "Dec 22nd, 2023"
        assert date_to_journal_format("2023-12-23") == "Dec 23rd, 2023"
    
    def test_datetime_object(self):
        """Test conversion from datetime object."""
        dt = datetime(2023, 12, 25, 10, 30, 45)
        assert date_to_journal_format(dt) == "Dec 25th, 2023"
    
    def test_date_object(self):
        """Test conversion from date object."""
        d = date(2023, 12, 25)
        assert date_to_journal_format(d) == "Dec 25th, 2023"
    
    def test_us_date_format(self):
        """Test conversion from US date format."""
        assert date_to_journal_format("12/25/2023") == "Dec 25th, 2023"
        assert date_to_journal_format("01/01/2023") == "Jan 1st, 2023"
    
    def test_eu_date_format(self):
        """Test conversion from EU date format."""
        assert date_to_journal_format("25/12/2023") == "Dec 25th, 2023"
        assert date_to_journal_format("01/01/2023") == "Jan 1st, 2023"
    
    def test_already_formatted(self):
        """Test that already formatted dates are returned as-is."""
        assert date_to_journal_format("Dec 25th, 2023") == "Dec 25th, 2023"
        assert date_to_journal_format("Jan 1st, 2023") == "Jan 1st, 2023"
        assert date_to_journal_format("Feb 2nd, 2023") == "Feb 2nd, 2023"
        assert date_to_journal_format("Mar 3rd, 2023") == "Mar 3rd, 2023"
    
    def test_various_formats(self):
        """Test various other date formats."""
        assert date_to_journal_format("2023/12/25") == "Dec 25th, 2023"
        assert date_to_journal_format("12-25-2023") == "Dec 25th, 2023"
        assert date_to_journal_format("20231225") == "Dec 25th, 2023"
    
    def test_invalid_date_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Cannot parse date"):
            date_to_journal_format("not a date")
        
        with pytest.raises(ValueError, match="Cannot parse date"):
            date_to_journal_format("2023-13-01")  # Invalid month
        
        with pytest.raises(ValueError, match="Cannot parse date"):
            date_to_journal_format("2023-12-32")  # Invalid day


class TestJournalFormatToDate:
    """Test journal_format_to_date function."""
    
    def test_valid_journal_format(self):
        """Test conversion from journal format to date."""
        assert journal_format_to_date("Dec 25th, 2023") == date(2023, 12, 25)
        assert journal_format_to_date("Jan 1st, 2023") == date(2023, 1, 1)
        assert journal_format_to_date("Feb 2nd, 2023") == date(2023, 2, 2)
        assert journal_format_to_date("Mar 3rd, 2023") == date(2023, 3, 3)
        assert journal_format_to_date("Apr 4th, 2023") == date(2023, 4, 4)
    
    def test_invalid_journal_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Cannot parse journal format"):
            journal_format_to_date("Not a journal format")
        
        with pytest.raises(ValueError, match="Cannot parse journal format"):
            journal_format_to_date("25th December, 2023")  # Wrong order


class TestRoundTrip:
    """Test round-trip conversions."""
    
    def test_date_to_journal_and_back(self):
        """Test converting date to journal format and back."""
        original_date = date(2023, 12, 25)
        journal = date_to_journal_format(original_date)
        back_to_date = journal_format_to_date(journal)
        assert back_to_date == original_date
    
    def test_multiple_dates_round_trip(self):
        """Test round-trip for multiple dates."""
        test_dates = [
            date(2023, 1, 1),
            date(2023, 2, 2),
            date(2023, 3, 3),
            date(2023, 4, 4),
            date(2023, 12, 11),
            date(2023, 12, 21),
            date(2023, 12, 22),
            date(2023, 12, 23),
            date(2023, 12, 31),
        ]
        
        for d in test_dates:
            journal = date_to_journal_format(d)
            back = journal_format_to_date(journal)
            assert back == d, f"Round-trip failed for {d}: {journal}"