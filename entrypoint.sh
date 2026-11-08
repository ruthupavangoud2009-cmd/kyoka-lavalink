#!/bin/sh
set -e

# ==============================================================================
# KYOKA LAVALINK V4 - CONTAINER ENTRYPOINT
# ==============================================================================

# Ensure PORT is populated (Render dynamically sets $PORT, default is 2333)
PORT="${PORT:-2333}"
export SERVER_PORT="${PORT}"

# Memory settings tuned for Render Free (512 MB hard container RAM limit)
DEFAULT_JAVA_OPTS="-Xmx384m -Xms128m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication -Dfile.encoding=UTF-8"
JAVA_OPTS="${JAVA_OPTS:-$DEFAULT_JAVA_OPTS}"

# Ensure required directories exist
mkdir -p /opt/Lavalink/plugins /opt/Lavalink/logs

echo "=================================================="
echo " Starting Kyoka Lavalink V4 Server"
echo "--------------------------------------------------"
echo " Target Port       : ${PORT}"
echo " Host Address      : 0.0.0.0"
echo " Memory Settings   : ${JAVA_OPTS}"
if [ -n "$LAVALINK_SERVER_PASSWORD" ] || [ -n "$LAVALINK_PASSWORD" ]; then
    echo " Authentication    : Configured (Secure Password Set)"
else
    echo " Authentication    : Warning: Using default password (Set LAVALINK_SERVER_PASSWORD in Render)"
fi
echo " Working Directory : $(pwd)"
echo " Java Version      : $(java -version 2>&1 | head -n 1)"
echo "=================================================="

# Forward SIGTERM / SIGINT for graceful shutdown
term_handler() {
    echo "[ENTRYPOINT] SIGTERM received - gracefully stopping Lavalink..."
    if [ -n "$PID" ]; then
        kill -TERM "$PID" 2>/dev/null
        wait "$PID"
    fi
    exit 0
}

trap 'term_handler' TERM INT

# Launch Lavalink with JVM options, explicit server port and address bindings
java $JAVA_OPTS \
    -Dserver.port="${PORT}" \
    -Dserver.address="0.0.0.0" \
    -jar /opt/Lavalink/Lavalink.jar &

PID=$!
wait "$PID"

