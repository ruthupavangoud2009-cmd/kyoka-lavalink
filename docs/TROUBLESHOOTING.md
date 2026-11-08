# Troubleshooting & Diagnostics Guide

This guide covers common issues, error codes, and solutions for **Kyoka Lavalink V4** on Render Free.

---

## 1. Quick Diagnostic Checklist

Run these diagnostic commands from your terminal to identify issues immediately:

```bash
# 1. Test server responsiveness, security, and version
python scripts/health_check.py --url https://<service-name>.onrender.com --password <password>

# 2. Test WebSocket connection & handshake
python scripts/test_websocket.py --url https://<service-name>.onrender.com --password <password>

# 3. Test track search and resolution
python scripts/test_rest.py --url https://<service-name>.onrender.com --password <password>
```

---

## 2. Common Errors and Solutions

### Issue A: "Authorization missing for GET /" or "HEAD /version"
- **Symptom**: Render logs show `Authorization missing for <IP> on GET /` or `HEAD /version`.
- **Cause**:
  1. If caused by Render: Render's health checker was configured with an HTTP path (`/version`). Render does not send authentication headers, so Lavalink correctly returns 401 Unauthorized.
  2. If caused by opening the URL in a browser: When you visit `https://<service-name>.onrender.com` in Google Chrome or Firefox, the browser sends an unauthenticated `GET /` request.
- **Solution**:
  - Remove `healthCheckPath` from `render.yaml` or Render dashboard settings so Render uses its native TCP port check.
  - Understand that browser requests returning 401 are normal and expected: Lavalink is a secure audio API for Discord bots, not an HTML website.

---

### Issue B: "No mapping for GET /favicon.ico"
- **Symptom**: Render logs display `No mapping for GET /favicon.ico` or `No endpoint GET /favicon.ico`.
- **Cause**: When a web browser accesses the URL, it automatically requests the website's favicon icon (`favicon.ico`). Because Lavalink is a backend API and does not have a web icon, Spring Boot logs this informational notice.
- **Solution**:
  - This is completely harmless and does not affect Lavalink, audio streaming, or Kyoka in any way. It can be safely ignored.

---

### Issue C: 401 Unauthorized or 403 Forbidden on REST / WebSocket
- **Symptom**: Health check fails, or bot logs `wavelink.exceptions.AuthorizationFailedException`.
- **Cause**: The password sent by the client does not match `LAVALINK_SERVER_PASSWORD` set in Render.
  - When no password header is sent: Lavalink responds with `401 Unauthorized`.
  - When the wrong password is sent: Lavalink responds with `403 Forbidden`.
- **Solution**:
  1. Open Render Dashboard -> `kyoka-lavalink` service -> **Environment**.
  2. Copy the exact value of `LAVALINK_SERVER_PASSWORD`.
  3. In your Kyoka bot config, set `LAVALINK_PASSWORD` to that exact value.
  4. Ensure there are no accidental spaces or newline characters.

---

### Issue D: 502 Bad Gateway or Cold Start Timeout
- **Symptom**: Connection returns `502 Bad Gateway` or times out.
- **Cause**: Render Free puts instances to sleep after 15 minutes of inactivity. When a request arrives, the JVM takes 30-50s to boot and initialize plugins.
- **Solution**:
  1. Wait 45 seconds and re-test.
  2. Set up a 24/7 keep-alive ping via [24_7_KEEPALIVE.md](24_7_KEEPALIVE.md) to prevent the service from ever sleeping.

---

### Issue E: Container Crashes with Exit Code 137 (OOMKilled)
- **Symptom**: Render logs show `Container killed by Out-of-Memory (OOM) killer`.
- **Cause**: The Java Virtual Machine exceeded Render's 512 MB hard container RAM limit.
- **Solution**:
  Verify your `JAVA_OPTS` setting in Render Environment:
  ```
  -Xmx384m -Xms128m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication
  ```
  Setting `-Xmx384m` ensures JVM heap stays well below 384 MB, leaving ~128 MB for native OS libraries and Temurin runtime.

---

### Issue F: YouTube "Sign in to confirm you're not a bot" or 429
- **Symptom**: YouTube tracks fail to resolve, but SoundCloud and HTTP tracks work fine.
- **Cause**: YouTube periodically blocks datacenter IP ranges (including cloud providers like Render, AWS, and DigitalOcean).
- **Solution**:
  1. In `application.yml`, the plugin cascade order is pre-configured with `MUSIC` and `WEBEMBEDDED` clients to bypass basic datacenter blocks.
  2. If persistent, you can provide a YouTube OAuth token or PO token in `application.yml` under `plugins.youtube.oauth`.

---

### Issue G: Spotify Playlists Fail to Load
- **Symptom**: Spotify track URLs return `404` or `Empty`.
- **Cause**: LavaSrc requires valid Spotify API credentials to fetch track metadata from the Spotify Web API before resolving to audio streams.
- **Solution**:
  1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
  2. Create a free App.
  3. Copy your **Client ID** and **Client Secret**.
  4. Add them to Render Environment variables as `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
