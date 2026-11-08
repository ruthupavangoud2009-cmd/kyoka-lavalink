# ==============================================================================
# KYOKA LAVALINK V4 - OFFICIAL DOCKERFILE
# ==============================================================================
# Base: Official Lavalink v4 Alpine image (Eclipse Temurin JRE 21 on Alpine Linux)
# Registry: ghcr.io/lavalink-devs/lavalink:4-alpine
# Target: Render Free Web Service (Docker Runtime)
# ==============================================================================

FROM ghcr.io/lavalink-devs/lavalink:4-alpine

USER root

# Install lightweight diagnostic and network utilities
RUN apk add --no-cache curl bash ca-certificates

WORKDIR /opt/Lavalink

# Create directories for plugin auto-download and logging
RUN mkdir -p /opt/Lavalink/plugins /opt/Lavalink/logs

# Copy configuration and entrypoint
COPY application.yml /opt/Lavalink/application.yml
COPY entrypoint.sh /entrypoint.sh

# Fix permissions for the lavalink service user (UID 322)
RUN chmod +x /entrypoint.sh \
    && chown -R 322:322 /opt/Lavalink /entrypoint.sh

# Switch to standard non-root user
USER 322

# Expose default Lavalink port (Render routes dynamic $PORT to the container)
EXPOSE 2333

# Native container healthcheck verifying Lavalink v4 /version endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-2333}/version" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
