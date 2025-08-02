# Test Tools

This directory contains standalone tools and utilities for testing and debugging the Logseq MCP server.

## test_logseq.py

A comprehensive test harness for interacting with the Logseq API directly, bypassing the MCP protocol layer. This is useful for:

- **Debugging API connectivity** - Test if Logseq API is accessible
- **Exploring API methods** - Try different API calls interactively
- **Validating responses** - Check API response formats before implementing MCP tools
- **Performance testing** - Measure API response times without MCP overhead

### Usage

```bash
# Test page retrieval
python test_logseq.py get-page "My Page Name"

# Interactive REPL mode
python test_logseq.py interactive

# Raw API calls
python test_logseq.py raw logseq.Editor.getCurrentGraph
```

## test_cases.json

Configuration file containing predefined test cases for the test harness. Useful for:
- Regression testing
- Documenting common API usage patterns
- Quick validation of API functionality

### Example Test Case

```json
{
  "name": "Test get_page with existing page",
  "command": "get-page",
  "args": ["Contents"],
  "description": "Should return page data if Contents page exists"
}
```

## Running the Test Harness

The test harness uses the same environment configuration as the main server:

```bash
# Set environment variables
export LOGSEQ_API_HOST=localhost
export LOGSEQ_API_PORT=12315
export LOGSEQ_API_TOKEN=your-token  # if required

# Run tests
python test_logseq.py --help
```