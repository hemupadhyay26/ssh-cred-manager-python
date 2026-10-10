#!/usr/bin/env bash
# Optional: expose ssc and ssh-cred from any directory. No shell profile edits.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SSC_BIN_DIR:-$HOME/.local/bin}"
MODE="${1:---docker}"
case "$MODE" in
    --docker)
        command -v docker >/dev/null 2>&1 || { echo "Docker is required. Run ./install.sh first." >&2; exit 1; }
        docker compose version >/dev/null
        TARGET="$PROJECT_DIR/docker-cli.sh"
        ;;
    --local)
        TARGET="$PROJECT_DIR/.venv/bin/ssc"
        [[ -x "$TARGET" ]] || { echo "Run ./install.sh --local first." >&2; exit 1; }
        ;;
    --help|-h)
        echo "Usage: ./setup.sh [--docker|--local]"
        echo "Optional setup for ssc and ssh-cred in ~/.local/bin; Docker is the default backend."
        exit 0
        ;;
    *) echo "Usage: ./setup.sh [--docker|--local]" >&2; exit 2 ;;
esac
for COMMAND in ssc ssh-cred; do
    if [[ -e "$BIN_DIR/$COMMAND" || -L "$BIN_DIR/$COMMAND" ]]; then
        if [[ ! -L "$BIN_DIR/$COMMAND" || "$(readlink "$BIN_DIR/$COMMAND")" != "$TARGET" ]]; then
            echo "Existing command: $BIN_DIR/$COMMAND. Move it aside before running setup." >&2
            exit 1
        fi
    fi
done
mkdir -p "$BIN_DIR"
for COMMAND in ssc ssh-cred; do
    ln -sfn "$TARGET" "$BIN_DIR/$COMMAND"
done
echo "Short commands installed ($MODE): ssc tui, ssc connect, ssc list"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo 'Add this to your shell profile: export PATH="$HOME/.local/bin:$PATH"'
fi
echo 'If an old alias overrides a command: unalias ssc ssh-cred 2>/dev/null; hash -r'
