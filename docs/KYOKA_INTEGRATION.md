# Kyoka 3.0 (Aizen Bot) Integration Guide

This guide details how to connect the **Kyoka 3.0 Discord Bot** ([ruthupavangoud2009-cmd/aizen-bot](https://github.com/ruthupavangoud2009-cmd/aizen-bot)) to your dedicated Render Lavalink V4 node.

---

## 1. Connection Architecture

Kyoka uses **Wavelink 3.5.2+** to manage audio connections to Lavalink V4.

```
+--------------------------------------------------------+
|           Kyoka Discord Bot (aizen-bot)                |
|           wavelink 3.5.2+ / Python 3.11                |
+--------------------------------------------------------+
                           |
        WSS / HTTPS (TLS Encrypted, Port 443)
                           |
                           v
+--------------------------------------------------------+
|       Render Free Web Service (Docker Runtime)         |
|             https://<service-name>.onrender.com        |
|                                                        |
|  +--------------------------------------------------+  |
|  |  Lavalink V4 Container (Port 10000 -> 443 proxy) |  |
|  |  - YouTube Plugin (dev.lavalink.youtube)         |  |
|  |  - LavaSrc Plugin (Spotify Resolution)           |  |
|  |  - Soundcloud, Bandcamp, Twitch, Direct HTTP     |  |
|  +--------------------------------------------------+  |
+--------------------------------------------------------+
```

---

## 2. Exact Environment Variables for Kyoka

Add these exact environment variables to your Kyoka bot's configuration:

### Configuration Values:

| Variable Name | Recommended Value | Notes |
| :--- | :--- | :--- |
| `LAVALINK_HOST` | `your-service-name.onrender.com` | **Domain only**. Do NOT include `https://` or trailing slashes. |
| `LAVALINK_PORT` | `443` | Render external HTTPS / WSS port is always `443`. |
| `LAVALINK_PASSWORD` | `<your_secure_password>` | Must match `LAVALINK_SERVER_PASSWORD` configured on Render. |
| `LAVALINK_SECURE` | `true` | Enables TLS (`https://` and `wss://`). |
| `LAVALINK_IDENTIFIER` | `kyoka-lavalink-v4` | Friendly node name in Kyoka's node pool. |
| `LAVALINK_AUTO_DISCOVER` | `false` | Disables fallback to unreliable public Lavalink nodes. |

---

## 3. Where to Set These Variables

### Case A: When Kyoka is Deployed on Render
1. Open the [Render Dashboard](https://dashboard.render.com).
2. Click on your **Kyoka Bot** service (e.g., `aizen-bot` / `kyoka-bot`).
3. Click the **Environment** tab on the left menu.
4. Add or update the variables:
   ```env
   LAVALINK_HOST=kyoka-lavalink.onrender.com
   LAVALINK_PORT=443
   LAVALINK_PASSWORD=your_actual_password_here
   LAVALINK_SECURE=true
   LAVALINK_IDENTIFIER=kyoka-lavalink-v4
   LAVALINK_AUTO_DISCOVER=false
   ```
5. Click **Save Changes**. Render will automatically redeploy Kyoka with the new settings.

### Case B: When Kyoka is Running Locally or on a VPS
Open the `.env` file in the root of your `aizen-bot` directory and append:

```env
LAVALINK_HOST=kyoka-lavalink.onrender.com
LAVALINK_PORT=443
LAVALINK_PASSWORD=your_actual_password_here
LAVALINK_SECURE=true
LAVALINK_IDENTIFIER=kyoka-lavalink-v4
LAVALINK_AUTO_DISCOVER=false
```

---

## 4. How Kyoka Connects Internally

In `src/core/config.py`:
```python
if LAVALINK_HOST:
    _scheme = "https" if LAVALINK_SECURE else "http"
    LAVALINK_URI = f"{_scheme}://{LAVALINK_HOST}:{LAVALINK_PORT}"
```
When `LAVALINK_HOST=kyoka-lavalink.onrender.com`, `LAVALINK_PORT=443`, and `LAVALINK_SECURE=true`, Kyoka automatically evaluates `LAVALINK_URI` to:
```
https://kyoka-lavalink.onrender.com:443
```
And connects via secure WebSocket:
```
wss://kyoka-lavalink.onrender.com:443/v4/websocket
```

In `src/core/lavalink.py`:
Kyoka applies a strict 10-second timeout on WebSocket handshakes and 12-second HTTP timeouts to prevent command lag.

---

## 5. Verification Command

From your computer, verify that Kyoka can connect using the built-in diagnostic tools:

```bash
# Test WebSocket Handshake
python scripts/test_websocket.py --url https://kyoka-lavalink.onrender.com --password your_password

# Test Track Search Resolution
python scripts/test_rest.py --url https://kyoka-lavalink.onrender.com --password your_password
```

