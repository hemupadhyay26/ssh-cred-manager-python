#!/usr/bin/env bash
# Local checks used by contributors and the optional pre-commit hook.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
command -v uv >/dev/null 2>&1 || { echo "Install uv to run contributor checks." >&2; exit 1; }
uv sync --frozen
uv run --frozen ruff check .
bash -n install.sh setup.sh docker-cli.sh scripts/check.sh scripts/build_binary.sh .githooks/pre-commit
uv run --frozen python -m unittest discover -s tests -v
git diff --check
git diff --cached --check
