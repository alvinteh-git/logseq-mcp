"""Page operations tools for Logseq."""

from mcp.types import Tool

get_all_pages_tool = Tool(
    name="get_all_pages",
    description="Get all pages in the current Logseq graph",
    inputSchema={
        "type": "object",
        "properties": {
            "include_journals": {
                "type": "boolean",
                "description": "Whether to include journal pages",
                "default": True,
            },
        },
    },
)

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

get_journal_page_tool = Tool(
    name="get_journal_page",
    description="Get a journal page by date. Automatically converts the date to Logseq's journal format.",
    inputSchema={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "The date for the journal page. Accepts various formats: ISO (2023-12-25), US (12/25/2023), or already formatted (December 25th, 2023)",
            },
            "include_children": {
                "type": "boolean",
                "description": "Whether to include child blocks",
                "default": True,
            },
        },
        "required": ["date"],
    },
)
