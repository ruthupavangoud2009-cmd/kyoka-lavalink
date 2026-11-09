#!/usr/bin/env bash
# ==============================================================================
# 24/7 Keep-Alive Background Worker (Linux / Mac)
# ==============================================================================
TARGET_URL="${1:-${RENDER_SERVICE_URL:-https://kyoka-lavalink.onrender.com}}"
INTERVAL="${2:-540}"
PASSWORD="${3:-${LAVALINK_SERVER_PASSWORD:-${LAVALINK_PASSWORD}}}"

if [ -z "$TARGET_URL" ]; then
    echo "Usage: ./scripts/keepalive.sh <RENDER_URL> [INTERVAL_SECONDS] [PASSWORD]"
    echo "Example: ./scripts/keepalive.sh https://kyoka-lavalink.onrender.com 540 my_password"
    exit 1
fi

echo "=================================================="
echo " Starting 24/7 Keep-Alive Worker"
echo " Target   : ${TARGET_URL}/version"
echo " Interval : ${INTERVAL}s"
if [ -n "$PASSWORD" ]; then
    echo " Auth     : Configured (Clean 200 OK pings)"
else
    echo " Auth     : None (Pings will return 401 but still keep container awake)"
fi
echo "=================================================="

while true; do
    DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    if [ -n "$PASSWORD" ]; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -H "Authorization: ${PASSWORD}" "${TARGET_URL}/version" || echo "FAILED")
    else
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${TARGET_URL}/version" || echo "FAILED")
    fi
    echo "[$DATE] Keep-alive ping -> HTTP $STATUS"
    sleep "$INTERVAL"
done
