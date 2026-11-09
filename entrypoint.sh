#!/bin/bash
set -Eeuo pipefail

# ==============================================================================
# 1. Strict Password Enforcement (No Insecure Defaults)
# ==============================================================================
if [ -z "${LAVALINK_SERVER_PASSWORD:-}" ]; then
    echo "[ENTRYPOINT ERROR] LAVALINK_SERVER_PASSWORD is missing or empty." >&2
    echo "[ENTRYPOINT ERROR] Refusing to start with insecure or empty credentials." >&2
    echo "[ENTRYPOINT ERROR] Configure LAVALINK_SERVER_PASSWORD in Render Dashboard." >&2
    exit 1
fi

PORT="${PORT:-10000}"
export PORT

# ==============================================================================
# 2. Template Generation & Syntax Verification
# ==============================================================================
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
nginx -t -c /etc/nginx/nginx.conf

# ==============================================================================
# 3. Process Tracking & Signal Traps
# ==============================================================================
NGINX_PID=0
JAVA_PID=0

cleanup() {
    echo "[SUPERVISOR] Termination signal received. Initiating graceful shutdown..."
    if [ "$NGINX_PID" -gt 0 ] && kill -0 "$NGINX_PID" 2>/dev/null; then
        kill -TERM "$NGINX_PID" 2>/dev/null || true
    fi
    if [ "$JAVA_PID" -gt 0 ] && kill -0 "$JAVA_PID" 2>/dev/null; then
        kill -TERM "$JAVA_PID" 2>/dev/null || true
    fi
    
    [ "$NGINX_PID" -gt 0 ] && wait "$NGINX_PID" 2>/dev/null || true
    [ "$JAVA_PID" -gt 0 ] && wait "$JAVA_PID" 2>/dev/null || true
    echo "[SUPERVISOR] All processes stopped cleanly."
    exit 0
}

trap cleanup SIGTERM SIGINT

# ==============================================================================
# 4. Launch Services
# ==============================================================================
echo "=================================================="
echo " Starting Kyoka Lavalink V4 with Nginx Edge Proxy"
echo "--------------------------------------------------"
echo " Public Port        : ${PORT}"
echo " Backend Listen     : 127.0.0.1:2333 (Loopback)"
echo " Password Protected : [YES] (${#LAVALINK_SERVER_PASSWORD} chars)"
echo " Memory Options     : ${JAVA_OPTS:-Defaults}"
echo "=================================================="

# Start Nginx
nginx -g "daemon off;" &
NGINX_PID=$!

# Start Lavalink bound strictly to 127.0.0.1 loopback
java ${JAVA_OPTS:-} \
    -Dserver.address=127.0.0.1 \
    -Dserver.port=2333 \
    -jar /opt/Lavalink/Lavalink.jar &
JAVA_PID=$!

# ==============================================================================
# 5. Active Supervisor Loop (Zombie-Safe Process Monitoring)
# ==============================================================================
is_alive() {
    local pid=$1
    if [ ! -d "/proc/$pid" ]; then
        return 1
    fi
    local state
    state=$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null || echo "Z")
    if [ "$state" = "Z" ] || [ -z "$state" ]; then
        return 1
    fi
    return 0
}

EXIT_STATUS=0

while true; do
    if ! is_alive "$NGINX_PID"; then
        echo "[SUPERVISOR ERROR] Nginx process terminated unexpectedly!" >&2
        EXIT_STATUS=1
        break
    fi
    if ! is_alive "$JAVA_PID"; then
        echo "[SUPERVISOR ERROR] Lavalink Java process terminated unexpectedly!" >&2
        EXIT_STATUS=1
        break
    fi
    sleep 2 &
    wait $! 2>/dev/null || true
done

# Terminate surviving child and reap both
echo "[SUPERVISOR] Terminating surviving processes..."
kill -TERM "$NGINX_PID" "$JAVA_PID" 2>/dev/null || true
wait "$NGINX_PID" 2>/dev/null || true
wait "$JAVA_PID" 2>/dev/null || true

echo "[SUPERVISOR] Container exiting with status $EXIT_STATUS."
exit "$EXIT_STATUS"
