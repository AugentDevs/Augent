#!/bin/bash
# Augent Setup Script
# One-liner: curl -sSL https://raw.githubusercontent.com/AugentDevs/Augent/main/setup.sh | bash

set -e

echo "=================================="
echo "  Augent - Audio Intelligence"
echo "  for Claude Code Agents"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[ok]${NC} Python $PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is required but not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}[ok]${NC} pip found"

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}[ok]${NC} FFmpeg found"
else
    echo -e "${YELLOW}[warn]${NC} FFmpeg not found - clip extraction will be limited"
    echo "       Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
fi

# Install Augent
echo ""
echo "Installing Augent..."
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    # Local install (development mode)
    pip3 install -e "$SCRIPT_DIR" --quiet
else
    # Remote install
    pip3 install augent --quiet
fi

echo -e "${GREEN}[ok]${NC} Augent installed"

# Verify installation
if command -v augent &> /dev/null; then
    echo -e "${GREEN}[ok]${NC} CLI available: augent"
else
    echo -e "${YELLOW}[warn]${NC} CLI not in PATH - try: python3 -m augent.cli"
fi

if command -v augent-mcp &> /dev/null; then
    echo -e "${GREEN}[ok]${NC} MCP server available: augent-mcp"
else
    echo -e "${YELLOW}[warn]${NC} MCP server not in PATH - try: python3 -m augent.mcp"
fi

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add to your Claude Code project (.mcp.json):"
echo ""
echo '   {'
echo '     "mcpServers": {'
echo '       "augent": {'
echo '         "command": "augent-mcp"'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "2. Or for Claude Desktop (claude_desktop_config.json):"
echo ""
echo '   {'
echo '     "mcpServers": {'
echo '       "augent": {'
echo '         "command": "python3",'
echo '         "args": ["-m", "augent.mcp"]'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "3. Test the CLI:"
echo "   augent --help"
echo ""
echo "Documentation: https://github.com/AugentDevs/Augent"
echo ""
