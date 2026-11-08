# Kyoka Lavalink V4 Server

Production-ready, highly optimized **Lavalink V4** audio node engineered for **Kyoka 3.0 Discord Bot** ([ruthupavangoud2009-cmd/aizen-bot](https://github.com/ruthupavangoud2009-cmd/aizen-bot)) and deployed on **Render Free Web Service** ($0/month).

[![Configuration Validation](https://img.shields.io/badge/Config-Validated-brightgreen.svg)](workflows/validate.yml)
[![24/7 Keep-Alive](https://img.shields.io/badge/Keep--Alive-Supported-blue.svg)](workflows/keepalive.yml)
[![Lavalink Version](https://img.shields.io/badge/Lavalink-v4.x-blue.svg)](https://github.com/lavalink-devs/Lavalink)
[![Render Free](https://img.shields.io/badge/Render-Free%20Tier-success.svg)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Architecture Overview

```
                          Internet / Discord Audio Requests
                                          |
                                          v
                      +---------------------------------------+
                      |         Kyoka 3.0 Discord Bot         |
                      |  wavelink 3.5.2+ | Python 3.11        |
                      +---------------------------------------+
                                          |
                               WSS / HTTPS (TLS: 443)
                                          |
                                          v
               +-----------------------------------------------------+
               |         Render Cloud Platform (Free Tier)           |
               |                                                     |
               |  URL: https://<service-name>.onrender.com           |
               |  Dynamic Ingress -> Container Port $PORT (0.0.0.0)  |
               |                                                     |
               |  +-----------------------------------------------+  |
               |  |  Official Docker Container                    |  |
               |  |  Image: ghcr.io/lavalink-devs/lavalink:4-alpine|  |
               |  |  JVM: Temurin OpenJDK 21 (-Xmx384m G1GC)      |  |
               |  |                                               |  |
               |  |  +-------------------+  +-------------------+ |  |
               |  |  |  YouTube Plugin   |  |   LavaSrc Plugin  | |  |
               |  |  |  (v1.18.2)        |  |   (v4.8.3)        | |  |
               |  |  +-------------------+  +-------------------+ |  |
               |  |  |  SoundCloud / HTTP Radio / Direct Audio  | |  |
               |  |  +------------------------------------------+ |  |
               |  +-----------------------------------------------+  |
               +-----------------------------------------------------+
                                          ^
                                          | Every 10 mins
                                          |
               +-----------------------------------------------------+
               |             24/7 Keep-Alive Worker                  |
               |    Cron-job.org / GitHub Actions / scripts/keepalive|
               |         Pings: GET /version (HTTP 200)              |
               +-----------------------------------------------------+
```

---

## Key Features

- **Official V4 Base Image**: Built directly on `ghcr.io/lavalink-devs/lavalink:4-alpine`.
- **Render Free Tier Optimized**: Pre-configured JVM heap limit (`-Xmx384m`) with G1GC and string deduplication, ensuring memory usage stays safely below Render's 512 MB RAM ceiling to prevent `OOMKilled (exit 137)`.
- **Dynamic Port Routing**: Automatically adapts to Render's injected `$PORT` environment variable and binds to `0.0.0.0`.
- **Full Plugin Support**:
  - **YouTube & YouTube Music**: Powered by `dev.lavalink.youtube:youtube-plugin:1.18.2` with multi-client fallback cascade (`MUSIC`, `WEB`, `ANDROID_VR`, `WEBEMBEDDED`).
  - **Spotify Resolution**: Powered by `com.github.topi314.lavasrc:lavasrc-plugin:4.8.3` using legitimate ISRC matching and search mirroring to audio streams.
  - **Native Sources**: SoundCloud, Bandcamp, Twitch, Vimeo, and Direct HTTP streams / Internet Radio.
- **24/7 Uptime Strategy**: Free Render services sleep after 15 minutes of inactivity. Complete solutions provided to keep the service warm 24/7 within Render's free 750 monthly instance hours.
- **Zero Hardcoded Secrets**: Fully environment-variable driven with random password generator and safe placeholders.
- **Pre-flight & Health Diagnostics**: Rich suite of CLI verification tools for unauthenticated health probing, authenticated REST info, and WebSocket handshake testing.

---

## 1. Quick Deploy on Render Free ($0/month)

### Method A: One-Click Blueprint Deployment (Recommended)

1. Fork or push this repository to your GitHub account: `ruthupavangoud2009-cmd/kyoka-lavalink`.
2. Go to the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Select `kyoka-lavalink`.
5. Render detects [`render.yaml`](render.yaml) automatically:
   - **Service Name**: `kyoka-lavalink`
   - **Plan**: `Free`
   - **Runtime**: `Docker`
   - **Healthcheck**: Managed natively via Render TCP Port Readiness (prevents 401 unauthenticated probe warnings)
6. Click **Apply**. Render will generate a secure `LAVALINK_SERVER_PASSWORD` and deploy the service.

### Method B: Manual Web Service Setup

See detailed instructions in [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md).

---

## 2. 24/7 Uptime on Render Free

Render Free Web Services spin down after 15 minutes of inactivity. Render grants **750 free instance hours per month** ($31 \text{ days} \times 24 \text{ hrs} = 744 \text{ hrs}$), so **one single free service can run 24/7 without exceeding your quota!**

To keep it awake 24/7:
1. Ping `https://<your-service>.onrender.com/version` every **10 minutes**.
2. **Options**:
   - Set up a free monitor at [Cron-job.org](https://cron-job.org) or [UptimeRobot](https://uptimerobot.com).
   - Or configure the included GitHub Actions cron workflow [`workflows/keepalive.yml`](workflows/keepalive.yml) (copy to `.github/workflows/` via GitHub Web UI or PAT with `workflow` scope).
   - Or run `./scripts/keepalive.sh` / `python scripts/keepalive.py`.

Full step-by-step instructions: [docs/24_7_KEEPALIVE.md](docs/24_7_KEEPALIVE.md).

---

## 3. Kyoka 3.0 Discord Bot Integration

Configure these exact environment variables in your Kyoka bot repository ([aizen-bot](https://github.com/ruthupavangoud2009-cmd/aizen-bot)):

```env
LAVALINK_HOST=your-service-name.onrender.com
LAVALINK_PORT=443
LAVALINK_PASSWORD=your_actual_password_from_render
LAVALINK_SECURE=true
LAVALINK_IDENTIFIER=kyoka-lavalink-v4
LAVALINK_AUTO_DISCOVER=false
```

Full details on where to paste these variables in Render or `.env`: [docs/KYOKA_INTEGRATION.md](docs/KYOKA_INTEGRATION.md).

---

## 4. Local Testing & Verification Suite

All scripts are written in pure Python 3 standard library (no pip installs needed):

```bash
# 1. Validate all repository files & configuration settings
python scripts/validate_config.py

# 2. Generate a secure 256-bit random password
python scripts/generate_password.py

# 3. Test unauthenticated & authenticated health endpoints
python scripts/health_check.py --url https://<service-name>.onrender.com --password <password>

# 4. Test WebSocket protocol handshake & receive ready event
python scripts/test_websocket.py --url https://<service-name>.onrender.com --password <password>

# 5. Test audio track resolution across YouTube, SoundCloud, and HTTP
python scripts/test_rest.py --url https://<service-name>.onrender.com --password <password>

# 6. Run keepalive ping loop
python scripts/keepalive.py --url https://<service-name>.onrender.com --interval 540
```

---

## 5. Repository File Structure

```
kyoka-lavalink/
├── workflows/
│   ├── validate.yml          # CI config validation workflow
│   └── keepalive.yml         # 24/7 scheduled keepalive workflow
├── docs/
│   ├── KYOKA_INTEGRATION.md      # Kyoka 3.0 connection instructions
│   ├── RENDER_DEPLOYMENT.md      # Render free deployment walkthrough
│   ├── 24_7_KEEPALIVE.md         # 24/7 uptime & idle sleep prevention
│   └── TROUBLESHOOTING.md        # Error codes, OOM, and solutions
├── scripts/
│   ├── generate_password.py      # Secure token generator
│   ├── validate_config.py        # Pre-flight YAML & file validator
│   ├── health_check.py           # REST & metrics diagnostic tool
│   ├── test_websocket.py         # WebSocket protocol tester
│   ├── test_rest.py              # Track resolution tester
│   ├── keepalive.py              # 24/7 keep-alive daemon (Python)
│   ├── health-check.sh           # Bash health check wrapper
│   ├── keepalive.sh              # Bash keep-alive wrapper
│   ├── validate-config.sh        # Bash validation wrapper
│   ├── health-check.ps1          # PowerShell health check wrapper
│   └── keepalive.ps1             # PowerShell keep-alive wrapper
├── .dockerignore                 # Excludes docs/scripts from Docker build
├── .env.example                  # Environment variable reference
├── .gitignore                    # Prevents committing secrets & caches
├── application.yml               # Lavalink V4 & plugin configuration
├── Dockerfile                    # Container build file (4-alpine)
├── entrypoint.sh                 # Container entrypoint with signal traps
├── render.yaml                   # Render Free Web Service Blueprint
└── README.md                     # Project documentation
```

---

## 6. License & Credits

- Base container: [Lavalink](https://github.com/lavalink-devs/Lavalink) by `lavalink-devs`
- YouTube Plugin: [youtube-plugin](https://github.com/lavalink-devs/youtube-source) by `lavalink-devs`
- Spotify Plugin: [LavaSrc](https://github.com/topi314/LavaSrc) by `topi314`
- Discord Bot: [Kyoka 3.0](https://github.com/ruthupavangoud2009-cmd/aizen-bot)
- License: MIT
