"""Integration tests for journal page tools."""

import json
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from logseq_mcp_server.server import handle_get_journal_page


@pytest.fixture
def mock_logseq_client():
    """Create a mock Logseq client."""
    client = AsyncMock()
    return client


class TestGetJournalPageTool:
    """Test get_journal_page tool integration."""
    
    @pytest.mark.asyncio
    async def test_get_journal_page_success(self, mock_logseq_client):
        """Test successful journal page retrieval."""
        # Mock response
        mock_page = {
            "uuid": "test-uuid-123",
            "originalName": "Dec 25th, 2023",
            "journal?": True,
            "properties": {},
        }
        mock_blocks = [
            {"uuid": "block-1", "content": "Test entry"},
            {"uuid": "block-2", "content": "Another entry"},
        ]
        
        mock_logseq_client.get_page.return_value = mock_page
        mock_logseq_client.get_page_blocks_tree.return_value = mock_blocks
        
        # Patch the global client
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({
                "date": "2023-12-25",
                "include_children": True
            })
        
        assert result["success"] is True
        assert result["page"] == mock_page
        assert result["blocks"] == mock_blocks
        assert result["journal_name"] == "Dec 25th, 2023"
        
        # Verify the client was called with the converted journal name
        mock_logseq_client.get_page.assert_called_once_with(name="Dec 25th, 2023")
        mock_logseq_client.get_page_blocks_tree.assert_called_once_with("test-uuid-123")
    
    @pytest.mark.asyncio
    async def test_get_journal_page_various_date_formats(self, mock_logseq_client):
        """Test journal page retrieval with various date formats."""
        mock_page = {"uuid": "test-uuid", "originalName": "Dec 25th, 2023"}
        mock_logseq_client.get_page.return_value = mock_page
        mock_logseq_client.get_page_blocks_tree.return_value = []
        
        test_cases = [
            ("2023-12-25", "Dec 25th, 2023"),  # ISO format
            ("12/25/2023", "Dec 25th, 2023"),  # US format
            ("Dec 25th, 2023", "Dec 25th, 2023"),  # Already formatted
        ]
        
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            for date_input, expected_journal in test_cases:
                result = await handle_get_journal_page({"date": date_input})
                
                assert result["success"] is True
                assert result["journal_name"] == expected_journal
    
    @pytest.mark.asyncio
    async def test_get_journal_page_not_found(self, mock_logseq_client):
        """Test journal page not found."""
        mock_logseq_client.get_page.return_value = None
        
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({"date": "2023-12-25"})
        
        assert result["success"] is False
        assert result["page"] is None
        assert result["journal_name"] == "Dec 25th, 2023"
    
    @pytest.mark.asyncio
    async def test_get_journal_page_without_children(self, mock_logseq_client):
        """Test getting journal page without child blocks."""
        mock_page = {"uuid": "test-uuid", "originalName": "Dec 25th, 2023"}
        mock_logseq_client.get_page.return_value = mock_page
        
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({
                "date": "2023-12-25",
                "include_children": False
            })
        
        assert result["success"] is True
        assert result["page"] == mock_page
        assert "blocks" not in result
        assert result["journal_name"] == "Dec 25th, 2023"
        
        # Verify blocks were not fetched
        mock_logseq_client.get_page_blocks_tree.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_journal_page_invalid_date_format(self, mock_logseq_client):
        """Test journal page with invalid date format."""
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({"date": "not a date"})
        
        assert result["success"] is False
        assert "Invalid date format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_journal_page_missing_date(self, mock_logseq_client):
        """Test journal page without date parameter."""
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({})
        
        assert result["success"] is False
        assert result["error"] == "Date is required"
    
    @pytest.mark.asyncio
    async def test_get_journal_page_block_retrieval_failure(self, mock_logseq_client):
        """Test handling of block retrieval failure."""
        mock_page = {"uuid": "test-uuid", "originalName": "Dec 25th, 2023"}
        mock_logseq_client.get_page.return_value = mock_page
        mock_logseq_client.get_page_blocks_tree.side_effect = Exception("API error")
        
        with patch("logseq_mcp_server.server.logseq_client", mock_logseq_client):
            result = await handle_get_journal_page({
                "date": "2023-12-25",
                "include_children": True
            })
        
        # Should still succeed but with empty blocks
        assert result["success"] is True
        assert result["page"] == mock_page
        assert result["blocks"] == []
        assert result["journal_name"] == "Dec 25th, 2023"
    
    @pytest.mark.asyncio
    async def test_get_journal_page_client_not_initialized(self):
        """Test error when client is not initialized."""
        with patch("logseq_mcp_server.server.logseq_client", None):
            with pytest.raises(RuntimeError, match="Logseq client not initialized"):
                await handle_get_journal_page({"date": "2023-12-25"})