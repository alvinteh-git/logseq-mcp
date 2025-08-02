"""Unit tests for MCP tools."""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import Tool

from logseq_mcp_server.tools.blocks import (
    create_block_tool,
    delete_block_tool,
    update_block_tool,
)
from logseq_mcp_server.tools.pages import (
    create_page_tool,
    get_all_pages_tool,
    get_page_tool,
    search_pages_tool,
)
from logseq_mcp_server.tools.queries import execute_query_tool
from logseq_mcp_server.server import (
    handle_create_block,
    handle_update_block,
    handle_delete_block,
    handle_create_page,
    handle_get_page,
    handle_get_all_pages,
    handle_search_pages,
    handle_execute_query,
)


@pytest.fixture
def mock_client():
    """Create a mock LogseqClient."""
    client = AsyncMock()
    return client


class TestBlockTools:
    """Test block-related tools."""

    def test_create_block_tool_schema(self):
        """Test create_block tool schema."""
        assert isinstance(create_block_tool, Tool)
        assert create_block_tool.name == "create_block"
        assert "content" in create_block_tool.inputSchema["properties"]
        assert "page" in create_block_tool.inputSchema["properties"]
        assert create_block_tool.inputSchema["required"] == ["content", "page"]

    def test_update_block_tool_schema(self):
        """Test update_block tool schema."""
        assert isinstance(update_block_tool, Tool)
        assert update_block_tool.name == "update_block"
        assert "block_id" in update_block_tool.inputSchema["properties"]
        assert update_block_tool.inputSchema["required"] == ["block_id"]

    def test_delete_block_tool_schema(self):
        """Test delete_block tool schema."""
        assert isinstance(delete_block_tool, Tool)
        assert delete_block_tool.name == "delete_block"
        assert "block_id" in delete_block_tool.inputSchema["properties"]
        assert delete_block_tool.inputSchema["required"] == ["block_id"]

    @pytest.mark.asyncio
    async def test_create_block_with_page(self, mock_client):
        """Test creating a block in a page."""
        mock_client.create_block.return_value = {
            "uuid": "new-block-uuid",
            "content": "Test content",
        }

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_block(
                {"content": "Test content", "page": "Test Page"}
            )

            mock_client.create_block.assert_called_once_with(
                content="Test content",
                page="Test Page",
                parent_block_id=None,
                properties=None,
            )

            assert result["success"] is True
            assert result["block"]["uuid"] == "new-block-uuid"

    @pytest.mark.asyncio
    async def test_create_block_with_parent(self, mock_client):
        """Test creating a block with parent block."""
        mock_client.create_block.return_value = {
            "uuid": "child-block-uuid",
            "content": "Child content",
        }

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_block(
                {"content": "Child content", "parent_block_id": "parent-uuid"}
            )

            mock_client.create_block.assert_called_once_with(
                content="Child content",
                page=None,
                parent_block_id="parent-uuid",
                properties=None,
            )

    @pytest.mark.asyncio
    async def test_create_block_with_properties(self, mock_client):
        """Test creating a block with properties."""
        mock_client.create_block.return_value = {"uuid": "block-uuid"}
        properties = {"tag": "important", "priority": "high"}

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_block(
                {
                    "content": "Block with props",
                    "page": "Test Page",
                    "properties": properties,
                }
            )

            mock_client.create_block.assert_called_once_with(
                content="Block with props",
                page="Test Page",
                parent_block_id=None,
                properties=properties,
            )

    @pytest.mark.asyncio
    async def test_create_block_validation_error(self, mock_client):
        """Test create_block with validation error."""
        mock_client.create_block.side_effect = ValueError(
            "Either page or parent_block_id must be provided"
        )

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_block(
                {
                    "content": "Test content"
                    # Missing both page and parent_block_id
                }
            )

            assert result["success"] is False
            assert "Either page or parent_block_id must be provided" in result["error"]

    @pytest.mark.asyncio
    async def test_update_block(self, mock_client):
        """Test updating a block."""
        mock_client.update_block.return_value = {
            "uuid": "block-uuid",
            "content": "Updated content",
        }

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_update_block(
                {"block_id": "block-uuid", "content": "Updated content"}
            )

            mock_client.update_block.assert_called_once_with(
                block_id="block-uuid", content="Updated content", properties=None
            )

            assert result["success"] is True
            assert result["block"]["uuid"] == "block-uuid"

    @pytest.mark.asyncio
    async def test_delete_block(self, mock_client):
        """Test deleting a block."""
        mock_client.delete_block.return_value = {"success": True}

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_delete_block({"block_id": "block-uuid"})

            mock_client.delete_block.assert_called_once_with(block_id="block-uuid")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_block_error(self, mock_client):
        """Test delete_block error handling."""
        mock_client.delete_block.side_effect = Exception("Delete failed")

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_delete_block({"block_id": "block-uuid"})

            assert result["success"] is False
            assert "Delete failed" in result["error"]


