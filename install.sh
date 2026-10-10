#!/usr/bin/env bash
# Install/build only. Short command links are opt-in via setup.sh.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:---docker}"
case "$MODE" in
    --docker)
        command -v docker >/dev/null 2>&1 || { echo "Install/start Docker before running ./install.sh." >&2; exit 1; }
        docker compose version >/dev/null
        docker info >/dev/null
        docker compose --project-directory "$PROJECT_DIR" -f "$PROJECT_DIR/compose.yaml" build
        ;;
    --local)
        command -v uv >/dev/null 2>&1 || { echo "Local mode requires uv." >&2; exit 1; }
        cd "$PROJECT_DIR"
        [[ -x .venv/bin/python ]] || uv venv --python 3.13 .venv
        uv pip install --python "$PROJECT_DIR/.venv/bin/python" -e .
        ;;
    *) echo "Usage: ./install.sh [--docker|--local]" >&2; exit 2 ;;
esac
echo "Installation complete."
echo "Docker: docker compose run --rm ssh-cred tui"
echo "Optional short commands: ./setup.sh (Docker) or ./setup.sh --local (native)"
