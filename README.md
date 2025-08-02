# Logseq MCP Server

An MCP (Model Context Protocol) server for interacting with Logseq graphs, enabling AI assistants to read, create, and manipulate Logseq content.

## Features

- **Block Operations**: Create, update, and delete blocks
- **Page Management**: Create pages, retrieve page content, search pages
- **Query Execution**: Execute Datalog queries against your Logseq graph
- **Journal Support**: Access journal pages by date with automatic format conversion
- **Privacy-First Logging**: Automatic sanitization of sensitive data in logs
- **MCP Protocol**: Full compliance with the Model Context Protocol specification

## Quick Setup

### Automated Setup (Recommended)

We provide a setup wizard that will guide you through the installation:

```bash
# Clone the repository
git clone https://github.com/yourusername/logseq-mcp.git
cd logseq-mcp

# Run the setup wizard
./deploy.sh
```

The setup wizard will:
1. Check your Python version (3.13+ required)
2. Install uv package manager (if not present)
3. Install all dependencies
4. Configure your Logseq API connection
5. Test the connection to Logseq
6. Generate configuration for Claude Desktop or Cline

### Prerequisites

- Python 3.13+
- Logseq with API enabled
- uv (recommended) or pip for package management

### Manual Installation

If you prefer to set up manually instead of using the setup wizard:

#### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/logseq-mcp.git
cd logseq-mcp

# Install dependencies
uv pip install --system -e .

# Install development dependencies (optional)
uv pip install --system -e ".[dev]"
```

#### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/logseq-mcp.git
cd logseq-mcp

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

## Configuration

### Logseq Configuration

1. Copy the example environment file:
   ```bash
   cp env/.env.example env/.env
   ```

2. Configure your Logseq API settings in `env/.env`:
   ```env
   LOGSEQ_API_HOST=localhost
   LOGSEQ_API_PORT=12315
   ```

3. Enable the Logseq API in your Logseq settings

### Claude Desktop Configuration

The setup wizard (`./deploy.sh`) will generate the configuration for you. If you need to configure manually, add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "logseq": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/logseq-mcp",
        "run",
        "--with",
        ".",
        "--refresh",
        "--python",
        "3.13",
        "python",
        "-m",
        "logseq_mcp_server"
      ],
      "env": {
        "LOGSEQ_API_HOST": "localhost",
        "LOGSEQ_API_PORT": "12315",
        "LOGSEQ_MCP_LOG_LEVEL": "INFO",
        "LOGSEQ_MCP_PROJECT_ROOT": "/path/to/logseq-mcp"
      }
    }
  }
}
```

**Important Notes**:
- Replace ALL instances of `/path/to/logseq-mcp` with the actual absolute path to your cloned repository (in args AND env)
- The `--directory` argument sets UV's working directory
- The `--with .` argument tells UV to install the local package before running
- The `--refresh` flag ensures UV uses the latest code (important during development)
- The `LOGSEQ_MCP_PROJECT_ROOT` environment variable ensures logs are saved in the project directory
- Ensure Logseq is running with the API server enabled before starting Claude Desktop
- You may need to configure authentication if your Logseq API requires a token

**Troubleshooting**:
- If you see errors about cached code, run `uv cache clean` to clear UV's cache
- Check logs in the `logs/` directory of the project for detailed error information

After updating the configuration, restart Claude Desktop to connect to the Logseq MCP server.

### Cline (VS Code Extension) Configuration

For Cline users, the setup wizard will provide the configuration. You can also manually add the server to your Cline settings in VS Code:

1. Open VS Code Settings
2. Navigate to Extensions > Cline > MCP Servers
3. Add the configuration provided by the setup wizard

### Logging and Privacy

The server includes privacy-focused logging that protects your personal data by default:

#### Privacy Features

- **Default Privacy Mode**: Personal data like page names, content, and queries are automatically sanitized
- **Automatic Log Rotation**: Prevents disk space issues with configurable size/time-based rotation
- **Configurable Retention**: Set how long to keep logs before automatic deletion

#### Logging Modes

1. **Privacy Mode** (default): Sanitizes sensitive information
   - Page names: `"My Private Notes"` → `"My P***otes"` (preserves partial visibility)
   - Content: Replaced with `[content_123_chars]`
   - Queries: Hidden as `[datalog_query_45_chars]`
   - File paths: `/Users/john/Documents` → `/Users/***/Documents`
   - Block IDs: Anonymized to `block_a1b2c3` (consistent hashing)

2. **Debug Mode**: Full logging for troubleshooting
   - Enable with `LOGSEQ_MCP_LOG_MODE=debug`
   - Shows complete data (use only when needed)

3. **Minimal Mode**: Only errors and warnings
   - Enable with `LOGSEQ_MCP_LOG_MODE=minimal`

#### Configuration

```bash
# Environment variables
LOGSEQ_MCP_LOG_MODE=privacy          # privacy, debug, or minimal (default: privacy)
LOGSEQ_MCP_LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR (default: INFO)
LOGSEQ_MCP_LOG_RETENTION_DAYS=7      # Days to keep logs (default: none)
LOGSEQ_MCP_LOG_MAX_SIZE=10MB         # Max file size before rotation (default: 10MB)
LOGSEQ_MCP_DEBUG=true                # Enable console output (default: false)
LOGSEQ_MCP_LOG_FILE=/custom/path.log # Custom log location (optional)
```

#### Example Privacy Mode Log Entry

```json
{
  "timestamp": "2025-01-15T10:30:45Z",
  "level": "INFO",
  "logger": "logseq_mcp_server.logging_config",
  "message": "Tool get_page completed successfully",
  "tool_name": "get_page",
  "arguments": {
    "name": "My P***nal"
  },
  "result": {
    "success": true,
    "page": {
      "originalName": "My P***nal",
      "uuid": "block_7d4e8c"
    }
  },
  "duration_ms": 45
}
```

