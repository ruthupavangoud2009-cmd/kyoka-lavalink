#!/usr/bin/env bash
# ==============================================================================
# 24/7 Keep-Alive Background Worker (Linux / Mac)
# ==============================================================================
TARGET_URL="${1:-${RENDER_SERVICE_URL:-https://kyoka-lavalink.onrender.com}}"
INTERVAL="${2:-540}"

if [ -z "$TARGET_URL" ]; then
    echo "Usage: ./scripts/keepalive.sh <RENDER_URL> [INTERVAL_SECONDS]"
    echo "Example: ./scripts/keepalive.sh https://kyoka-lavalink.onrender.com 540"
    exit 1
fi

echo "Starting Keep-Alive ping loop for: $TARGET_URL every ${INTERVAL}s"
while true; do
    DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${TARGET_URL}/version" || echo "FAILED")
    echo "[$DATE] Keep-alive ping -> HTTP $STATUS"
    sleep "$INTERVAL"
done

