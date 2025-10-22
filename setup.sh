#!/bin/bash

# OpenAI Images MCP Server - Quick Setup Script
# This script helps set up the MCP server for Claude Desktop

set -e  # Exit on error

echo "======================================"
echo "OpenAI Images MCP Server Setup"
echo "======================================"

# Check Python version
echo -n "Checking Python version... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "Found Python $PYTHON_VERSION"
else
    echo "ERROR: Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check for API key
echo ""
echo "Checking for OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set."
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    if [ ! -z "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
        echo "export OPENAI_API_KEY='$api_key'" >> ~/.bashrc
        echo "✓ API key set and saved to ~/.bashrc"
    else
        echo "You'll need to set OPENAI_API_KEY before using the server."
    fi
else
    echo "✓ API key found"
fi

# Detect OS and configure Claude Desktop
echo ""
echo "Configuring Claude Desktop..."

# Get the full path to the MCP server
MCP_PATH="$(pwd)/openai_images_mcp.py"

# Determine config file location based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
else
    # Linux or other
    CONFIG_DIR="$HOME/.config/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
fi

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo "Found existing Claude Desktop config at: $CONFIG_FILE"
    echo ""
    echo "⚠️  Please manually add the following to your config file:"
else
    echo "Creating Claude Desktop config at: $CONFIG_FILE"
    # Create new config file
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "openai-images": {
      "command": "python3",
      "args": [
        "$MCP_PATH"
      ],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY:-your-api-key-here}"
      }
    }
  }
}
EOF
    echo "✓ Config file created"
fi

echo ""
echo "Configuration to add to $CONFIG_FILE:"
echo "----------------------------------------"
cat << EOF
{
  "mcpServers": {
    "openai-images": {
      "command": "python3",
      "args": [
        "$MCP_PATH"
      ],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY:-your-api-key-here}"
      }
    }
  }
}
EOF
echo "----------------------------------------"

# Test the server
echo ""
echo "Testing the MCP server..."
python3 test_mcp_server.py

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Ensure your API key is set: export OPENAI_API_KEY='your-key'"
echo "2. Restart Claude Desktop"
echo "3. Try asking Claude: 'Generate an image of a futuristic city'"
echo ""
echo "Server location: $MCP_PATH"
echo "Config location: $CONFIG_FILE"
echo ""
echo "For more information, see README.md"
