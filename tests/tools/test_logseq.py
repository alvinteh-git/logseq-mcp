#!/usr/bin/env python3
"""
Logseq API Test Harness

A simple tool for testing Logseq API methods directly without going through MCP.
This allows for rapid iteration and debugging of API calls.

Usage:
    python test_logseq.py get-page "Page Name"
    python test_logseq.py interactive
    python test_logseq.py raw "logseq.Editor.getPage" "Page Name"
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from logseq_mcp_server.logseq.client import LogseqClient
from logseq_mcp_server.logging_config import setup_logging

# Rich is optional but provides better output
try:
    from rich.console import Console
    from rich.json import JSON
    from rich.table import Table
    from rich.syntax import Syntax
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False


class LogseqTestHarness:
    """Test harness for Logseq API testing."""
    
    def __init__(self, host: str, port: int, token: Optional[str] = None):
        """Initialize the test harness."""
        self.client = LogseqClient(host=host, port=port, token=token)
        self.history = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.close()
        
    def print_result(self, result: Any, title: str = "Result"):
        """Pretty print the result."""
        if RICH_AVAILABLE and console:
            if isinstance(result, (dict, list)):
                console.print(f"\n[bold blue]{title}:[/bold blue]")
                console.print(JSON.from_data(result))
            else:
                console.print(f"\n[bold blue]{title}:[/bold blue] {result}")
        else:
            print(f"\n{title}:")
            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(result)
    
    def print_error(self, error: Exception):
        """Print error message."""
        if RICH_AVAILABLE and console:
            console.print(f"\n[bold red]Error:[/bold red] {error}")
        else:
            print(f"\nError: {error}")
    
    async def test_get_page(self, page_name: str, show_raw: bool = False) -> dict:
        """Test get_page method."""
        print(f"\nTesting get_page('{page_name}')")
        print("-" * 50)
        
        try:
            result = await self.client.get_page(page_name)
            
            if show_raw:
                self.print_result(result, "Raw Response")
            else:
                if result:
                    self.print_result({
                        "found": True,
                        "name": result.get("originalName", result.get("name")),
                        "uuid": result.get("uuid"),
                        "properties": result.get("properties", {}),
                        "created_at": result.get("createdAt"),
                        "updated_at": result.get("updatedAt"),
                    }, "Page Info")
                else:
                    self.print_result({"found": False, "page": None}, "Page Not Found")
            
            return result
            
        except Exception as e:
            self.print_error(e)
            raise
    
    async def test_get_all_pages(self, limit: Optional[int] = None) -> list:
        """Test get_all_pages method."""
        print(f"\nTesting get_all_pages()")
        print("-" * 50)
        
        try:
            result = await self.client.get_all_pages()
            
            if limit and len(result) > limit:
                result = result[:limit]
                print(f"Showing first {limit} pages")
            
            if RICH_AVAILABLE and console:
                table = Table(title=f"Found {len(result)} pages")
                table.add_column("Name", style="cyan")
                table.add_column("Journal?", style="green")
                table.add_column("UUID", style="dim")
                
                for page in result:
                    table.add_row(
                        page.get("originalName", page.get("name", "Unknown")),
                        "Yes" if page.get("journal?", False) else "No",
                        page.get("uuid", "")[:8] + "..." if page.get("uuid") else ""
                    )
                
                console.print(table)
            else:
                print(f"Found {len(result)} pages:")
                for page in result:
                    name = page.get("originalName", page.get("name", "Unknown"))
                    journal = "Journal" if page.get("journal?", False) else "Page"
                    print(f"  - {name} ({journal})")
            
            return result
            
        except Exception as e:
            self.print_error(e)
            raise
    
    async def test_search(self, query: str) -> list:
        """Test search_pages method."""
        print(f"\nTesting search_pages('{query}')")
        print("-" * 50)
        
        try:
            result = await self.client.search_pages(query)
            
            if result:
                self.print_result(result, f"Found {len(result)} results")
            else:
                print("No results found")
            
            return result
            
        except Exception as e:
            self.print_error(e)
            raise
    
    async def test_raw(self, method: str, args: Any) -> Any:
        """Test raw API call."""
        print(f"\nTesting raw API call: {method}")
        print(f"Args: {args}")
        print("-" * 50)
        
        try:
            result = await self.client._request(method, args=args)
            self.print_result(result, "Raw API Response")
            return result
            
        except Exception as e:
            self.print_error(e)
            raise
    
    async def interactive_mode(self):
        """Run interactive REPL mode."""
        print("\nLogseq Test Harness - Interactive Mode")
        print("Type 'help' for available commands, 'exit' to quit")
        print("-" * 50)
        
        # Test connection
        try:
            graph = await self.client.get_current_graph()
            print(f"Connected to graph: {graph.get('name', 'Unknown')}")
        except Exception as e:
            print(f"Warning: Could not connect to Logseq: {e}")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if not command:
                    continue
                
                self.history.append(command)
                
                if command == "exit":
                    break
                elif command == "help":
                    self.show_help()
                elif command == "history":
                    for i, cmd in enumerate(self.history[-10:], 1):
                        print(f"{i}: {cmd}")
                elif command.startswith("get_page "):
                    page_name = command[9:].strip('"\'')
                    await self.test_get_page(page_name)
                elif command == "get_all_pages":
                    await self.test_get_all_pages(limit=10)
                elif command.startswith("search "):
                    query = command[7:].strip('"\'')
                    await self.test_search(query)
                elif command.startswith("raw "):
                    parts = command[4:].split(None, 1)
                    if len(parts) == 2:
                        method, args = parts
                        # Try to parse args as JSON, otherwise use as string
                        try:
                            args = json.loads(args)
                        except:
                            args = args.strip('"\'')
                        await self.test_raw(method, args)
                    else:
                        print("Usage: raw <method> <args>")
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                self.print_error(e)
    
    def show_help(self):
        """Show help for interactive mode."""
        help_text = """
