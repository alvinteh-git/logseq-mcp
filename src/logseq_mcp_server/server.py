"""Main MCP server for Logseq integration."""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    ClientCapabilities,
    ServerCapabilities,
    Tool,
)

from .tools.blocks import create_block_tool, update_block_tool, delete_block_tool
from .tools.pages import create_page_tool, get_page_tool, search_pages_tool
from .tools.queries import execute_query_tool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server("logseq-mcp-server")


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return [
        create_block_tool,
        update_block_tool,
        delete_block_tool,
        create_page_tool,
        get_page_tool,
        search_pages_tool,
        execute_query_tool,
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Handle tool execution requests."""
    logger.info(f"Executing tool: {name}")
    
    tool_handlers = {
        "create_block": handle_create_block,
        "update_block": handle_update_block,
        "delete_block": handle_delete_block,
        "create_page": handle_create_page,
        "get_page": handle_get_page,
        "search_pages": handle_search_pages,
        "execute_query": handle_execute_query,
    }
    
    handler = tool_handlers.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    
    try:
        result = await handler(arguments)
        logger.info(f"Tool {name} executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        raise


async def handle_create_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block creation."""
    # TODO: Implement actual Logseq API integration
    return {
        "block_id": "mock-block-id",
        "content": arguments.get("content", ""),
        "page": arguments.get("page", ""),
    }


async def handle_update_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block updates."""
    # TODO: Implement actual Logseq API integration
    return {
        "block_id": arguments.get("block_id", ""),
        "updated": True,
    }


async def handle_delete_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block deletion."""
    # TODO: Implement actual Logseq API integration
    return {
        "block_id": arguments.get("block_id", ""),
        "deleted": True,
    }


async def handle_create_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page creation."""
    # TODO: Implement actual Logseq API integration
    return {
        "page_name": arguments.get("name", ""),
        "created": True,
    }


async def handle_get_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page retrieval."""
    # TODO: Implement actual Logseq API integration
    return {
        "page_name": arguments.get("name", ""),
        "content": "Mock page content",
        "properties": {},
    }


async def handle_search_pages(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page search."""
    # TODO: Implement actual Logseq API integration
    return {
        "query": arguments.get("query", ""),
        "results": [],
    }


async def handle_execute_query(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle Datalog query execution."""
    # TODO: Implement actual Logseq API integration
    return {
        "query": arguments.get("query", ""),
        "results": [],
    }


@app.initialize()
async def handle_initialize(
    client_capabilities: ClientCapabilities,
) -> InitializationOptions:
    """Handle server initialization."""
    logger.info("Initializing Logseq MCP server")
    
    return InitializationOptions(
        server_info={
            "name": "logseq-mcp-server",
            "version": "0.1.0",
        },
        capabilities=ServerCapabilities(
            tools={"listChanged": True},
        ),
    )


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    transport = os.getenv("LOGSEQ_MCP_TRANSPORT", "stdio")
    
    if transport == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_info={
                        "name": "logseq-mcp-server",
                        "version": "0.1.0",
                    },
                    capabilities=ServerCapabilities(
                        tools={"listChanged": True},
                    ),
                ),
            )
    else:
        # TODO: Implement SSE transport
        raise NotImplementedError(f"Transport {transport} not implemented")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())