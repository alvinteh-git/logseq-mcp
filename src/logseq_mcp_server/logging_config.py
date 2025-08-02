"""Logging configuration for the Logseq MCP server."""

import copy
import json
import logging
import logging.handlers
import os
import re
import sys
import typing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .utils.sanitizer import LogSanitizer


class LoggingMode(Enum):
    """Logging modes for different privacy levels."""

    PRIVACY = "privacy"  # Default: Sanitized logs
    DEBUG = "debug"  # Full details for troubleshooting
    MINIMAL = "minimal"  # Only errors and warnings


class PrivacyFilter(logging.Filter):
    """Filter that sanitizes sensitive data in log records."""

    def __init__(self, mode: LoggingMode = LoggingMode.PRIVACY):
        """Initialize the privacy filter.

        Args:
            mode: The logging mode to use
        """
        super().__init__()
        self.mode = mode
        self.sanitizer = LogSanitizer()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize log records based on mode.

        Args:
            record: The log record to filter

        Returns:
            True to include the record, False to exclude it
        """
        # In minimal mode, only allow warnings and errors
        if self.mode == LoggingMode.MINIMAL:
            if record.levelno < logging.WARNING:
                return False

        # In privacy mode, sanitize sensitive data
        if self.mode == LoggingMode.PRIVACY:
            # Sanitize the main message
            if hasattr(record, "msg") and isinstance(record.msg, str):
                # Look for common patterns in messages
                def sanitize_page_pattern(m: re.Match[str]) -> str:
                    return f"page: '{self.sanitizer.sanitize_page_name(m.group(1))}'"

                def sanitize_getting_page(m: re.Match[str]) -> str:
                    return (
                        f"Getting page: {self.sanitizer.sanitize_page_name(m.group(1))}"
                    )

                def sanitize_creating_page(m: re.Match[str]) -> str:
                    return f"Creating page: {self.sanitizer.sanitize_page_name(m.group(1))}"

                def sanitize_search_query(m: re.Match[str]) -> str:
                    return f"Searching pages with query: {self.sanitizer.sanitize_query(m.group(1))}"

                def sanitize_datalog_query(m: re.Match[str]) -> str:
                    return f"Executing Datalog query: {self.sanitizer.sanitize_query(m.group(1))}"

                patterns: list[tuple[str, typing.Callable[[re.Match[str]], str]]] = [
                    (r"page: ['\"]([^'\"]+)['\"]", sanitize_page_pattern),
                    (r"Getting page: ([^'\"]+)", sanitize_getting_page),
                    (r"Creating page: ([^'\"]+)", sanitize_creating_page),
                    (r"Searching pages with query: (.+)", sanitize_search_query),
                    (r"Executing Datalog query: (.+)", sanitize_datalog_query),
                ]
                for pattern, replacement in patterns:
                    record.msg = re.sub(pattern, replacement, record.msg)

            # Sanitize extra fields - IMPORTANT: Use deep copies to avoid modifying original data
            if hasattr(record, "arguments") and getattr(record, "arguments", None):
                # Deep copy to avoid modifying the original arguments
                arguments = getattr(record, "arguments")
                setattr(record, "arguments", copy.deepcopy(arguments))
                setattr(
                    record,
                    "arguments",
                    self.sanitizer.sanitize_dict(getattr(record, "arguments")),
                )

            if hasattr(record, "result") and isinstance(
                getattr(record, "result", None), dict
            ):
                # Deep copy the entire result to avoid modifying original data
                result = getattr(record, "result")
                setattr(record, "result", copy.deepcopy(result))

                # Now we can safely sanitize the copied data
                result = getattr(record, "result")
                if "page" in result:
                    if (
                        isinstance(result["page"], dict)
                        and "originalName" in result["page"]
                    ):
                        result["page"]["originalName"] = (
                            self.sanitizer.sanitize_page_name(
                                result["page"]["originalName"]
                            )
                        )
                if "pages" in result and isinstance(result["pages"], list):
                    result["pages"] = f"[list_with_{len(result['pages'])}_pages]"
                if "results" in result and isinstance(result["results"], list):
                    result["results"] = f"[list_with_{len(result['results'])}_results]"

        return True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        extra_fields = [
            "tool_name",
            "arguments",
            "result",
            "error",
            "duration_ms",
            "log_level",
            "log_file",
            "debug_mode",
            "log_mode",
            "max_file_size",
            "retention_days",
        ]

        for field in extra_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                if value is not None:
                    log_data[field] = value

        return json.dumps(log_data)


class StderrFilter(logging.Filter):
    """Filter to ensure only ERROR and above go to stderr."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Only allow ERROR and above."""
        return record.levelno >= logging.ERROR


def parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes."""
    size_str = size_str.upper().strip()
    if size_str.endswith("GB"):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    elif size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    else:
        return int(size_str)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_mode: Optional[str] = None,
    max_file_size: Optional[int] = None,
    backup_count: int = 5,
    retention_days: Optional[int] = None,
) -> None:
    """Configure logging for the MCP server.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path. If not provided, logs to a default location
        log_mode: Logging mode (privacy, debug, minimal). Defaults to privacy.
        max_file_size: Maximum size of log file before rotation (bytes). Defaults to 10MB.
        backup_count: Number of backup files to keep
        retention_days: Days to retain logs (used for time-based rotation)
    """
    # Get configuration from environment
    env_level = os.getenv("LOGSEQ_MCP_LOG_LEVEL", log_level)
    env_file = os.getenv("LOGSEQ_MCP_LOG_FILE", log_file)
    env_debug = os.getenv("LOGSEQ_MCP_DEBUG", "false").lower() == "true"
    env_mode = os.getenv("LOGSEQ_MCP_LOG_MODE", log_mode or "privacy")
    env_retention = os.getenv("LOGSEQ_MCP_LOG_RETENTION_DAYS")
    env_max_size = os.getenv("LOGSEQ_MCP_LOG_MAX_SIZE")

    # Parse logging mode
    try:
        mode = LoggingMode(env_mode.lower())
    except ValueError:
        mode = LoggingMode.PRIVACY

    # Parse retention days
    if env_retention:
        try:
            retention_days = int(env_retention)
        except ValueError:
            pass

    # Parse max file size
    if max_file_size is None:
        max_file_size = 10 * 1024 * 1024  # Default 10MB
    if env_max_size:
        try:
            max_file_size = parse_size(env_max_size)
        except ValueError:
            pass

    # Determine log file path
    if env_file is None:
        # Try to get project root from environment variable first
        project_root_env = os.getenv("LOGSEQ_MCP_PROJECT_ROOT")
        if project_root_env:
            project_root = Path(project_root_env)
        else:
            # Fallback to relative path from __file__
            project_root = Path(__file__).parent.parent.parent

        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Use retention-based naming if retention is set
        if retention_days:
            log_file_path = log_dir / "logseq-mcp.log"
        else:
            log_file_path = log_dir / f"logseq-mcp-{datetime.now():%Y%m%d}.log"
    else:
        log_file_path = Path(env_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, env_level.upper(), logging.INFO))

    # Remove default handlers
    root_logger.handlers.clear()

    # Create privacy filter
    privacy_filter = PrivacyFilter(mode)

    # Console formatter for human-readable output
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # JSON formatter for file output
    json_formatter = JSONFormatter()

    # File handler with rotation
    if retention_days:
        # Use time-based rotation
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
        )
        # Add date suffix to rotated files
        file_handler.suffix = ".%Y%m%d"
    else:
        # Use size-based rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(privacy_filter)
    root_logger.addHandler(file_handler)

    # Stderr handler for errors only (for Claude Desktop)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(console_formatter)
    stderr_handler.addFilter(StderrFilter())
    stderr_handler.addFilter(privacy_filter)
    root_logger.addHandler(stderr_handler)

    # Optionally add stdout handler for debugging
    if env_debug or mode == LoggingMode.DEBUG:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(console_formatter)
        # Don't apply privacy filter in debug mode console
        if mode != LoggingMode.DEBUG:
            stdout_handler.addFilter(privacy_filter)
        root_logger.addHandler(stdout_handler)

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging initialized",
        extra={
            "log_level": env_level,
            "log_file": str(log_file_path),
            "debug_mode": env_debug,
            "log_mode": mode.value,
            "max_file_size": max_file_size,
            "retention_days": retention_days,
        },
    )


def log_tool_invocation(
    logger: logging.Logger,
    tool_name: str,
    arguments: dict[str, Any],
    result: Any | None = None,
    error: Exception | None = None,
    duration_ms: float | None = None,
) -> None:
    """Log a tool invocation with structured data.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being invoked
        arguments: Tool arguments
        result: Tool result (if successful)
        error: Exception (if failed)
        duration_ms: Execution time in milliseconds
    """
    extra: dict[str, Any] = {
        "tool_name": tool_name,
        "arguments": arguments,
    }

    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    if error:
        extra["error"] = str(error)
        logger.error(
            f"Tool {tool_name} failed: {error}",
            extra=extra,
            exc_info=True,
        )
    else:
        extra["result"] = result
        logger.info(
            f"Tool {tool_name} completed successfully",
            extra=extra,
        )
