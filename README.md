# Kyoka Lavalink V4 Audio Node

Production-ready, dual-layer **Lavalink V4** audio node engineered for **Kyoka 3.0 Discord Bot** ([ruthupavangoud2009-cmd/aizen-bot](https://github.com/ruthupavangoud2009-cmd/aizen-bot)) and deployed on **Render Free Web Service** ($0/month).

[![Lavalink Version](https://img.shields.io/badge/Lavalink-v4.2.2-blue.svg)](https://github.com/lavalink-devs/Lavalink)
[![Architecture](https://img.shields.io/badge/Architecture-Nginx%20Edge%20Gateway-brightgreen.svg)](nginx.conf.template)
[![Render Free](https://img.shields.io/badge/Render-Free%20Tier-success.svg)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Architecture Overview

```
                               Incoming Public Traffic (Port 443)
                                               │
                                               ▼
                              ┌─────────────────────────────────┐
                              │     Render Free Web Service     │
                              │     Dynamic Port $PORT          │
                              └────────────────┬────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Single Docker Container (Alpine Linux)                                                     │
│                                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Edge Gateway (Nginx) — Listens on 0.0.0.0:$PORT                              │  │
│  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
│  │ 1. GET /              ──► Serves static HTML homepage (200 OK, public, no auth)       │  │
│  │ 2. GET /favicon.ico   ──► Returns HTTP 204 No Content immediately                     │  │
│  │ 3. GET /healthz       ──► Probes Lavalink backend directly (200 if up, 502 if down)   │  │
│  │ 4. GET /v4/websocket  ──► Proxies WS with Upgrade headers to 127.0.0.1:2333           │  │
│  │ 5. ALL /v4/* (REST)   ──► Proxies REST calls with Auth headers to 127.0.0.1:2333      │  │
│  │ 6. ALL other routes   ──► REJECTED LOCALLY by Nginx with HTTP 404 (never hits Java)  │  │
│  └───────────────────────────────────┬───────────────────────────────────────────────────┘  │
│                                      │ Internal Loopback ONLY (127.0.0.1:2333)              │
│                                      ▼                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Layer 2: Lavalink V4.2.2 Engine — Bound strictly to 127.0.0.1:2333                    │  │
│  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
│  │ - Unexposed to public internet (isolated behind localhost)                            │  │
│  │ - 100% strict password authentication enforced on /v4/* and /v4/websocket             │  │
│  │ - YouTube Plugin 1.18.2 & LavaSrc Plugin 4.8.3 loaded and active                      │  │
│  │ - Zero 'Authorization missing' log spam from crawlers, health checks, or browser hits │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Nginx Edge Gateway**: Runs inside the same container (<3 MB RAM footprint) to separate public status requests from private audio routes.
- **Public Homepage**: Visiting `https://kyoka-lavalink.onrender.com/` in a browser displays a clean, dark-mode status card with `HTTP 200 OK` (no authentication required).
- **Public Backend Health Check (`/healthz`)**: Verifies that the internal Lavalink backend is responding without exposing raw metrics or requiring authentication headers.
- **Favicon Handling**: `GET /favicon.ico` returns `HTTP 204 No Content` directly from Nginx.
- **Local 404 Rejection**: Unknown probe paths are dropped immediately by Nginx, preventing random internet crawlers from touching Java or cluttering logs.
- **Protected Audio Streaming**: 100% of audio routes (`/v4/websocket`, `/v4/loadtracks`, `/v4/sessions/*`) strictly require `LAVALINK_SERVER_PASSWORD`.
- **Zero Insecure Defaults**: Lavalink refuses to start if `LAVALINK_SERVER_PASSWORD` is missing or empty. No hardcoded default passwords.
- **Reliable Dual-Process Supervisor**: `entrypoint.sh` supervises both Nginx and Lavalink using zombie-safe process state inspection. If either process dies, it cleanly terminates the surviving child, reaps both, and exits with code 1 so Render can restart the container.
- **Conservative Memory Sizing**: Pre-configured with `-Xmx256m` and reduced thread stacks (`-Xss384k`) to maintain safe operating margins on Render Free's 512 MB ceiling.
- **Full Plugin Support**:
  - **YouTube & YouTube Music**: `dev.lavalink.youtube:youtube-plugin:1.18.2`
  - **Spotify Resolution**: `com.github.topi314.lavasrc:lavasrc-plugin:4.8.3`
  - **Native Sources**: SoundCloud, Direct HTTP Audio, Internet Radio Streams, Bandcamp, Twitch.

---

## Quick Deploy on Render Free ($0/month)

1. Fork or push this repository to your GitHub account: `ruthupavangoud2009-cmd/kyoka-lavalink`.
2. Open [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Select `kyoka-lavalink`. Render automatically parses [`render.yaml`](render.yaml):
   - **Plan**: `Free` ($0/mo)
   - **Runtime**: `Docker`
   - **Health Check Path**: `/healthz`
5. Click **Apply**.

---

## Kyoka 3.0 (`aizen-bot`) Connection Settings

In your Kyoka Discord bot environment (Render Environment or `.env` file):

```env
LAVALINK_HOST=kyoka-lavalink.onrender.com
LAVALINK_PORT=443
LAVALINK_PASSWORD=YOUR_ACTUAL_RENDER_PASSWORD
LAVALINK_SECURE=true
LAVALINK_IDENTIFIER=kyoka-lavalink-v4
LAVALINK_AUTO_DISCOVER=false
```

---

## Verification Test Suite

```bash
# 1. Verify Public Homepage (HTTP 200 OK)
curl -s -i "https://kyoka-lavalink.onrender.com/" | head -n 5

# 2. Verify Favicon Handling (HTTP 204 No Content)
curl -s -i "https://kyoka-lavalink.onrender.com/favicon.ico" | head -n 1

# 3. Verify Public Backend Health Check (HTTP 200 OK)
curl -s -i "https://kyoka-lavalink.onrender.com/healthz"

# 4. Verify Unknown Route Drop (HTTP 404 Not Found)
curl -s -i "https://kyoka-lavalink.onrender.com/unknown-route"

# 5. Verify Unauthenticated REST Block (HTTP 401 Unauthorized)
curl -s -i "https://kyoka-lavalink.onrender.com/v4/info" | head -n 1

# 6. Verify Invalid Password Rejection (HTTP 403 Forbidden)
curl -s -i -H "Authorization: wrong_pw" "https://kyoka-lavalink.onrender.com/v4/info" | head -n 1

# 7. Authenticated REST & Plugin Verification
python scripts/health_check.py --url https://kyoka-lavalink.onrender.com --password <PASSWORD>

# 8. Authenticated WebSocket 101 Handshake & Ready Event
python scripts/test_websocket.py --url https://kyoka-lavalink.onrender.com --password <PASSWORD>

# 9. Track Resolution Test (YouTube, SoundCloud, Spotify)
python scripts/test_rest.py --url https://kyoka-lavalink.onrender.com --password <PASSWORD>
```

---

## License

MIT License - Copyright (c) 2026 ruthupavangoud2009-cmd
