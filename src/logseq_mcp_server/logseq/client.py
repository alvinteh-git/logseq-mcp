"""Logseq API client."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LogseqClient:
    """Client for interacting with Logseq API."""
    
    def __init__(self, host: str = "localhost", port: int = 12315):
        """Initialize the Logseq client.
        
        Args:
            host: Logseq API host
            port: Logseq API port
        """
        self.base_url = f"http://{host}:{port}/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make a request to the Logseq API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint}"
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def create_block(
        self,
        content: str,
        page: str,
        parent_block_id: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new block.
        
        Args:
            content: Block content
            page: Page name
            parent_block_id: Optional parent block ID
            properties: Optional block properties
            
        Returns:
            Created block data
        """
        data = {
            "content": content,
            "page": page,
        }
        if parent_block_id:
            data["parent"] = parent_block_id
        if properties:
            data["properties"] = properties
            
        return await self._request("POST", "blocks", json=data)
    
    async def update_block(
        self,
        block_id: str,
        content: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a block.
        
        Args:
            block_id: Block ID
            content: New content
            properties: New properties
            
        Returns:
            Updated block data
        """
        data = {}
        if content is not None:
            data["content"] = content
        if properties is not None:
            data["properties"] = properties
            
        return await self._request("PUT", f"blocks/{block_id}", json=data)
    
    async def delete_block(self, block_id: str) -> dict[str, Any]:
        """Delete a block.
        
        Args:
            block_id: Block ID
            
        Returns:
            Deletion result
        """
        return await self._request("DELETE", f"blocks/{block_id}")
    
    async def create_page(
        self,
        name: str,
        content: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new page.
        
        Args:
            name: Page name
            content: Initial content
            properties: Page properties
            
        Returns:
            Created page data
        """
        data = {"name": name}
        if content:
            data["content"] = content
        if properties:
            data["properties"] = properties
            
        return await self._request("POST", "pages", json=data)
    
    async def get_page(self, name: str, include_children: bool = True) -> dict[str, Any]:
        """Get a page by name.
        
        Args:
            name: Page name
            include_children: Whether to include child blocks
            
        Returns:
            Page data
        """
        params = {"include_children": include_children}
        return await self._request("GET", f"pages/{name}", params=params)
    
    async def search_pages(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for pages.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching pages
        """
        params = {"q": query, "limit": limit}
        result = await self._request("GET", "pages/search", params=params)
        return result.get("pages", [])
    
    async def execute_query(
        self, query: str, inputs: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Datalog query.
        
        Args:
            query: Datalog query
            inputs: Query inputs
            
        Returns:
            Query results
        """
        data = {"query": query}
        if inputs:
            data["inputs"] = inputs
            
        result = await self._request("POST", "query", json=data)
        return result.get("results", [])