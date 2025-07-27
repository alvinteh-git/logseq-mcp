"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock

from logseq_mcp_server.logseq.client import LogseqClient


@pytest.fixture
async def mock_logseq_client():
    """Mock Logseq client for testing."""
    client = AsyncMock(spec=LogseqClient)
    
    # Mock common responses
    client.create_block.return_value = {
        "block_id": "test-block-123",
        "content": "Test content",
        "page": "Test Page",
    }
    
    client.get_page.return_value = {
        "name": "Test Page",
        "properties": {},
        "blocks": [],
    }
    
    client.search_pages.return_value = [
        {"name": "Test Page 1"},
        {"name": "Test Page 2"},
    ]
    
    return client


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        "id": "block-123",
        "content": "Sample block content",
        "page": "Sample Page",
        "properties": {"tags": ["test", "sample"]},
    }


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return {
        "name": "Sample Page",
        "properties": {"type": "document"},
        "blocks": [
            {
                "id": "block-1",
                "content": "First block",
            },
            {
                "id": "block-2",
                "content": "Second block",
            },
        ],
    }