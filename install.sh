#!/bin/bash
# SSH Credential Manager - Installation Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

echo "🚀 Installing SSH Credential Manager..."
echo ""

# Create bin directory if it doesn't exist
mkdir -p "$BIN_DIR"

# Install the package in editable mode
echo "📦 Installing package..."
cd "$PROJECT_DIR"
uv pip install -e .

# Create symlinks to the binaries
echo "🔗 Creating symlinks..."

# Remove old symlinks if they exist
rm -f "$BIN_DIR/ssh-cred"
rm -f "$BIN_DIR/ssc"

# Create new symlinks
ln -s "$PROJECT_DIR/.venv/bin/ssh-cred" "$BIN_DIR/ssh-cred"
ln -s "$PROJECT_DIR/.venv/bin/ssc" "$BIN_DIR/ssc"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Commands available:"
echo "  ssh-cred    - Full command"
echo "  ssc         - Short command"
echo ""
echo "Quick test:"
echo "  ssh-cred version"
echo "  ssc version"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Warning: $HOME/.local/bin is not in your PATH"
    echo ""
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then reload your shell:"
    echo "  source ~/.bashrc  # or source ~/.zshrc"
    echo ""
else
    echo "✅ $HOME/.local/bin is already in your PATH"
    echo ""
    echo "Try it now:"
    echo "  ssh-cred version"
    echo "  ssc list"
    echo "  ssc connect"
    echo ""
fi

