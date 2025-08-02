"""Block manipulation tools for Logseq."""

from mcp.types import Tool

create_block_tool = Tool(
    name="create_block",
    description="Create a new block in Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The content of the block",
            },
            "page": {
                "type": "string",
                "description": "The page to create the block in",
            },
            "parent_block_id": {
                "type": "string",
                "description": "Optional parent block ID for nested blocks",
            },
            "properties": {
                "type": "object",
                "description": "Optional block properties",
            },
        },
        "required": ["content", "page"],
    },
)

update_block_tool = Tool(
    name="update_block",
    description="Update an existing block in Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "The ID of the block to update",
            },
            "content": {
                "type": "string",
                "description": "The new content for the block",
            },
            "properties": {
                "type": "object",
                "description": "Optional updated block properties",
            },
        },
        "required": ["block_id"],
    },
)

delete_block_tool = Tool(
    name="delete_block",
    description="Delete a block from Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "The ID of the block to delete",
            },
        },
        "required": ["block_id"],
    },
)
