# Render Free Deployment Guide

This guide provides step-by-step instructions for deploying **Kyoka Lavalink V4** on Render's **Free Tier** ($0/month) with zero unexpected charges.

---

## Important Rules for Free Tier

> [!IMPORTANT]
> - Always select the **Free** instance type.
> - Render Free allows **512 MB RAM** and **0.1 CPU**.
> - Memory settings in this repository (`-Xmx384m`) are pre-calibrated to stay safely under the 512 MB limit to prevent Out-Of-Memory (OOM) crashes.
> - Never upgrade to a paid plan unless you intentionally want paid features.

---

## Method 1: Blueprint Deployment (Recommended - Easiest)

Render Blueprints automatically configure the service using `render.yaml`.

1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Select your repository: `ruthupavangoud2009-cmd/kyoka-lavalink`.
4. Render will read `render.yaml` and display:
   - **Service Name**: `kyoka-lavalink`
   - **Runtime**: `Docker`
   - **Plan**: `Free`
   - **Health Check Path**: `/version`
   - **Auto-generated Password**: `LAVALINK_SERVER_PASSWORD`
5. Click **Apply**.
6. Render will automatically build the Docker image, download plugins, and start the service!

---

## Method 2: Manual Web Service Creation

If you prefer setting up manually:

1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub repository: `ruthupavangoud2009-cmd/kyoka-lavalink`.
3. Set the following fields:
   - **Name**: `kyoka-lavalink` (or any custom name)
   - **Region**: `Oregon (US West)` or `Frankfurt (EU)` (closest to your Discord bot)
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Build Context Directory**: `.`
   - **Instance Type**: **Free** ($0/month)
4. Expand **Advanced**:
   - **Health Check Path**: `/version`
   - **Auto-Deploy**: `Yes`
5. Under **Environment Variables**, add:
   - `LAVALINK_SERVER_PASSWORD`: `<your-random-secure-password>`
     *(Use `python scripts/generate_password.py` to generate one)*
   - `JAVA_OPTS`: `-Xmx384m -Xms128m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication`
   - *(Optional)* `SPOTIFY_CLIENT_ID`: `<your_spotify_client_id>`
   - *(Optional)* `SPOTIFY_CLIENT_SECRET`: `<your_spotify_client_secret>`
6. Click **Create Web Service**.

---

## Verifying Deployment Logs

While Render builds and deploys your container, watch the **Logs** tab in Render:

1. **Docker Build**:
   ```
   Step 1/10 : FROM ghcr.io/lavalink-devs/lavalink:4-alpine
   Step 2/10 : USER root
   Step 3/10 : RUN apk add --no-cache curl bash ca-certificates
   ...
   Successfully tagged service:latest
   ```

2. **Server Boot**:
   ```
   ==================================================
    Starting Kyoka Lavalink V4 Server
   --------------------------------------------------
    Target Port       : 10000
    Host Address      : 0.0.0.0
    Memory Settings   : -Xmx384m ...
    Authentication    : Configured (Secure Password Set)
   ==================================================
   ```

3. **Plugin Auto-Download**:
   ```
   Loading plugins from /opt/Lavalink/plugins
   Downloading dev.lavalink.youtube:youtube-plugin:1.18.2...
   Downloading com.github.topi314.lavasrc:lavasrc-plugin:4.8.3...
   Loaded plugin YouTube-Plugin v1.18.2
   Loaded plugin LavaSrc v4.8.3
   ```

4. **Health Check Passed**:
   ```
   Lavalink is ready to accept connections.
   Health check on /version succeeded. Service is live.
   ```

Your public URL will be:
`https://<your-service-name>.onrender.com`
