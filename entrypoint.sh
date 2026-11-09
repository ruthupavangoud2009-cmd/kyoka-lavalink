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
# 3. Process Tracking, State Verification & Signal Traps
# ==============================================================================
NGINX_PID=0
JAVA_PID=0

# Zombie-safe process state inspection (MUST be declared before any invocation)
is_alive() {
    local pid="${1:-}"
    if [ -z "$pid" ] || [ "$pid" -le 0 ] 2>/dev/null; then
        return 1
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
        return 1
    fi
    # If /proc is available, check for zombie (Z) or dead (X/x) state
    if [ -f "/proc/$pid/stat" ]; then
        local state
        state=$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null || echo "Z")
        if [ "$state" = "Z" ] || [ "$state" = "X" ] || [ "$state" = "x" ]; then
            return 1
        fi
    fi
    return 0
}

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
# 4. Launch Services in Order (Backend First, then Edge Gateway)
# ==============================================================================
JAVA_OPTS="${JAVA_OPTS:--Xmx256m -Xms96m -XX:MaxMetaspaceSize=160m -XX:ReservedCodeCacheSize=48m -XX:MaxDirectMemorySize=32m -Xss384k -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication}"

echo "=================================================="
echo " Starting Kyoka Lavalink V4 with Nginx Edge Proxy"
echo "--------------------------------------------------"
echo " Public Port        : ${PORT}"
echo " Backend Listen     : 127.0.0.1:2333 (Loopback)"
echo " Password Protected : [YES] (${#LAVALINK_SERVER_PASSWORD} chars)"
echo " Memory Options     : ${JAVA_OPTS}"
echo "=================================================="

# Ensure execution context is /opt/Lavalink
cd /opt/Lavalink

# Start Lavalink bound strictly to 127.0.0.1 loopback (executed exactly once)
java ${JAVA_OPTS} \
    -Dserver.address=127.0.0.1 \
    -Dserver.port=2333 \
    -jar /opt/Lavalink/Lavalink.jar &
JAVA_PID=$!

echo "[STARTUP] Lavalink Java backend initiated (PID: $JAVA_PID). Awaiting port 2333 readiness..."

# Wait for Lavalink to be fully online and accepting connections before starting Nginx.
READY=0
MAX_WAIT=120

for i in $(seq 1 "$MAX_WAIT"); do
    if ! is_alive "$JAVA_PID"; then
        echo "[STARTUP ERROR] Lavalink Java process terminated during boot! Check stderr above." >&2
        wait "$JAVA_PID" 2>/dev/null || true
        exit 1
    fi

    # Probe port 2333 readiness via loopback
    if curl -fsS --max-time 2 "http://127.0.0.1:2333/metrics" >/dev/null 2>&1 || \
       curl -fsS --max-time 2 -H "Authorization: ${LAVALINK_SERVER_PASSWORD}" "http://127.0.0.1:2333/v4/info" >/dev/null 2>&1; then
        echo "[STARTUP] Lavalink Java backend is fully ONLINE and accepting connections on 127.0.0.1:2333 (boot took ~${i}s)."
        READY=1
        break
    fi

    # Periodic heartbeat diagnostics every 10 seconds to trace startup progress in Render logs
    if [ $((i % 10)) -eq 0 ]; then
        MEM_RSS=$(awk '/VmRSS/{print $2 " " $3}' "/proc/$JAVA_PID/status" 2>/dev/null || echo "N/A")
        PORT_OPEN="NO"
        if grep -q "091D" /proc/net/tcp 2>/dev/null; then
            PORT_OPEN="YES"
        fi
        echo "[STARTUP WAIT] Still waiting for Lavalink backend (elapsed: ${i}s/${MAX_WAIT}s | PID: $JAVA_PID | RSS: $MEM_RSS | Port 2333 bound: $PORT_OPEN)..."
    fi

    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "[STARTUP ERROR] Timed out waiting for Lavalink to bind to 127.0.0.1:2333 after ${MAX_WAIT}s!" >&2
    echo "[STARTUP DIAGNOSTICS] Process status:" >&2
    cat "/proc/$JAVA_PID/status" 2>/dev/null | grep -E "State|VmSize|VmRSS|Threads" >&2 || true
    echo "[STARTUP DIAGNOSTICS] Open TCP listeners:" >&2
    grep "091D" /proc/net/tcp 2>/dev/null >&2 || echo "No listener on port 2333 (091D)." >&2
    if [ -d "/opt/Lavalink/logs" ]; then
        echo "[STARTUP DIAGNOSTICS] Recent application logs:" >&2
        tail -n 30 /opt/Lavalink/logs/* 2>/dev/null >&2 || true
    fi
    kill -TERM "$JAVA_PID" 2>/dev/null || true
    wait "$JAVA_PID" 2>/dev/null || true
    exit 1
fi

# Start Nginx: Now that the backend is 100% online, Nginx edge proxy will never receive connection refused!
echo "[STARTUP] Starting Nginx edge proxy on public port ${PORT}..."
nginx -g "daemon off;" &
NGINX_PID=$!

# ==============================================================================
# 5. Active Supervisor Loop (Zombie-Safe Process Monitoring)
# ==============================================================================
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
