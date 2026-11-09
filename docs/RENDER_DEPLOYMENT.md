# Render Free Deployment Guide

This guide provides step-by-step instructions for deploying **Kyoka Lavalink V4** with the **Nginx Edge Gateway** on Render's **Free Tier** ($0/month) with zero unexpected charges.

---

## Architecture Summary

- **Layer 1 (Public Edge)**: Nginx listens on Render's dynamic `$PORT` (mapped to port 443 externally).
  - `GET /`: Serves static HTML homepage (`200 OK`, no auth).
  - `GET /healthz`: Public health check verifying backend readiness (`200 OK` when backend up, `502` when down).
  - `GET /favicon.ico`: Returns `204 No Content`.
  - All unknown routes dropped locally with `404 Not Found`.
- **Layer 2 (Internal Backend)**: Lavalink V4.2.2 bound to `127.0.0.1:2333` (loopback only).
  - Strictly protected by `LAVALINK_SERVER_PASSWORD`.
  - Forwarded routes: `/v4/*` and `/v4/websocket`.
- **Memory Footprint**: Capped conservatively with `-Xmx256m -Xms96m` to leave ample headroom on Render Free's 512 MB ceiling.

---

## Method 1: Blueprint Deployment (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Select your repository: `ruthupavangoud2009-cmd/kyoka-lavalink`.
4. Render detects [`render.yaml`](../render.yaml) automatically:
   - **Service Name**: `kyoka-lavalink`
   - **Plan**: `Free` ($0.00/mo)
   - **Runtime**: `Docker`
   - **Health Check Path**: `/healthz`
   - **LAVALINK_SERVER_PASSWORD**: Automatically generated secure secret
5. Click **Apply**.

---

## Method 2: Manual Web Service Setup

If setting up manually:

1. Click **New +** -> **Web Service**.
2. Connect `ruthupavangoud2009-cmd/kyoka-lavalink`.
3. Set the following:
   - **Name**: `kyoka-lavalink`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: **Free** ($0/month)
4. Under **Advanced**:
   - **Health Check Path**: `/healthz`
   - **Auto-Deploy**: `Yes`
5. Under **Environment Variables**:
   - `LAVALINK_SERVER_PASSWORD`: `<your-secure-random-password>`
   - `JAVA_OPTS`: `-Xmx256m -Xms96m -XX:MaxMetaspaceSize=72m -XX:ReservedCodeCacheSize=48m -XX:MaxDirectMemorySize=32m -Xss384k -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication`
   - *(Optional)* `SPOTIFY_CLIENT_ID`: `<your_spotify_client_id>`
   - *(Optional)* `SPOTIFY_CLIENT_SECRET`: `<your_spotify_client_secret>`
6. Click **Create Web Service**.

---

## Verification Commands

After deployment finishes:

```bash
# 1. Verify Public Homepage
curl -s -i "https://kyoka-lavalink.onrender.com/" | head -n 5

# 2. Verify Backend Health
curl -s -i "https://kyoka-lavalink.onrender.com/healthz"

# 3. Verify Favicon Handling
curl -s -i "https://kyoka-lavalink.onrender.com/favicon.ico"

# 4. Verify Unknown Route Drop
curl -s -i "https://kyoka-lavalink.onrender.com/unknown-route"

# 5. Verify Unauthenticated REST Block
curl -s -i "https://kyoka-lavalink.onrender.com/v4/info"
```
