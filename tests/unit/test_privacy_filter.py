"""Unit tests for the privacy filter to ensure data integrity."""

import copy
import logging
import pytest

from logseq_mcp_server.logging_config import PrivacyFilter, LoggingMode


class TestPrivacyFilter:
    """Test the PrivacyFilter class."""

    @pytest.fixture
    def privacy_filter(self):
        """Create a privacy filter instance."""
        return PrivacyFilter(LoggingMode.PRIVACY)

    def test_filter_does_not_modify_original_arguments(self, privacy_filter):
        """Test that filtering doesn't modify the original arguments dict."""
        # Create a log record with arguments
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add arguments as extra field (this is how log_tool_invocation does it)
        original_args = {
            "page_name": "My Private Page",
            "content": "Secret content",
            "nested": {"path": "/home/user/documents"},
        }
        record.arguments = original_args

        # Create a deep copy to compare against
        original_copy = copy.deepcopy(original_args)

        # Apply the filter
        privacy_filter.filter(record)

        # Verify original data is unchanged
        assert original_args == original_copy
        assert original_args["page_name"] == "My Private Page"
        assert original_args["content"] == "Secret content"
        assert original_args["nested"]["path"] == "/home/user/documents"

        # Verify the record's arguments were sanitized
        assert record.arguments != original_args
        assert record.arguments["page_name"] != "My Private Page"
        assert record.arguments["content"] != "Secret content"
        assert record.arguments["nested"]["path"] != "/home/user/documents"

    def test_filter_does_not_modify_original_result(self, privacy_filter):
        """Test that filtering doesn't modify the original result dict."""
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add result as extra field
        original_result = {
            "page": {
                "originalName": "My Secret Page",
                "uuid": "123-456-789",
                "properties": {"key": "value"},
            },
            "pages": ["page1", "page2", "page3"],
            "results": [{"id": 1}, {"id": 2}],
        }
        record.result = original_result

        # Create a deep copy to compare against
        original_copy = copy.deepcopy(original_result)

        # Apply the filter
        privacy_filter.filter(record)

        # Verify original data is unchanged
        assert original_result == original_copy
        assert original_result["page"]["originalName"] == "My Secret Page"
        assert original_result["pages"] == ["page1", "page2", "page3"]
        assert original_result["results"] == [{"id": 1}, {"id": 2}]

        # Verify the record's result was sanitized
        assert record.result != original_result
        assert record.result["page"]["originalName"] != "My Secret Page"
        assert record.result["pages"] == "[list_with_3_pages]"
        assert record.result["results"] == "[list_with_2_results]"

    def test_filter_handles_missing_fields(self, privacy_filter):
        """Test that the filter handles records without arguments/result fields."""
        # Create a basic log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise any errors
        result = privacy_filter.filter(record)
        assert result is True

        # Should not add the fields if they don't exist
        assert not hasattr(record, "arguments")
        assert not hasattr(record, "result")

    def test_filter_handles_non_dict_result(self, privacy_filter):
        """Test that the filter handles non-dict result values."""
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add non-dict result
        original_result = "string result"
        record.result = original_result

        # Apply the filter
        privacy_filter.filter(record)

        # String result should remain unchanged (filter only processes dicts)
        assert record.result == original_result

    def test_filter_in_debug_mode_preserves_data(self):
        """Test that debug mode doesn't sanitize data."""
        debug_filter = PrivacyFilter(LoggingMode.DEBUG)

        # Create a log record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Getting page: My Private Page",
            args=(),
            exc_info=None,
        )

        original_args = {"page_name": "My Private Page"}
        record.arguments = original_args

        # Apply the filter
        debug_filter.filter(record)

        # In debug mode, data should not be sanitized
        assert record.msg == "Getting page: My Private Page"
        assert record.arguments == original_args

    def test_deep_nested_structure_integrity(self, privacy_filter):
        """Test that deeply nested structures remain unmodified."""
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Create a deeply nested structure
        original_data = {
            "level1": {
                "level2": {
                    "level3": {"page_name": "Deep Secret", "items": ["a", "b", "c"]}
                }
            }
        }
        record.arguments = original_data

        # Store the object ID to verify it's the same object
        original_id = id(original_data)
        original_level3_id = id(original_data["level1"]["level2"]["level3"])

        # Apply the filter
        privacy_filter.filter(record)

        # Verify the original object hasn't changed
        assert id(original_data) == original_id
        assert id(original_data["level1"]["level2"]["level3"]) == original_level3_id
        assert original_data["level1"]["level2"]["level3"]["page_name"] == "Deep Secret"

        # Verify the sanitized copy is different
        assert (
            record.arguments["level1"]["level2"]["level3"]["page_name"] != "Deep Secret"
        )