Available commands:
  get_page <name>      - Get a specific page
  get_all_pages        - List all pages (limited to 10)
  search <query>       - Search for pages
  raw <method> <args>  - Call raw API method
  history              - Show command history
  help                 - Show this help
  exit                 - Exit interactive mode
  
Examples:
  get_page "MCP Server"
  search "test"
  raw logseq.Editor.getCurrentGraph
  raw logseq.Editor.getPage "My Page"
        """
        print(help_text)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Logseq API Test Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s get-page "MCP Server"
  %(prog)s get-page "Test Page" --show-raw
  %(prog)s get-all-pages --limit 5
  %(prog)s search "test"
  %(prog)s raw logseq.Editor.getPage "MCP Server"
  %(prog)s interactive
        """
    )
    
    parser.add_argument("--host", default=None, help="Logseq API host")
    parser.add_argument("--port", type=int, default=None, help="Logseq API port")
    parser.add_argument("--token", default=None, help="Logseq API token")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # get-page command
    get_page = subparsers.add_parser("get-page", help="Get a specific page")
    get_page.add_argument("name", help="Page name")
    get_page.add_argument("--show-raw", action="store_true", help="Show raw response")
    
    # get-all-pages command
    get_all = subparsers.add_parser("get-all-pages", help="Get all pages")
    get_all.add_argument("--limit", type=int, help="Limit number of results")
    
    # search command
    search = subparsers.add_parser("search", help="Search for pages")
    search.add_argument("query", help="Search query")
    
    # raw command
    raw = subparsers.add_parser("raw", help="Raw API call")
    raw.add_argument("method", help="API method (e.g., logseq.Editor.getPage)")
    raw.add_argument("args", nargs="?", help="Arguments (JSON or string)")
    
    # interactive command
    subparsers.add_parser("interactive", help="Interactive REPL mode")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv("env/.env")
    
    # Get configuration
    host = args.host or os.getenv("LOGSEQ_API_HOST", "localhost")
    port = args.port or int(os.getenv("LOGSEQ_API_PORT", "12315"))
    token = args.token or os.getenv("LOGSEQ_API_TOKEN")
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    log_file = f"logs/test-logseq-{datetime.now():%Y%m%d-%H%M%S}.log"
    setup_logging(log_level=log_level, log_file=log_file)
    
    # Adjust console logging for readability
    if not args.verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
    
    print(f"Connecting to Logseq at {host}:{port}")
    if token:
        print("Using authentication token")
    
    async with LogseqTestHarness(host, port, token) as harness:
        if args.command == "get-page":
            await harness.test_get_page(args.name, args.show_raw)
        elif args.command == "get-all-pages":
            await harness.test_get_all_pages(args.limit)
        elif args.command == "search":
            await harness.test_search(args.query)
        elif args.command == "raw":
            # Parse args if provided
            raw_args = None
            if args.args:
                try:
                    raw_args = json.loads(args.args)
                except:
                    raw_args = args.args
            await harness.test_raw(args.method, raw_args)
        elif args.command == "interactive":
            await harness.interactive_mode()
        else:
            parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())