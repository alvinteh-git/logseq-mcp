"""Entry point for the Logseq MCP server."""

import asyncio
import sys

from .server import main


def run():
    """Run the MCP server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
