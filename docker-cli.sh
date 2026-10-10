#!/usr/bin/env bash
# Forward the original CLI syntax to the Docker container.
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
    DIRECTORY="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" = /* ]] || SOURCE="$DIRECTORY/$SOURCE"
done
PROJECT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required. Install/start Docker, then retry." >&2
    exit 1
fi
COMPOSE=(docker compose --project-directory "$PROJECT_DIR" -f "$PROJECT_DIR/compose.yaml")
OPTIONS=(run --rm)
# Keep TTY for interactive SSH/dashboard; allow pipes and scripts too.
if [[ ! -t 0 || ! -t 1 ]]; then
    OPTIONS+=(-T)
fi
exec "${COMPOSE[@]}" "${OPTIONS[@]}" ssh-cred "$@"
