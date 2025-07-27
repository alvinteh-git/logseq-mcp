# Logseq MCP Server

An MCP (Model Context Protocol) server for interacting with Logseq graphs, enabling AI assistants to read, create, and manipulate Logseq content.

## Features

- **Block Operations**: Create, update, and delete blocks
- **Page Management**: Create pages, retrieve page content, search pages
- **Query Execution**: Execute Datalog queries against your Logseq graph
- **MCP Protocol**: Full compliance with the Model Context Protocol specification

## Prerequisites

- Python 3.13+
- Logseq with API enabled
- uv (recommended) or pip for package management

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/logseq-mcp.git
cd logseq-mcp

# Install dependencies
uv pip install --system -e .

# Install development dependencies (optional)
uv pip install --system -e ".[dev]"
```

### Using pip

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

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure your Logseq API settings in `.env`:
   ```env
   LOGSEQ_API_HOST=localhost
   LOGSEQ_API_PORT=12315
   ```

3. Enable the Logseq API in your Logseq settings

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
- `get_page`: Retrieve a page and its content
- `search_pages`: Search for pages by query

#### Query Operations
- `execute_query`: Execute Datalog queries

## Development

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

MIT License - see LICENSE file for details

## Acknowledgments

- Built with the [MCP SDK](https://github.com/anthropics/model-context-protocol)
- Integrates with [Logseq](https://logseq.com/)