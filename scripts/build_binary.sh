#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
uv sync --frozen
uv run --frozen pyinstaller --noconfirm --clean --distpath dist/binary --workpath build/pyinstaller ssc.spec
