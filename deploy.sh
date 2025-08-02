#!/bin/bash

# Logseq MCP Server Deployment Script
# This script helps set up the Logseq MCP server for use with Claude Desktop or Cline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Logseq MCP Server Setup Wizard         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Claude Desktop config path
get_claude_config_path() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "$APPDATA/Claude/claude_desktop_config.json"
    else
        echo "$HOME/.config/Claude/claude_desktop_config.json"
    fi
}

# Step 1: Check Python version
echo -e "${YELLOW}Step 1: Checking Python version...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}✗ Python 3.13+ required, but $PYTHON_VERSION found${NC}"
        echo "Please install Python 3.13 or higher and try again."
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.13+ and try again."
    exit 1
fi

# Step 2: Check for uv
echo -e "\n${YELLOW}Step 2: Checking for uv package manager...${NC}"
if command_exists uv; then
    echo -e "${GREEN}✓ uv is installed${NC}"
else
    echo -e "${YELLOW}uv not found. Would you like to install it? (recommended)${NC}"
    read -p "Install uv? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo -e "${GREEN}✓ uv installed successfully${NC}"
        echo "Please restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
        echo "Then run this script again."
        exit 0
    else
        echo -e "${YELLOW}Continuing with pip...${NC}"
        USE_PIP=true
    fi
fi

# Step 3: Install dependencies
echo -e "\n${YELLOW}Step 3: Installing dependencies...${NC}"
cd "$SCRIPT_DIR"

if [ -z "$USE_PIP" ]; then
    echo "Installing with uv..."
    uv pip install --system -e .
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo "Installing with pip..."
    pip install -e .
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Step 4: Configure Logseq API
echo -e "\n${YELLOW}Step 4: Configuring Logseq API connection...${NC}"

# Check if env directory exists
if [ ! -d "env" ]; then
    mkdir -p env
fi

# Check if .env file exists
if [ -f "env/.env" ]; then
    echo -e "${YELLOW}Found existing env/.env file${NC}"
    read -p "Do you want to reconfigure? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing configuration..."
    else
        cp env/.env env/.env.backup.$(date +%Y%m%d%H%M%S)
        echo "Backed up existing config to env/.env.backup.*"
    fi
else
    REPLY="y"
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Copy template if it exists
    if [ -f "env/.env.example" ]; then
        cp env/.env.example env/.env
    fi
    
    # Get Logseq API settings
    read -p "Logseq API Host [localhost]: " LOGSEQ_HOST
    LOGSEQ_HOST=${LOGSEQ_HOST:-localhost}
    
    read -p "Logseq API Port [12315]: " LOGSEQ_PORT
    LOGSEQ_PORT=${LOGSEQ_PORT:-12315}
    
    read -p "Logseq API Token (optional, press Enter to skip): " LOGSEQ_TOKEN
    
    # Write to .env file
    cat > env/.env << EOF
# Logseq API Configuration
LOGSEQ_API_HOST=$LOGSEQ_HOST
LOGSEQ_API_PORT=$LOGSEQ_PORT
LOGSEQ_API_TOKEN=$LOGSEQ_TOKEN

# MCP Server Configuration
LOGSEQ_MCP_TRANSPORT=stdio

# Logging Configuration
LOGSEQ_MCP_LOG_MODE=privacy
LOGSEQ_MCP_LOG_LEVEL=INFO
LOGSEQ_MCP_LOG_RETENTION_DAYS=7
LOGSEQ_MCP_LOG_MAX_SIZE=10MB
EOF
    
    echo -e "${GREEN}✓ Configuration saved to env/.env${NC}"
fi

# Step 5: Test connection
echo -e "\n${YELLOW}Step 5: Testing Logseq connection...${NC}"
echo "Make sure Logseq is running with the API server enabled!"
echo "To enable the API server in Logseq:"
echo "  1. Open Logseq"
echo "  2. Go to Settings > Advanced"
echo "  3. Enable 'API Server'"
echo "  4. Note the port number (default: 12315)"
echo
read -p "Press Enter when Logseq is ready..."

# Test the connection
python3 -c "
import asyncio
import sys
sys.path.insert(0, '$SCRIPT_DIR/src')
from logseq_mcp_server.logseq.client import LogseqClient
import os
from dotenv import load_dotenv

load_dotenv('$SCRIPT_DIR/env/.env')

async def test():
    try:
        client = LogseqClient(
            host=os.getenv('LOGSEQ_API_HOST', 'localhost'),
            port=int(os.getenv('LOGSEQ_API_PORT', '12315')),
            token=os.getenv('LOGSEQ_API_TOKEN')
        )
        graph = await client.get_current_graph()
        print(f'✓ Connected to graph: {graph.get(\"name\", \"Unknown\")}')
        await client.close()
        return True
    except Exception as e:
        print(f'✗ Connection failed: {e}')
        await client.close()
        return False

