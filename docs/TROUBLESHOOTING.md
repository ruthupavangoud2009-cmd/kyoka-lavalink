# Troubleshooting & Diagnostics Guide

This guide covers common questions, error codes, and diagnostics for **Kyoka Lavalink V4**.

---

## 1. Quick Diagnostic Checklist

```bash
# Full test suite covering homepage, favicon, healthz, 401/403 security, and authenticated API:
python scripts/health_check.py --url https://kyoka-lavalink.onrender.com --password <YOUR_PASSWORD>

# WebSocket protocol handshake and ready event:
python scripts/test_websocket.py --url https://kyoka-lavalink.onrender.com --password <YOUR_PASSWORD>

# Audio search resolution across YouTube, SoundCloud, and Spotify:
python scripts/test_rest.py --url https://kyoka-lavalink.onrender.com --password <YOUR_PASSWORD>
```

---

## 2. Common Issues and Resolutions

### Issue A: `/healthz` returns 502 Bad Gateway
- **Cause**: Nginx is running, but the internal Lavalink backend on `127.0.0.1:2333` has not finished booting or has crashed.
- **Solution**:
  1. If the container was just deployed, wait 30–50 seconds for Temurin JVM and plugins (YouTube, LavaSrc) to finish initialization.
  2. Inspect container logs to verify `LAVALINK_SERVER_PASSWORD` is configured in Render Environment.

### Issue B: 401 Unauthorized or 403 Forbidden
- **Cause**: The client did not provide the matching password.
  - `401 Unauthorized`: Request sent without an `Authorization` header.
  - `403 Forbidden`: Request sent with an incorrect password.
- **Solution**:
  1. Open Render Dashboard -> `kyoka-lavalink` -> Environment.
  2. Copy the exact `LAVALINK_SERVER_PASSWORD`.
  3. Update `LAVALINK_PASSWORD` in your Kyoka bot's environment variables.

### Issue C: Unknown Routes Return 404 Not Found
- **Cause**: Nginx dropped an unmapped route locally (`location / { return 404; }`).
- **Explanation**: This is intentional. Random internet bots scanning for WordPress, PHP, or admin panels are immediately stopped by Nginx so they never hit Java or pollute your server logs.

### Issue D: OOMKilled (Exit Code 137)
- **Cause**: Physical memory exceeded Render Free's 512 MB hard ceiling.
- **Solution**:
  Verify your `JAVA_OPTS` matches the conservative sizing:
  ```
  -Xmx256m -Xms96m -XX:MaxMetaspaceSize=72m -XX:ReservedCodeCacheSize=48m -XX:MaxDirectMemorySize=32m -Xss384k -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:+ExitOnOutOfMemoryError -XX:+UseStringDeduplication
  ```
