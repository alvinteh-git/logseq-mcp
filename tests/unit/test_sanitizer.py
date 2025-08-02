"""Unit tests for log sanitizer."""

import pytest

from logseq_mcp_server.utils.sanitizer import LogSanitizer


class TestLogSanitizer:
    """Test the LogSanitizer class."""

    @pytest.fixture
    def sanitizer(self):
        """Create a sanitizer instance."""
        return LogSanitizer()

    def test_sanitize_page_name_empty(self, sanitizer):
        """Test sanitizing empty page names."""
        assert sanitizer.sanitize_page_name(None) == "[empty]"
        assert sanitizer.sanitize_page_name("") == "[empty]"

    def test_sanitize_page_name_short(self, sanitizer):
        """Test sanitizing short page names."""
        # Names <= min_mask_length are not masked
        assert sanitizer.sanitize_page_name("ABC") == "ABC"
        assert sanitizer.sanitize_page_name("XY") == "XY"

    def test_sanitize_page_name_journal(self, sanitizer):
        """Test sanitizing journal page names."""
        assert sanitizer.sanitize_page_name("Jul 1st, 2024") == "[journal_page]"
        assert sanitizer.sanitize_page_name("December 25th, 2023") == "[journal_page]"

    def test_sanitize_page_name_regular(self, sanitizer):
        """Test sanitizing regular page names."""
        # For "My Private Notes" (16 chars), visible_chars = 16//4 = 4
        assert sanitizer.sanitize_page_name("My Private Notes") == "My P***otes"
        # For "TODO List" (9 chars), visible_chars = 9//4 = 2
        assert sanitizer.sanitize_page_name("TODO List") == "TO***st"
        # For "Work" (4 chars), visible_chars = 1
        assert sanitizer.sanitize_page_name("Work") == "W***k"

    def test_sanitize_content(self, sanitizer):
        """Test content sanitization."""
        assert sanitizer.sanitize_content(None) == "[empty]"
        assert sanitizer.sanitize_content("") == "[empty]"
        assert sanitizer.sanitize_content("Hello World") == "[content_11_chars]"
        assert (
            sanitizer.sanitize_content("Secret password: 12345") == "[content_22_chars]"
        )

    def test_sanitize_block_id(self, sanitizer):
        """Test block ID anonymization."""
        assert sanitizer.sanitize_block_id(None) == "[empty]"
        assert sanitizer.sanitize_block_id("") == "[empty]"

        # Same input should produce same hash
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        result1 = sanitizer.sanitize_block_id(uuid)
        result2 = sanitizer.sanitize_block_id(uuid)
        assert result1 == result2
        assert result1.startswith("block_")
        assert len(result1) == 12  # "block_" + 6 chars

    def test_sanitize_path_unix(self, sanitizer):
        """Test Unix path sanitization."""
        assert sanitizer.sanitize_path("/home/john/Documents") == "/home/***/Documents"
        assert sanitizer.sanitize_path("/Users/jane/Logseq") == "/Users/***/Logseq"
        assert (
            sanitizer.sanitize_path("/home/user/graphs/work") == "/home/***/graphs/***"
        )

    def test_sanitize_path_windows(self, sanitizer):
        """Test Windows path sanitization."""
        assert (
            sanitizer.sanitize_path("C:\\Users\\john\\Documents")
            == "C:\\Users\\***\\Documents"
        )
        assert (
            sanitizer.sanitize_path("\\Users\\jane\\graphs\\personal")
            == "\\Users\\***\\graphs\\***"
        )

    def test_sanitize_properties_sensitive(self, sanitizer):
        """Test sanitizing sensitive properties."""
        props = {
            "password": "secret123",
            "api_key": "sk-1234567890",
            "email": "john@example.com",
            "normal": "value",
        }
        result = sanitizer.sanitize_properties(props)

        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["email"] == "[REDACTED]"
        assert result["normal"] == "value"

    def test_sanitize_properties_urls(self, sanitizer):
        """Test sanitizing URL properties."""
        props = {
            "url": "https://example.com/secret/path",
            "website": "http://mysite.com/private",
            "link": "short",
        }
        result = sanitizer.sanitize_properties(props)

        assert result["url"] == "example.com/***"
        assert result["website"] == "mysite.com/***"
        assert result["link"] == "short"  # Too short to sanitize

    def test_sanitize_properties_long_values(self, sanitizer):
        """Test sanitizing long property values."""
        props = {
            "description": "A" * 60,  # Long string
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],  # Long list
            "metadata": {
                "key1": "val1",
                "key2": "val2",
                "key3": "val3",
            },  # Complex dict
        }
        result = sanitizer.sanitize_properties(props)

        assert result["description"] == "[string_60_chars]"
        # Lists are not sanitized by sanitize_properties unless they're long (>100 chars when stringified)
        assert result["tags"] == ["tag1", "tag2", "tag3", "tag4", "tag5"]
        # Dicts are not sanitized unless they're long
        assert result["metadata"] == {"key1": "val1", "key2": "val2", "key3": "val3"}

    def test_sanitize_query(self, sanitizer):
        """Test query sanitization."""
        assert sanitizer.sanitize_query(None) == "[empty]"
        assert sanitizer.sanitize_query("") == "[empty]"

        query = '[:find ?b :where [?b :block/content ?c] [(clojure.string/includes? ?c "password")]]'
        # The actual length is 83, not 87
        assert sanitizer.sanitize_query(query) == f"[datalog_query_{len(query)}_chars]"

    def test_sanitize_dict_basic(self, sanitizer):
        """Test basic dictionary sanitization."""
        data = {
            "page_name": "My Private Page",
            "content": "Secret content here",
            "success": True,
            "count": 42,
        }
        result = sanitizer.sanitize_dict(data)

        # "My Private Page" (15 chars), visible = 15//4 = 3
        assert result["page_name"] == "My ***age"
        assert result["content"] == "[content_19_chars]"
        assert result["success"] is True
        assert result["count"] == 42

    def test_sanitize_dict_nested(self, sanitizer):
        """Test nested dictionary sanitization."""
        data = {
            "page": {"name": "Nested Page", "path": "/home/user/logseq"},
            "blocks": [
                {"content": "Block 1", "uuid": "uuid-1"},
                {"content": "Block 2", "uuid": "uuid-2"},
            ],
        }
        result = sanitizer.sanitize_dict(data)

        # "Nested Page" (11 chars), visible = 11//4 = 2
        assert result["page"]["name"] == "Ne***ge"
        assert result["page"]["path"] == "/home/***/logseq"
        assert result["blocks"][0]["content"] == "[content_7_chars]"
        # Check the actual hash for "uuid-1"
        import hashlib

        hash_val = hashlib.sha256("uuid-1".encode()).hexdigest()[:6]
        assert result["blocks"][0]["uuid"] == f"block_{hash_val}"

    def test_sanitize_dict_custom_rules(self, sanitizer):
        """Test dictionary sanitization with custom rules."""
        data = {"custom_field": "value", "page_name": "Test Page"}
        rules = {
            "custom_field": "content",  # Treat as content
            "page_name": "page_name",
        }
        result = sanitizer.sanitize_dict(data, rules)

        assert result["custom_field"] == "[content_5_chars]"
        # "Test Page" (9 chars), visible = 9//4 = 2
        assert result["page_name"] == "Te***ge"
