"""Query tools for Logseq."""

from mcp.types import Tool

execute_query_tool = Tool(
    name="execute_query",
    description="Execute a Datalog query in Logseq",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The Datalog query to execute",
            },
            "inputs": {
                "type": "array",
                "description": "Optional query inputs/parameters",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": ["query"],
    },
)
