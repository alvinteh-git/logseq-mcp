"""Unit tests for LogseqClient."""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from logseq_mcp_server.logseq.client import LogseqClient


@pytest.fixture
def client():
    """Create a LogseqClient instance for testing."""
    return LogseqClient(host="localhost", port=12315, token="test-token")


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.raise_for_status = Mock()
    return response


class TestLogseqClient:
    """Test LogseqClient methods."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization."""
        # Test with default values
        client = LogseqClient()
        assert client.base_url == "http://localhost:12315/api"

        # Test with custom values
        client = LogseqClient(host="example.com", port=8080, token="secret")
        assert client.base_url == "http://example.com:8080/api"
        assert "Authorization" in client.client.headers
        assert client.client.headers["Authorization"] == "Bearer secret"

    @pytest.mark.asyncio
    async def test_get_page_with_array_format(self, client, mock_response):
        """Test get_page uses array format for arguments."""
        mock_response.json.return_value = {
            "uuid": "test-uuid",
            "originalName": "Test Page",
            "name": "test page",
        }

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.get_page("Test Page")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={"method": "logseq.Editor.getPage", "args": ["Test Page"]},
            )

            assert result["uuid"] == "test-uuid"
            assert result["originalName"] == "Test Page"

    @pytest.mark.asyncio
    async def test_get_page_not_found(self, client, mock_response):
        """Test get_page returns None for non-existent pages."""
        mock_response.json.return_value = None

        with patch.object(client.client, "post", return_value=mock_response):
            result = await client.get_page("NonExistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_page_blocks_with_array_format(self, client, mock_response):
        """Test get_page_blocks uses array format for arguments."""
        mock_blocks = [
            {"uuid": "block1", "content": "Block 1"},
            {"uuid": "block2", "content": "Block 2"},
        ]
        mock_response.json.return_value = mock_blocks

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.get_page_blocks("Test Page")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={
                    "method": "logseq.Editor.getPageBlocksTree",
                    "args": ["Test Page"],
                },
            )

            assert len(result) == 2
            assert result[0]["content"] == "Block 1"

    @pytest.mark.asyncio
    async def test_create_page_with_array_format(self, client, mock_response):
        """Test create_page uses array format for arguments."""
        mock_response.json.return_value = {
            "uuid": "new-page-uuid",
            "originalName": "New Page",
            "name": "new page",
        }

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.create_page("New Page")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={"method": "logseq.Editor.createPage", "args": ["New Page"]},
            )

            assert result["uuid"] == "new-page-uuid"

    @pytest.mark.asyncio
    async def test_create_page_with_content(self, client, mock_response):
        """Test create_page with initial content."""
        mock_response.json.return_value = {"uuid": "page-uuid", "name": "new page"}

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            with patch.object(
                client, "create_block", new_callable=AsyncMock
            ) as mock_create_block:
                result = await client.create_page("New Page", content="Initial content")

                # Verify page was created
                assert mock_post.call_count == 1

                # Verify block was created with content
                mock_create_block.assert_called_once_with(
                    content="Initial content", page="New Page"
                )

    @pytest.mark.asyncio
    async def test_get_block_with_array_format(self, client, mock_response):
        """Test get_block uses array format for arguments."""
        mock_response.json.return_value = {
            "uuid": "block-uuid",
            "content": "Block content",
        }

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.get_block("block-uuid")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={"method": "logseq.Editor.getBlock", "args": ["block-uuid"]},
            )

            assert result["content"] == "Block content"

    @pytest.mark.asyncio
    async def test_delete_block_with_array_format(self, client, mock_response):
        """Test delete_block uses array format for arguments."""
        mock_response.json.return_value = {"success": True}

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.delete_block("block-uuid")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={"method": "logseq.Editor.removeBlock", "args": ["block-uuid"]},
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_pages_with_string_format(self, client, mock_response):
        """Test search_pages uses string format (not array) for arguments."""
        mock_response.json.return_value = [{"name": "Page 1"}, {"name": "Page 2"}]

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.search_pages("test query")

            # Verify the request was made with string format (not array)
            mock_post.assert_called_once_with(
                client.base_url,
                json={"method": "logseq.Editor.search", "args": "test query"},
            )

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_execute_query_with_string_format(self, client, mock_response):
        """Test execute_query uses string format (not array) for arguments."""
        mock_response.json.return_value = [["result1"], ["result2"]]

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.execute_query("[:find ?p :where [?p :block/name]]")

            # Verify the request was made with string format (not array)
            mock_post.assert_called_once_with(
                client.base_url,
                json={
                    "method": "logseq.DB.q",
                    "args": "[:find ?p :where [?p :block/name]]",
                },
            )

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_create_block_with_array_format(self, client, mock_response):
        """Test create_block uses array format for arguments."""
        mock_response.json.return_value = {
            "uuid": "new-block-uuid",
            "content": "New block",
        }

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.create_block("New block", page="Test Page")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={
                    "method": "logseq.Editor.insertBlock",
                    "args": ["Test Page", "New block"],
                },
            )

            assert result["uuid"] == "new-block-uuid"

    @pytest.mark.asyncio
    async def test_create_block_with_properties(self, client, mock_response):
        """Test create_block with properties."""
        mock_response.json.return_value = {"uuid": "block-uuid"}

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            properties = {"tag": "important", "priority": "high"}
            result = await client.create_block(
                "Block with props", page="Test Page", properties=properties
            )

            # Verify properties are included in the request
            mock_post.assert_called_once_with(
                client.base_url,
                json={
                    "method": "logseq.Editor.insertBlock",
                    "args": [
                        "Test Page",
                        "Block with props",
                        {"properties": properties},
                    ],
                },
            )

    @pytest.mark.asyncio
    async def test_update_block_with_array_format(self, client, mock_response):
        """Test update_block uses array format for arguments."""
        mock_response.json.return_value = {"uuid": "block-uuid", "content": "Updated"}

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.update_block("block-uuid", content="Updated content")

            # Verify the request was made with array format
            mock_post.assert_called_once_with(
                client.base_url,
                json={
                    "method": "logseq.Editor.updateBlock",
                    "args": ["block-uuid", "Updated content"],
                },
            )

    @pytest.mark.asyncio
    async def test_get_all_pages(self, client, mock_response):
        """Test get_all_pages method."""
        mock_pages = [
            {"name": "Page 1", "uuid": "uuid1"},
            {"name": "Page 2", "uuid": "uuid2"},
        ]
        mock_response.json.return_value = mock_pages

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.get_all_pages()

            mock_post.assert_called_once_with(
                client.base_url, json={"method": "logseq.Editor.getAllPages"}
            )

            assert len(result) == 2
            assert result[0]["name"] == "Page 1"

    @pytest.mark.asyncio
    async def test_get_current_graph(self, client, mock_response):
        """Test get_current_graph method."""
        mock_response.json.return_value = {"name": "My Graph", "path": "/path/to/graph"}

        with patch.object(
            client.client, "post", return_value=mock_response
        ) as mock_post:
            result = await client.get_current_graph()

            mock_post.assert_called_once_with(
                client.base_url, json={"method": "logseq.Editor.getCurrentGraph"}
            )

            assert result["name"] == "My Graph"

    @pytest.mark.asyncio
    async def test_error_handling_http_error(self, client):
        """Test error handling for HTTP errors."""
        error_response = Mock(spec=httpx.Response)
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=error_response
        )

        with patch.object(client.client, "post", return_value=error_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_page("Test Page")

    @pytest.mark.asyncio
    async def test_error_handling_connection_error(self, client):
        """Test error handling for connection errors."""
        with patch.object(
            client.client, "post", side_effect=httpx.ConnectError("Connection failed")
        ):
            with pytest.raises(httpx.ConnectError):
                await client.get_page("Test Page")

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test closing the client."""
        with patch.object(
            client.client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()
