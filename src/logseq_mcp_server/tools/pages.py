"""Page operations tools for Logseq."""

from mcp.types import Tool

create_page_tool = Tool(
    name="create_page",
    description="Create a new page in Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the page",
            },
            "content": {
                "type": "string",
                "description": "Optional initial content for the page",
            },
            "properties": {
                "type": "object",
                "description": "Optional page properties",
            },
        },
        "required": ["name"],
    },
)

get_page_tool = Tool(
    name="get_page",
    description="Get a page from Logseq by name",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the page to retrieve",
            },
            "include_children": {
                "type": "boolean",
                "description": "Whether to include child blocks",
                "default": True,
            },
        },
        "required": ["name"],
    },
)

search_pages_tool = Tool(
    name="search_pages",
    description="Search for pages in Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
            },
        },
        "required": ["query"],
    },
)