class TestPageTools:
    """Test page-related tools."""

    def test_create_page_tool_schema(self):
        """Test create_page tool schema."""
        assert isinstance(create_page_tool, Tool)
        assert create_page_tool.name == "create_page"
        assert "name" in create_page_tool.inputSchema["properties"]
        assert create_page_tool.inputSchema["required"] == ["name"]

    def test_get_page_tool_schema(self):
        """Test get_page tool schema."""
        assert isinstance(get_page_tool, Tool)
        assert get_page_tool.name == "get_page"
        assert "name" in get_page_tool.inputSchema["properties"]
        assert get_page_tool.inputSchema["required"] == ["name"]

    def test_get_all_pages_tool_schema(self):
        """Test get_all_pages tool schema."""
        assert isinstance(get_all_pages_tool, Tool)
        assert get_all_pages_tool.name == "get_all_pages"

    def test_search_pages_tool_schema(self):
        """Test search_pages tool schema."""
        assert isinstance(search_pages_tool, Tool)
        assert search_pages_tool.name == "search_pages"
        assert "query" in search_pages_tool.inputSchema["properties"]
        assert search_pages_tool.inputSchema["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_create_page(self, mock_client):
        """Test creating a page."""
        mock_client.create_page.return_value = {
            "uuid": "page-uuid",
            "originalName": "New Page",
            "name": "new page",
        }

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_page({"name": "New Page"})

            mock_client.create_page.assert_called_once_with(
                name="New Page", content=None
            )

            assert result["success"] is True
            assert result["page"]["uuid"] == "page-uuid"

    @pytest.mark.asyncio
    async def test_create_page_with_content(self, mock_client):
        """Test creating a page with initial content."""
        mock_client.create_page.return_value = {"uuid": "page-uuid", "name": "new page"}

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_create_page(
                {"name": "New Page", "content": "Initial content"}
            )

            mock_client.create_page.assert_called_once_with(
                name="New Page", content="Initial content"
            )

    @pytest.mark.asyncio
    async def test_get_page_found(self, mock_client):
        """Test getting an existing page."""
        mock_page = {
            "uuid": "page-uuid",
            "originalName": "Test Page",
            "name": "test page",
            "properties": {"type": "document"},
        }
        mock_blocks = [
            {"uuid": "block1", "content": "Block 1"},
            {"uuid": "block2", "content": "Block 2"},
        ]

        mock_client.get_page.return_value = mock_page
        mock_client.get_page_blocks.return_value = mock_blocks

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_get_page({"name": "Test Page"})

            mock_client.get_page.assert_called_once_with(name="Test Page")
            mock_client.get_page_blocks.assert_called_once_with(name="Test Page")

            assert result["success"] is True
            assert result["page"]["uuid"] == "page-uuid"
            assert len(result["blocks"]) == 2

    @pytest.mark.asyncio
    async def test_get_page_not_found(self, mock_client):
        """Test getting a non-existent page."""
        mock_client.get_page.return_value = None

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_get_page({"name": "NonExistent"})

            mock_client.get_page.assert_called_once_with(name="NonExistent")
            mock_client.get_page_blocks.assert_not_called()

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_all_pages(self, mock_client):
        """Test getting all pages."""
        mock_pages = [
            {"name": "Page 1", "uuid": "uuid1", "journal?": False},
            {"name": "jul 1st, 2024", "uuid": "uuid2", "journal?": True},
            {"name": "Page 3", "uuid": "uuid3", "journal?": False},
        ]

        mock_client.get_all_pages.return_value = mock_pages

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_get_all_pages({"include_journals": True})

            mock_client.get_all_pages.assert_called_once()

            assert result["success"] is True
            assert result["count"] == 3
            assert len(result["pages"]) == 3

    @pytest.mark.asyncio
    async def test_search_pages(self, mock_client):
        """Test searching pages."""
        mock_results = [
            {"name": "Test Page 1", "uuid": "uuid1"},
            {"name": "Test Page 2", "uuid": "uuid2"},
        ]

        mock_client.search_pages.return_value = mock_results

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_search_pages({"query": "test"})

            mock_client.search_pages.assert_called_once_with(query="test")

            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_search_pages_no_results(self, mock_client):
        """Test searching with no results."""
        mock_client.search_pages.return_value = []

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_search_pages({"query": "nonexistent"})

            assert result["success"] is True
            assert result["count"] == 0


class TestQueryTools:
    """Test query-related tools."""

    def test_execute_query_tool_schema(self):
        """Test execute_query tool schema."""
        assert isinstance(execute_query_tool, Tool)
        assert execute_query_tool.name == "execute_query"
        assert "query" in execute_query_tool.inputSchema["properties"]
        assert execute_query_tool.inputSchema["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_execute_query_success(self, mock_client):
        """Test executing a successful query."""
        mock_results = [["result1"], ["result2"]]

        mock_client.execute_query.return_value = mock_results

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_execute_query(
                {"query": "[:find ?p :where [?p :block/name]]"}
            )

            mock_client.execute_query.assert_called_once_with(
                query="[:find ?p :where [?p :block/name]]"
            )

            assert result["success"] is True
            assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_execute_query_empty_results(self, mock_client):
        """Test executing a query with no results."""
        mock_client.execute_query.return_value = []

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_execute_query(
                {"query": "[:find ?p :where [?p :nonexistent/attr]]"}
            )

            assert result["success"] is True
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_execute_query_error(self, mock_client):
        """Test query execution error."""
        mock_client.execute_query.side_effect = Exception("Invalid query syntax")

        with patch("logseq_mcp_server.server.logseq_client", mock_client):
            result = await handle_execute_query({"query": "invalid query"})

            assert result["success"] is False
            assert "Invalid query syntax" in result["error"]
