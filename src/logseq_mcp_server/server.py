"""Main MCP server for Logseq integration."""

import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

from .logging_config import log_tool_invocation, setup_logging
from .logseq.client import LogseqClient
from .tools.blocks import create_block_tool, delete_block_tool, update_block_tool
from .tools.pages import (
    create_page_tool,
    get_all_pages_tool,
    get_journal_page_tool,
    get_page_tool,
    search_pages_tool,
)
from .tools.queries import execute_query_tool
from .utils.date_converter import date_to_journal_format

# Load environment variables
load_dotenv("env/.env")

# Configure logging
log_level = os.getenv("LOGSEQ_MCP_LOG_LEVEL", "INFO")
log_file = os.getenv("LOGSEQ_MCP_LOG_FILE")
setup_logging(log_level=log_level, log_file=log_file)

logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server("logseq-mcp-server", version="0.1.0")

# Global client instance
logseq_client: LogseqClient | None = None


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return [
        create_block_tool,
        update_block_tool,
        delete_block_tool,
        create_page_tool,
        get_all_pages_tool,
        get_page_tool,
        get_journal_page_tool,
        search_pages_tool,
        execute_query_tool,
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Handle tool execution requests."""
    start_time = time.time()
    logger.info(
        f"Tool invocation started: {name}",
        extra={"tool_name": name, "arguments": arguments},
    )

    if not logseq_client:
        error_msg = "Logseq client not initialized"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    tool_handlers = {
        "create_block": handle_create_block,
        "update_block": handle_update_block,
        "delete_block": handle_delete_block,
        "create_page": handle_create_page,
        "get_all_pages": handle_get_all_pages,
        "get_page": handle_get_page,
        "get_journal_page": handle_get_journal_page,
        "search_pages": handle_search_pages,
        "execute_query": handle_execute_query,
    }

    handler = tool_handlers.get(name)
    if not handler:
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg, extra={"tool_name": name})
        raise ValueError(error_msg)

    try:
        result = await handler(arguments)
        duration_ms = (time.time() - start_time) * 1000
        log_tool_invocation(
            logger=logger,
            tool_name=name,
            arguments=arguments,
            result=result,
            duration_ms=duration_ms,
        )
        return result
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_invocation(
            logger=logger,
            tool_name=name,
            arguments=arguments,
            error=e,
            duration_ms=duration_ms,
        )
        raise


async def handle_create_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block creation."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        logger.debug(
            f"Creating block with content: {arguments.get('content', '')[:100]}..."
        )
        result = await logseq_client.create_block(
            content=arguments["content"],
            page=arguments.get("page"),
            parent_block_id=arguments.get("parent_block_id"),
            properties=arguments.get("properties"),
        )
        logger.debug(f"Block created successfully: {result}")
        return {"success": True, "block": result}
    except Exception as e:
        logger.error(f"Failed to create block: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_update_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block updates."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        logger.debug(f"Updating block {arguments.get('block_id')}")
        result = await logseq_client.update_block(
            block_id=arguments["block_id"],
            content=arguments.get("content"),
            properties=arguments.get("properties"),
        )
        logger.debug(f"Block updated successfully: {result}")
        return {"success": True, "block": result}
    except Exception as e:
        logger.error(f"Failed to update block: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_delete_block(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle block deletion."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        logger.debug(f"Deleting block {arguments.get('block_id')}")
        result = await logseq_client.delete_block(
            block_id=arguments["block_id"],
        )
        logger.debug("Block deleted successfully")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to delete block: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_create_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page creation."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        logger.debug(f"Creating page: {arguments.get('name')}")
        result = await logseq_client.create_page(
            name=arguments["name"],
            content=arguments.get("content"),
        )
        logger.debug(f"Page created successfully: {result}")
        return {"success": True, "page": result}
    except Exception as e:
        logger.error(f"Failed to create page: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_all_pages(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle getting all pages."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        include_journals = arguments.get("include_journals", True)
        logger.debug(f"Getting all pages (include_journals={include_journals})")

        pages = await logseq_client.get_all_pages()

        # Filter out journal pages if requested
        if not include_journals:
            pages = [p for p in pages if not p.get("journal?", False)]

        logger.debug(f"Retrieved {len(pages)} pages")
        return {"success": True, "pages": pages, "count": len(pages)}
    except Exception as e:
        logger.error(f"Failed to get all pages: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page retrieval."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        page_name = arguments.get("name", "")
        if not page_name:
            return {"success": False, "error": "Page name is required"}

        logger.debug(f"Getting page: {page_name}")
        page = await logseq_client.get_page(name=page_name)

        # Check if page exists
        if page is None:
            logger.debug(f"Page '{page_name}' not found")
            return {"success": False, "error": f"Page '{page_name}' not found"}

        # Only get blocks if page exists and include_children is True
        if arguments.get("include_children", True):
            try:
                blocks = await logseq_client.get_page_blocks(name=page_name)
                logger.debug(
                    f"Retrieved page with {len(blocks) if blocks else 0} blocks"
                )
                return {"success": True, "page": page, "blocks": blocks}
            except Exception as block_error:
                logger.warning(
                    f"Failed to get blocks for page '{page_name}': {block_error}"
                )
                # Return page without blocks if block retrieval fails
                return {"success": True, "page": page, "blocks": []}

        logger.debug("Retrieved page without blocks")
        return {"success": True, "page": page}
    except Exception as e:
        logger.error(f"Failed to get page: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_journal_page(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle journal page retrieval by date."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        date_input = arguments.get("date", "")
        if not date_input:
            return {"success": False, "error": "Date is required"}

        # Convert date to journal format
        try:
            journal_name = date_to_journal_format(date_input)
            logger.debug(
                f"Converted date '{date_input}' to journal format: '{journal_name}'"
            )
        except ValueError as e:
            return {"success": False, "error": f"Invalid date format: {str(e)}"}

        # Get the journal page using the converted name
        logger.debug(f"Getting journal page: {journal_name}")
        page = await logseq_client.get_page(name=journal_name)

        # Check if page exists
        if page is None:
            logger.debug(f"Journal page '{journal_name}' not found")
            logger.info(f"Tried to find journal page with name: '{journal_name}' for date input: '{date_input}'")
            return {"success": False, "page": None, "journal_name": journal_name}

        logger.debug(f"Retrieved journal page: {page.get('uuid')}")

        # Get child blocks if requested
        include_children = arguments.get("include_children", True)
        if include_children and page.get("uuid"):
            try:
                logger.debug("Getting blocks for journal page")
                blocks = await logseq_client.get_page_blocks(journal_name)
                return {
                    "success": True,
                    "page": page,
                    "blocks": blocks,
                    "journal_name": journal_name,
                }
            except Exception as block_error:
                logger.warning(
                    f"Failed to get blocks for journal page '{journal_name}': {block_error}"
                )
                # Return page without blocks if block retrieval fails
                return {
                    "success": True,
                    "page": page,
                    "blocks": [],
                    "journal_name": journal_name,
                }

        logger.debug("Retrieved journal page without blocks")
        return {"success": True, "page": page, "journal_name": journal_name}
    except Exception as e:
        logger.error(f"Failed to get journal page: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_search_pages(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle page search."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        query = arguments.get("query", "")
        logger.debug(f"Searching pages with query: {query}")
        results = await logseq_client.search_pages(
            query=arguments["query"],
        )
        # Limit results if specified
        limit = arguments.get("limit", 10)
        if limit and len(results) > limit:
            results = results[:limit]

        logger.debug(f"Found {len(results)} pages matching query")
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Failed to search pages: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_execute_query(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle Datalog query execution."""
    if not logseq_client:
        raise RuntimeError("Logseq client not initialized")

    try:
        query = arguments.get("query", "")
        logger.debug(f"Executing Datalog query: {query[:200]}...")
        results = await logseq_client.execute_query(
            query=arguments["query"],
        )
        logger.debug(f"Query returned {len(results)} results")
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Failed to execute query: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def initialize_logseq_client():
    """Initialize the Logseq client."""
    global logseq_client

    logger.info("Initializing Logseq MCP server")

    # Initialize Logseq client
    host = os.getenv("LOGSEQ_API_HOST", "localhost")
    port = int(os.getenv("LOGSEQ_API_PORT", "12315"))
    token = os.getenv("LOGSEQ_API_TOKEN")

    logger.info(
        f"Logseq API configuration: host={host}, port={port}, token={'set' if token else 'not set'}"
    )

    if not token:
        logger.warning("LOGSEQ_API_TOKEN not set, API calls may fail")

    logseq_client = LogseqClient(host=host, port=port, token=token)

    # Test connection
    try:
        logger.debug("Testing Logseq API connection...")
        graph = await logseq_client.get_current_graph()
        logger.info(f"Successfully connected to Logseq graph: {graph}")
    except Exception as e:
        logger.error(f"Failed to connect to Logseq: {e}", exc_info=True)
        logger.warning("Continuing with initialization, but API calls may fail")


async def cleanup():
    """Cleanup resources."""
    global logseq_client
    if logseq_client:
        await logseq_client.close()
        logseq_client = None


async def main():
    """Run the MCP server."""
    logger.info("Starting Logseq MCP server")
    logger.info(f"Server version: {app.name} v{app.version}")

    # Log file location
    for handler in logging.getLogger().handlers:
        if hasattr(handler, "baseFilename"):
            # Use getattr to safely access the attribute
            filename = getattr(handler, "baseFilename", None)
            if filename:
                logger.info(f"Log file location: {filename}")
            break
    else:
        logger.info("Logging to console only (no file handler)")

    from mcp.server.stdio import stdio_server

    # Initialize Logseq client before starting server
    await initialize_logseq_client()

    transport = os.getenv("LOGSEQ_MCP_TRANSPORT", "stdio")
    logger.info(f"Using transport: {transport}")

    if transport == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            try:
                logger.debug("Creating initialization options")
                initialization_options = app.create_initialization_options()
                logger.info("Starting MCP server main loop")
                await app.run(
                    read_stream,
                    write_stream,
                    initialization_options,
                )
            except Exception as e:
                logger.error(f"Error in server main loop: {e}", exc_info=True)
                raise
            finally:
                logger.info("Shutting down server")
                await cleanup()
    else:
        # TODO: Implement SSE transport
        error_msg = f"Transport {transport} not implemented"
        logger.error(error_msg)
        raise NotImplementedError(error_msg)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
