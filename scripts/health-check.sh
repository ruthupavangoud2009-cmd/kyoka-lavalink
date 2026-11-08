#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_URL="${1:-${RENDER_SERVICE_URL:-http://localhost:2333}}"
PASSWORD="${2:-${LAVALINK_SERVER_PASSWORD:-youshallnotpass}}"

python3 "$DIR/scripts/health_check.py" --url "$TARGET_URL" --password "$PASSWORD"
