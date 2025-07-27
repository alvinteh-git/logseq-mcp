"""Unit tests for MCP tools."""

import pytest
from mcp.types import Tool

from logseq_mcp_server.tools.blocks import (
    create_block_tool,
    update_block_tool,
    delete_block_tool,
)
from logseq_mcp_server.tools.pages import (
    create_page_tool,
    get_page_tool,
    search_pages_tool,
)
from logseq_mcp_server.tools.queries import execute_query_tool


class TestBlockTools:
    """Test block manipulation tools."""
    
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


class TestPageTools:
    """Test page operation tools."""
    
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
        assert "include_children" in get_page_tool.inputSchema["properties"]
    
    def test_search_pages_tool_schema(self):
        """Test search_pages tool schema."""
        assert isinstance(search_pages_tool, Tool)
        assert search_pages_tool.name == "search_pages"
        assert "query" in search_pages_tool.inputSchema["properties"]
        assert "limit" in search_pages_tool.inputSchema["properties"]


class TestQueryTools:
    """Test query tools."""
    
    def test_execute_query_tool_schema(self):
        """Test execute_query tool schema."""
        assert isinstance(execute_query_tool, Tool)
        assert execute_query_tool.name == "execute_query"
        assert "query" in execute_query_tool.inputSchema["properties"]
        assert "inputs" in execute_query_tool.inputSchema["properties"]
        assert execute_query_tool.inputSchema["required"] == ["query"]