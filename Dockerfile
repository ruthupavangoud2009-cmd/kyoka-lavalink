# ==============================================================================
# KYOKA LAVALINK V4 - OFFICIAL DOCKERFILE WITH NGINX GATEWAY
# ==============================================================================
# Base: Official Lavalink v4 Alpine image (Eclipse Temurin JRE 21 on Alpine Linux)
# Registry: ghcr.io/lavalink-devs/lavalink:4-alpine
# Target: Render Free Web Service (Docker Runtime)
# ==============================================================================

FROM ghcr.io/lavalink-devs/lavalink:4-alpine

USER root

# Install Nginx, envsubst (gettext), curl, bash, and procps
RUN apk add --no-cache nginx gettext curl bash ca-certificates procps

WORKDIR /opt/Lavalink

# Create directories
RUN mkdir -p /opt/Lavalink/plugins /opt/Lavalink/logs /var/www/html /run/nginx

# Copy static status page, Nginx template, and configuration
COPY public/index.html /var/www/html/index.html
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY application.yml /opt/Lavalink/application.yml
COPY entrypoint.sh /entrypoint.sh

# Set executable permissions
RUN chmod +x /entrypoint.sh

EXPOSE 10000

# Native container check validates /healthz via Nginx edge gateway
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-10000}/healthz" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
