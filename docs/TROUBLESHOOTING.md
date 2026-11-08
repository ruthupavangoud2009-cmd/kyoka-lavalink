# Troubleshooting & Diagnostics Guide

This guide covers common issues, error codes, and solutions for **Kyoka Lavalink V4** on Render Free.

---

## 1. Quick Diagnostic Checklist

Run these diagnostic commands from your terminal to identify issues immediately:

```bash
# 1. Test unauthenticated /version endpoint
python scripts/health_check.py --url https://<service-name>.onrender.com

# 2. Test authenticated REST endpoint & loaded plugins
python scripts/health_check.py --url https://<service-name>.onrender.com --password <password>

# 3. Test WebSocket handshake
python scripts/test_websocket.py --url https://<service-name>.onrender.com --password <password>

# 4. Test audio track resolution
python scripts/test_rest.py --url https://<service-name>.onrender.com --password <password>
```

---

## 2. Common Errors and Solutions

### Issue A: 401 Unauthorized on REST API or WebSocket (Code 4001)
- **Symptom**: Health check fails at step 2, or bot logs `wavelink.exceptions.AuthorizationFailedException`.
- **Cause**: The password sent by Kyoka does not match `LAVALINK_SERVER_PASSWORD` set in Render.
- **Solution**:
  1. Open Render Dashboard -> `kyoka-lavalink` service -> **Environment**.
  2. Copy the exact value of `LAVALINK_SERVER_PASSWORD`.
  3. In your Kyoka bot config, set `LAVALINK_PASSWORD` to that exact value.
  4. Ensure there are no accidental spaces or newline characters.

---

### Issue B: 502 Bad Gateway or Cold Start Timeout
- **Symptom**: `curl https://<service-name>.onrender.com/version` returns `502 Bad Gateway` or times out.
- **Cause**: Render Free puts instances to sleep after 15 minutes of inactivity. When a request arrives, the JVM takes 30-50s to boot and download plugins.
- **Solution**:
  1. Wait 45 seconds and re-test.
  2. Set up a 24/7 keep-alive ping via [24_7_KEEPALIVE.md](24_7_KEEPALIVE.md) to prevent the service from ever sleeping.

---

### Issue C: Container Crashes with Exit Code 137 (OOMKilled)
- **Symptom**: Render logs show `Container killed by Out-of-Memory (OOM) killer`.
- **Cause**: The Java Virtual Machine exceeded Render's 512 MB hard container RAM limit.
- **Solution**:
  Verify your `JAVA_OPTS` setting in Render Environment:
  ```
  -Xmx384m -Xms128m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication
  ```
  Setting `-Xmx384m` ensures JVM heap stays well below 384 MB, leaving ~128 MB for native OS libraries and Temurin runtime.

---

### Issue D: YouTube "Sign in to confirm you're not a bot" or 429
- **Symptom**: YouTube tracks fail to resolve, but SoundCloud and HTTP tracks work fine.
- **Cause**: YouTube periodically blocks datacenter IP ranges (including cloud providers like Render, AWS, and DigitalOcean).
- **Solution**:
  1. In `application.yml`, the plugin cascade order is pre-configured with `MUSIC` and `WEBEMBEDDED` clients to bypass basic datacenter blocks.
  2. If persistent, you can provide a YouTube OAuth token or PO token in `application.yml` under `plugins.youtube.oauth`.

---

### Issue E: Port Binding or 0.0.0.0 Mismatch
- **Symptom**: Render logs show `Port scan timeout` or `Application did not bind to PORT within 15 minutes`.
- **Cause**: The application listened on `127.0.0.1` or a static port instead of the dynamic `$PORT` injected by Render.
- **Solution**:
  - `application.yml` uses `port: ${PORT:2333}` and `address: 0.0.0.0`.
  - `entrypoint.sh` automatically reads `$PORT` and passes `-Dserver.port="${PORT}" -Dserver.address="0.0.0.0"`.

---

### Issue F: Spotify Playlists Fail to Load
- **Symptom**: Spotify track URLs return `404` or `Empty`.
- **Cause**: LavaSrc requires valid Spotify API credentials to fetch track metadata from the Spotify Web API.
- **Solution**:
  1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
  2. Create a free App.
  3. Copy your **Client ID** and **Client Secret**.
  4. Add them to Render Environment variables as `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
