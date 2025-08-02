"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from logseq_mcp_server.logseq.client import LogseqClient


@pytest.fixture
async def mock_logseq_client():
    """Mock Logseq client for testing."""
    client = AsyncMock(spec=LogseqClient)

    # Mock common responses
    client.create_block.return_value = {
        "uuid": "test-block-123",
        "content": "Test content",
        "page": "Test Page",
    }

    client.get_page.return_value = {
        "uuid": "test-page-uuid",
        "originalName": "Test Page",
        "name": "test page",
        "properties": {},
    }

    client.get_page_blocks.return_value = []

    client.search_pages.return_value = [
        {"name": "Test Page 1", "uuid": "uuid1"},
        {"name": "Test Page 2", "uuid": "uuid2"},
    ]

    client.get_all_pages.return_value = []
    client.execute_query.return_value = []
    client.get_current_graph.return_value = {
        "name": "test-graph",
        "path": "/test/graph",
    }

    return client


@pytest.fixture
def test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("LOGSEQ_API_HOST", "localhost")
    monkeypatch.setenv("LOGSEQ_API_PORT", "12315")
    monkeypatch.setenv("LOGSEQ_MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOGSEQ_MCP_PROJECT_ROOT", str(Path(__file__).parent.parent))


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        "uuid": "block-123",
        "content": "Sample block content",
        "page": {"id": 1},
        "properties": {"tags": ["test", "sample"]},
        "parent": None,
        "children": [],
        "format": "markdown",
    }


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return {
        "uuid": "sample-page-uuid",
        "originalName": "Sample Page",
        "name": "sample page",
        "journal?": False,
        "createdAt": 1234567890000,
        "updatedAt": 1234567890000,
        "properties": {"type": "document"},
    }


@pytest.fixture
def sample_query_results():
    """Sample Datalog query results."""
    return [[1, "page-1"], [2, "page-2"], [3, "page-3"]]