#### Viewing Logs

```bash
# View logs in real-time
tail -f logs/logseq-mcp.log

# Search logs while respecting privacy
grep '"level": "ERROR"' logs/logseq-mcp.log
```

#### Temporary Debug Mode

When troubleshooting issues:

```bash
# Run with debug logging temporarily
LOGSEQ_MCP_LOG_MODE=debug python -m logseq_mcp_server

# Or in Claude Desktop config (temporarily):
"env": {
  "LOGSEQ_MCP_LOG_MODE": "debug",
  "LOGSEQ_MCP_LOG_RETENTION_DAYS": "1"
}
```

**Important**: Remember to switch back to privacy mode after debugging to protect your personal data.

## Usage

### Running the Server

```bash
# Run with default stdio transport
python -m logseq_mcp_server

# Run with SSE transport
LOGSEQ_MCP_TRANSPORT=sse python -m logseq_mcp_server

# Run with MCP CLI
mcp run src/logseq_mcp_server/server.py
```

### Available Tools

#### Block Operations
- `create_block`: Create a new block in a page
- `update_block`: Update an existing block's content or properties
- `delete_block`: Delete a block

#### Page Operations
- `create_page`: Create a new page
- `get_all_pages`: Get all pages in the current graph
- `get_page`: Retrieve a page and its content
- `get_journal_page`: Get a journal page by date (supports various date formats)
- `search_pages`: Search for pages by query

#### Query Operations
- `execute_query`: Execute Datalog queries

### Working with Journal Pages

The `get_journal_page` tool provides a convenient way to retrieve journal pages by date, automatically converting various date formats to Logseq's journal page naming convention.

#### Supported Date Formats

The tool accepts dates in multiple formats:
- **ISO format**: `"2023-12-25"`
- **US format**: `"12/25/2023"`
- **EU format**: `"25/12/2023"` 
- **Pre-formatted**: `"December 25th, 2023"`
- **Python date/datetime objects** (when using the API directly)

#### Example Usage

```json
// Get today's journal page
{
  "tool": "get_journal_page",
  "arguments": {
    "date": "2024-01-15"
  }
}

// Get journal with blocks
{
  "tool": "get_journal_page", 
  "arguments": {
    "date": "01/15/2024",
    "include_children": true
  }
}
```

The tool automatically converts the provided date to Logseq's journal format (e.g., "January 15th, 2024") before fetching the page.

## Troubleshooting

If you encounter issues during setup:

1. **Python Version**: Ensure you have Python 3.13+ installed
   ```bash
   python3 --version
   ```

2. **Logseq API**: Make sure the API server is enabled in Logseq:
   - Settings > Advanced > Enable "API Server"
   - Default port is 12315

3. **Connection Issues**: Test the connection manually:
   ```bash
   cd logseq-mcp
   python tests/tools/test_logseq.py get-all-pages --limit 5
   ```

4. **Logs**: Check the logs directory for detailed error information:
   ```bash
   tail -f logs/logseq-mcp.log
   ```

5. **Clean Install**: If all else fails, try a clean installation:
   ```bash
   # Remove existing installation
   rm -rf .venv build dist *.egg-info
   
   # Run setup wizard again
   ./deploy.sh
   ```

## Development

### Testing with the Test Harness

A standalone test harness (`tests/tools/test_logseq.py`) is provided for rapid testing and debugging of Logseq API calls without going through the MCP protocol. This tool is useful for:
- Debugging API connectivity issues
- Testing raw API methods directly
- Exploring Logseq API capabilities interactively
- Verifying API responses before implementing MCP tools

Usage examples:

```bash
# Test specific methods
python tests/tools/test_logseq.py get-page "MCP Server"
python tests/tools/test_logseq.py get-page "Test Page" --show-raw
python tests/tools/test_logseq.py get-all-pages --limit 5
python tests/tools/test_logseq.py search "test"

# Test journal pages
python tests/tools/test_logseq.py get-page "December 25th, 2023"  # Get journal by formatted name

# Raw API calls
python tests/tools/test_logseq.py raw logseq.Editor.getCurrentGraph
python tests/tools/test_logseq.py raw logseq.Editor.getPage "My Page"

# Interactive REPL mode
python tests/tools/test_logseq.py interactive

# Verbose mode for debugging
python tests/tools/test_logseq.py get-page "MCP Server" --verbose
```

The test harness provides:
- Direct access to LogseqClient without MCP overhead
- Pretty-printed JSON output
- Interactive REPL for exploration
- Full request/response logging
- Command history in interactive mode

#### Important Note on Logseq API Arguments

Most Logseq API methods expect arguments to be wrapped in arrays, even for single values:
- **Correct**: `logseq.Editor.getPage ["MCP Server"]`
- **Incorrect**: `logseq.Editor.getPage "MCP Server"`

Methods that require array format: getPage, getPageBlocksTree, getBlock, removeBlock, createPage, insertBlock, updateBlock.
Methods that use string format: search, q (queries).

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/logseq_mcp_server tests/

# Run specific test
pytest tests/unit/test_tools.py -v
```

### Code Quality

```bash
# Run linter
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes using conventional commits
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

### Conventional Commits

This project uses conventional commits. Examples:
- `feat(tools): add block creation tool`
- `fix(api): handle empty query results`
- `docs(readme): update installation instructions`

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

This project is private and proprietary. All rights reserved.

## Acknowledgments

- Built with the [MCP SDK](https://github.com/anthropics/model-context-protocol)
- Integrates with [Logseq](https://logseq.com/)