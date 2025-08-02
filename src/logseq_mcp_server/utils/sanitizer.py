"""Log sanitization utilities for privacy protection.

This module provides comprehensive sanitization functionality to protect
sensitive user data in logs while maintaining useful debugging information.
The sanitizer ensures that personal information like page names, content,
file paths, and queries are partially or fully obfuscated based on context.

Example:
    >>> sanitizer = LogSanitizer()
    >>> sanitizer.sanitize_page_name("My Private Journal")
    'My P***nal'
    >>> sanitizer.sanitize_content("Secret meeting notes")
    '[content_19_chars]'
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union


class LogSanitizer:
    """Sanitizes sensitive data in log messages.
    
    This class provides methods to sanitize various types of sensitive data
    that might appear in logs, including page names, content, file paths,
    block IDs, properties, and queries. The sanitization preserves some
    information for debugging while protecting user privacy.
    
    Attributes:
        min_mask_length: Minimum string length required for masking.
                        Strings shorter than this are left unchanged.
    """

    def __init__(self, min_mask_length: int = 3):
        """Initialize the sanitizer.

        Args:
            min_mask_length: Minimum length of string to partially mask.
                           Defaults to 3 to avoid masking very short strings.
        """
        self.min_mask_length = min_mask_length

    def sanitize_page_name(self, name: Optional[str]) -> str:
        """Partially mask page names to protect privacy.
        
        Page names are masked by showing the first and last portions of the
        name while hiding the middle section. Very short names are left
        unchanged, and journal pages are completely replaced with a marker.

        Args:
            name: The page name to sanitize. Can be None.

        Returns:
            Sanitized page name with middle portion masked, or special
            markers for empty/journal pages.

        Examples:
            >>> sanitizer.sanitize_page_name("My Private Journal")
            'My P***nal'
            >>> sanitizer.sanitize_page_name("TODO")
            'TODO'  # Too short to mask
            >>> sanitizer.sanitize_page_name("December 25th, 2023")
            '[journal_page]'
            >>> sanitizer.sanitize_page_name(None)
            '[empty]'
        """
        if not name:
            return "[empty]"

        if len(name) <= self.min_mask_length:
            return name

        # For journal pages, just indicate it's a journal
        if re.match(r"^\w+\s+\d+\w*,\s+\d{4}$", name):
            return "[journal_page]"

        # Mask middle portion of the name
        visible_chars = max(1, len(name) // 4)
        if len(name) <= 8:
            # Short names: show first and last char
            return f"{name[0]}***{name[-1]}"
        else:
            # Longer names: show more context
            start = name[:visible_chars]
            end = name[-visible_chars:]
            return f"{start}***{end}"

    def sanitize_content(self, content: Optional[str]) -> str:
        """Replace content with length indicator.

        Examples:
            "Meeting notes..." -> "[content_16_chars]"
            None -> "[empty]"
        """
        if not content:
            return "[empty]"

        # Just return length info, no content
        return f"[content_{len(content)}_chars]"

    def sanitize_block_id(self, block_id: Optional[str]) -> str:
        """Anonymize block IDs while keeping them traceable.

        Examples:
            "550e8400-e29b-41d4-a716-446655440000" -> "block_a1b2c3"
        """
        if not block_id:
            return "[empty]"

        # Create a short hash for correlation without revealing actual ID
        hash_obj = hashlib.sha256(block_id.encode())
        short_hash = hash_obj.hexdigest()[:6]
        return f"block_{short_hash}"

    def sanitize_path(self, path: Optional[Union[str, Path]]) -> str:
        """Mask username and sensitive parts in file paths.

        Examples:
            "/Users/john/Documents/Logseq" -> "/Users/***/Documents/Logseq"
            "/home/jane/graphs/work" -> "/home/***/graphs/***"
        """
        if not path:
            return "[empty]"

        path_str = str(path)

        # Common patterns to mask
        patterns = [
            # Unix home directories
            (r"/home/([^/]+)", r"/home/***"),
            (r"/Users/([^/]+)", r"/Users/***"),
            # Windows paths
            (r"C:\\Users\\([^\\]+)", r"C:\\Users\\***"),
            (r"\\Users\\([^\\]+)", r"\\Users\\***"),
            # Graph names (often sensitive)
            (r"/graphs/([^/]+)", r"/graphs/***"),
            (r"\\graphs\\([^\\]+)", r"\\graphs\\***"),
        ]

        sanitized = path_str
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    def sanitize_properties(
        self, properties: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Redact sensitive property values.

        Keeps property keys but sanitizes values that might be sensitive.
        """
        if not properties:
            return {}

        # Keys that should always be redacted
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "key",
            "api_key",
            "email",
            "phone",
            "ssn",
            "credit_card",
        }

        # Keys that can be partially shown
        partial_keys = {"url", "link", "website", "domain"}

        sanitized = {}
        for key, value in properties.items():
            lower_key = key.lower()

            if any(sensitive in lower_key for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif any(partial in lower_key for partial in partial_keys):
                if isinstance(value, str) and len(value) > 10:
                    # Show domain for URLs
                    domain_match = re.search(r"https?://([^/]+)", value)
                    if domain_match:
                        sanitized[key] = f"{domain_match.group(1)}/***"
                    else:
                        sanitized[key] = f"{value[:10]}***"
                else:
                    sanitized[key] = value
            elif isinstance(value, str) and len(value) > 50:
                # Long string values might be sensitive
                sanitized[key] = f"[string_{len(value)}_chars]"
            elif isinstance(value, (list, dict)) and len(str(value)) > 100:
                # Complex values
                sanitized[key] = f"[{type(value).__name__}_with_{len(value)}_items]"
            else:
                # Keep non-sensitive values
                sanitized[key] = value

        return sanitized

    def sanitize_query(self, query: Optional[str]) -> str:
        """Sanitize Datalog queries to hide search patterns.

        Examples:
            "[:find ?b :where [?b :block/content ?c] [(clojure.string/includes? ?c \"password\")]]"
            -> "[datalog_query_76_chars]"
        """
        if not query:
            return "[empty]"

        # Queries can reveal search patterns, so just show type and length
        return f"[datalog_query_{len(query)}_chars]"

    def sanitize_dict(
        self, data: Dict[str, Any], rules: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Sanitize a dictionary based on rules.
        
        Recursively sanitizes dictionary values based on a set of rules that
        map dictionary keys to sanitization methods. Handles nested dictionaries
        and lists of dictionaries. Non-sensitive data is preserved as-is.

        Args:
            data: Dictionary to sanitize. Can contain nested structures.
            rules: Optional mapping of keys to sanitization method names.
                  Keys are dictionary keys to look for, values are method
                  names without the 'sanitize_' prefix.
                  Example: {"page_name": "page_name", "content": "content"}
                  If None, uses default rules for common Logseq fields.

        Returns:
            New dictionary with sanitized values. Original data is not modified.

        Examples:
            >>> data = {"page_name": "Secret Page", "count": 42}
            >>> sanitizer.sanitize_dict(data)
            {'page_name': 'Se***ge', 'count': 42}
        """
        if not rules:
            rules = {
                "page_name": "page_name",
                "page": "page_name",
                "name": "page_name",
                "content": "content",
                "block_content": "content",
                "path": "path",
                "file_path": "path",
                "properties": "properties",
                "query": "query",
                "block_id": "block_id",
                "uuid": "block_id",
            }

        sanitized = {}
        for key, value in data.items():
            if key in rules and not isinstance(value, (dict, list)):
                # Apply rule only if value is not a complex type
                method_name = f"sanitize_{rules[key]}"
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    sanitized[key] = method(value)
                else:
                    sanitized[key] = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self.sanitize_dict(value, rules)
            elif isinstance(value, list) and len(value) > 0:
                # For lists, sanitize if items are dicts
                if isinstance(value[0], dict):
                    sanitized[key] = [self.sanitize_dict(item, rules) for item in value]
                else:
                    sanitized[key] = f"[list_with_{len(value)}_items]"
            elif isinstance(value, (str, int, float, bool, type(None))):
                # Keep non-sensitive simple data
                sanitized[key] = value
            else:
                sanitized[key] = f"[{type(value).__name__}]"

        return sanitized
