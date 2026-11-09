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

# Pre-download plugins at build time to eliminate startup network latency and bandwidth bottlenecks
RUN curl -fsSL -o /opt/Lavalink/plugins/youtube-plugin-1.18.2.jar \
    https://maven.lavalink.dev/releases/dev/lavalink/youtube/youtube-plugin/1.18.2/youtube-plugin-1.18.2.jar && \
    curl -fsSL -o /opt/Lavalink/plugins/lavasrc-plugin-4.8.3.jar \
    https://maven.lavalink.dev/releases/com/github/topi314/lavasrc/lavasrc-plugin/4.8.3/lavasrc-plugin-4.8.3.jar

# Safe baseline JVM options for 512MB Render Free tier (160m Metaspace prevents classload starvation)
ENV JAVA_OPTS="-Xmx256m -Xms96m -XX:MaxMetaspaceSize=160m -XX:ReservedCodeCacheSize=48m -XX:MaxDirectMemorySize=32m -Xss384k -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication"

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