success = asyncio.run(test())
sys.exit(0 if success else 1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully connected to Logseq!${NC}"
else
    echo -e "${RED}✗ Could not connect to Logseq${NC}"
    echo "Please check:"
    echo "  - Logseq is running"
    echo "  - API server is enabled in Logseq settings"
    echo "  - The host and port are correct"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 6: Configure Claude Desktop or Cline
echo -e "\n${YELLOW}Step 6: Configure your AI assistant...${NC}"
echo "Which assistant are you setting up?"
echo "  1) Claude Desktop"
echo "  2) Cline (VS Code extension)"
echo "  3) Other/Manual setup"
read -p "Select (1-3): " -n 1 -r ASSISTANT_CHOICE
echo

case $ASSISTANT_CHOICE in
    1)
        # Claude Desktop setup
        CONFIG_PATH=$(get_claude_config_path)
        CONFIG_DIR=$(dirname "$CONFIG_PATH")
        
        echo -e "\n${YELLOW}Setting up Claude Desktop...${NC}"
        
        # Create config directory if it doesn't exist
        if [ ! -d "$CONFIG_DIR" ]; then
            mkdir -p "$CONFIG_DIR"
            echo "Created config directory: $CONFIG_DIR"
        fi
        
        # Generate the config snippet
        if [ -z "$USE_PIP" ]; then
            # uv configuration
            cat > /tmp/logseq_mcp_config.json << EOF
{
  "mcpServers": {
    "logseq": {
      "command": "uv",
      "args": [
        "--directory",
        "$SCRIPT_DIR",
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
        "LOGSEQ_API_HOST": "$LOGSEQ_HOST",
        "LOGSEQ_API_PORT": "$LOGSEQ_PORT",
        "LOGSEQ_API_TOKEN": "$LOGSEQ_TOKEN",
        "LOGSEQ_MCP_LOG_LEVEL": "INFO",
        "LOGSEQ_MCP_PROJECT_ROOT": "$SCRIPT_DIR"
      }
    }
  }
}
EOF
        else
            # pip configuration
            cat > /tmp/logseq_mcp_config.json << EOF
{
  "mcpServers": {
    "logseq": {
      "command": "python3",
      "args": [
        "-m",
        "logseq_mcp_server"
      ],
      "cwd": "$SCRIPT_DIR",
      "env": {
        "LOGSEQ_API_HOST": "$LOGSEQ_HOST",
        "LOGSEQ_API_PORT": "$LOGSEQ_PORT",
        "LOGSEQ_API_TOKEN": "$LOGSEQ_TOKEN",
        "LOGSEQ_MCP_LOG_LEVEL": "INFO",
        "LOGSEQ_MCP_PROJECT_ROOT": "$SCRIPT_DIR"
      }
    }
  }
}
EOF
        fi
        
        echo -e "${GREEN}Configuration generated!${NC}"
        echo
        echo "The configuration has been saved to: /tmp/logseq_mcp_config.json"
        echo
        echo -e "${YELLOW}To complete setup:${NC}"
        echo "1. If Claude Desktop config exists, merge this with your existing config"
        echo "2. If not, copy this as your new config:"
        echo "   cp /tmp/logseq_mcp_config.json \"$CONFIG_PATH\""
        echo
        echo "3. Restart Claude Desktop"
        echo
        echo -e "${BLUE}The config file is at: $CONFIG_PATH${NC}"
        ;;
        
    2)
        # Cline setup
        echo -e "\n${YELLOW}Setting up Cline...${NC}"
        echo
        echo "Add the following to your Cline settings in VS Code:"
        echo "(Settings > Extensions > Cline > MCP Servers)"
        echo
        
        if [ -z "$USE_PIP" ]; then
            cat << EOF
{
  "logseq": {
    "command": "uv",
    "args": [
      "--directory",
      "$SCRIPT_DIR",
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
      "LOGSEQ_API_HOST": "$LOGSEQ_HOST",
      "LOGSEQ_API_PORT": "$LOGSEQ_PORT",
      "LOGSEQ_API_TOKEN": "$LOGSEQ_TOKEN"
    }
  }
}
EOF
        else
            cat << EOF
{
  "logseq": {
    "command": "python3",
    "args": ["-m", "logseq_mcp_server"],
    "cwd": "$SCRIPT_DIR",
    "env": {
      "LOGSEQ_API_HOST": "$LOGSEQ_HOST",
      "LOGSEQ_API_PORT": "$LOGSEQ_PORT",
      "LOGSEQ_API_TOKEN": "$LOGSEQ_TOKEN"
    }
  }
}
EOF
        fi
        ;;
        
    3)
        # Manual setup
        echo -e "\n${YELLOW}Manual setup instructions:${NC}"
        echo
        echo "To run the server manually:"
        if [ -z "$USE_PIP" ]; then
            echo "  cd $SCRIPT_DIR"
            echo "  uv run python -m logseq_mcp_server"
        else
            echo "  cd $SCRIPT_DIR"
            echo "  python3 -m logseq_mcp_server"
        fi
        echo
        echo "Environment variables are loaded from: $SCRIPT_DIR/env/.env"
        ;;
esac

echo
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Setup Complete! 🎉               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo
echo "Next steps:"
echo "  1. Make sure Logseq is running with API server enabled"
echo "  2. Configure your AI assistant with the settings above"
echo "  3. Restart your AI assistant to load the MCP server"
echo
echo "For more information, see the README.md file."
echo