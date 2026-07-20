#!/bin/zsh

set -euo pipefail
RESOURCE_DIR="${0:A:h}"
exec "$RESOURCE_DIR/app/mtga-deck-downloader" "$@"
