"""Logseq API client."""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LogseqClient:
    """Client for interacting with Logseq API.

    Note on API argument formats:
    Most Logseq API methods expect arguments wrapped in arrays:
    - getPage: ["page-name"]
    - getPageBlocksTree: ["page-name"]
    - getBlock: ["block-uuid"]
    - removeBlock: ["block-uuid"]
    - createPage: ["page-name"]
    - insertBlock: ["page-or-parent", "content", options]
    - updateBlock: ["uuid", "content", options]

    Some methods use plain strings:
    - search: "query-string"
    - q (query): "datalog-query"
    - getCurrentGraph: no args
    - getAllPages: no args or empty array
    """

    def __init__(
        self, host: str = "localhost", port: int = 12315, token: str | None = None
    ):
        """Initialize the Logseq client.

        Args:
            host: Logseq API host
            port: Logseq API port
            token: Bearer token for authorization
        """
        self.base_url = f"http://{host}:{port}/api"
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(
        self, action: str, args: Any = None, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a POST request to the Logseq API.

        Args:
            action: API action to perform
            args: Simple argument(s) to pass as {"args": args}
            data: Complex data object to merge with request

        Returns:
            Response data
        """
        request_data = {"method": action}

        # If args is provided, use the simple format
        if args is not None:
            request_data["args"] = args

        # If data is provided, merge it (for complex requests)
        if data:
            request_data.update(data)

        logger.debug(
            f"Logseq API request: {action}", extra={"request_data": request_data}
        )

        # Log the JSON payload at INFO level for better visibility
        logger.info(f"Sending JSON payload to Logseq API: {json.dumps(request_data)}")

        try:
            response = await self.client.post(self.base_url, json=request_data)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(
                f"Logseq API response: {action}",
                extra={
                    "status_code": response.status_code,
                    "response_data": json.dumps(response_data)[:500]
                    if response_data
                    else None,
                },
            )

            # Log the response at INFO level for better visibility
            response_preview = (
                json.dumps(response_data)[:200] if response_data else "null"
            )
            logger.info(
                f"Received response from Logseq API: {response_preview}{'...' if len(json.dumps(response_data) if response_data else '') > 200 else ''}"
            )

            return response_data
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Logseq API HTTP error: {action}",
                extra={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text[:500],
                    "request_data": request_data,
                },
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Logseq API request failed: {action}",
                extra={"request_data": request_data},
                exc_info=True,
            )
            raise

    async def get_current_graph(self) -> dict[str, Any]:
        """Get the current graph information.

        Returns:
            Current graph data
        """
        return await self._request("logseq.Editor.getCurrentGraph")

    async def create_block(
        self,
        content: str,
        page: str | None = None,
        parent_block_id: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new block.

        Args:
            content: Block content
            page: Page name (if creating in a page)
            parent_block_id: Parent block UUID (if creating as child)
            properties: Optional block properties

        Returns:
            Created block data
        """
        # For insertBlock, the API expects [page/parent, content, opts]
        args: list[Any] = []
        if page:
            args = [page, content]
        elif parent_block_id:
            args = [parent_block_id, content]
        else:
            raise ValueError("Either page or parent_block_id must be provided")

        # Add options if properties exist
        if properties:
            args.append({"properties": properties})

        return await self._request("logseq.Editor.insertBlock", args=args)

    async def update_block(
        self,
        block_id: str,
        content: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a block.

        Args:
            block_id: Block UUID
            content: New content
            properties: New properties

        Returns:
            Updated block data
        """
        # For updateBlock, the API expects [uuid, content, opts]
        args: list[Any] = [block_id]

        if content is not None:
            args.append(content)
        else:
            args.append("")  # Empty content if not updating

        # Add options if properties exist
        if properties is not None:
            args.append({"properties": properties})

        return await self._request("logseq.Editor.updateBlock", args=args)

    async def delete_block(self, block_id: str) -> dict[str, Any]:
        """Delete a block.

        Args:
            block_id: Block UUID

        Returns:
            Deletion result
        """
        # Logseq API expects block UUID in an array
        return await self._request("logseq.Editor.removeBlock", args=[block_id])

    async def get_block(self, block_id: str) -> dict[str, Any]:
        """Get a block by UUID.

        Args:
            block_id: Block UUID

        Returns:
            Block data
        """
        # Logseq API expects block UUID in an array
        return await self._request("logseq.Editor.getBlock", args=[block_id])

    async def create_page(
        self,
        name: str,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Create a new page.

        Args:
            name: Page name
            content: Initial content

        Returns:
            Created page data
        """
        # Logseq API expects page name in an array
        result = await self._request("logseq.Editor.createPage", args=[name])

        # If content is provided, add it as the first block
        if content and result:
            await self.create_block(content=content, page=name)

        return result

    async def get_page(self, name: str) -> dict[str, Any] | None:
        """Get a page by name.

        Args:
            name: Page name

        Returns:
            Page data or None if page doesn't exist
        """
        try:
            logger.info(f"Getting page: '{name}'")
            # Logseq API expects page name in an array
            result = await self._request("logseq.Editor.getPage", args=[name])
            # Logseq returns null/nil for non-existent pages
            if result:
                logger.info(f"Page found: {json.dumps(result)[:100]}...")
            else:
                logger.info(f"Page '{name}' not found (result was null/nil)")
            return result if result else None
        except Exception as e:
            logger.error(f"Failed to get page '{name}': {e}")
            raise

    async def get_page_blocks(self, name: str) -> list[dict[str, Any]]:
        """Get all blocks in a page.

        Args:
            name: Page name

        Returns:
            List of blocks
        """
        try:
            # Logseq API expects page name in an array
            result = await self._request("logseq.Editor.getPageBlocksTree", args=[name])
            # Return empty list if result is None or not a list
            if not isinstance(result, list):
                logger.warning(
                    f"Unexpected result type for page blocks: {type(result)}"
                )
                return []
            return result
        except Exception as e:
            logger.error(f"Failed to get blocks for page '{name}': {e}")
            # Return empty list on error instead of propagating
            return []

    async def get_all_pages(self) -> list[dict[str, Any]]:
        """Get all pages in the current graph.

        Returns:
            List of all pages with their metadata
        """
        try:
            result = await self._request("logseq.Editor.getAllPages")
            # The result should be a list of page objects
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"Failed to get all pages: {e}")
            return []

    async def search_pages(self, query: str) -> list[dict[str, Any]]:
        """Search for pages.

        Args:
            query: Search query

        Returns:
            List of matching pages
        """
        try:
            result = await self._request("logseq.Editor.search", args=query)
            # The result might be a list directly or wrapped in an object
            if isinstance(result, list):
                return result
            return result.get("pages", []) if result else []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a Datalog query.

        Args:
            query: Datalog query

        Returns:
            Query results
        """
        result = await self._request("logseq.DB.q", args=query)
        # Handle different response formats
        if isinstance(result, list):
            return result
        return result.get("results", [])
