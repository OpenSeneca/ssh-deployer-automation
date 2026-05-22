#!/bin/bash
# Installation script for ssh-deployer-automation

set -e

TOOL_DIR="$HOME/.openclaw/workspace/tools/ssh-deployer-automation"

echo "Installing SSH Deployment Automation Tool..."

# Check if tool directory exists
if [ ! -d "$TOOL_DIR" ]; then
    echo "Error: Tool directory not found: $TOOL_DIR"
    exit 1
fi

# Create symlink in ~/.local/bin
mkdir -p "$HOME/.local/bin"

if [ -L "$HOME/.local/bin/ssh-deploy-automation" ]; then
    echo "Removing existing symlink..."
    rm "$HOME/.local/bin/ssh-deploy-automation"
fi

ln -s "$TOOL_DIR/main.py" "$HOME/.local/bin/ssh-deploy-automation"
chmod +x "$HOME/.local/bin/ssh-deploy-automation"

echo "✓ Installed ssh-deploy-automation to ~/.local/bin/"
echo ""
echo "Usage:"
echo "  ssh-deploy-automation              # Check status"
echo "  ssh-deploy-automation --help       # Show help"
echo "  ssh-deploy-automation --json       # JSON output"
echo "  ssh-deploy-automation --watch      # Watch mode"
echo ""
