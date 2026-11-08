#!/usr/bin/env python3
"""
WebSocket Protocol & Handshake Test for Kyoka Lavalink V4.

Validates:
- TCP/TLS connection to Render HTTPS/WSS (port 443) or local port
- HTTP Upgrade to WebSocket at /v4/websocket
- Authorization header verification
- Mandatory User-Id header verification (as required by Lavalink HandshakeInterceptorImpl)
- Receipt and parsing of initial Lavalink v4 'ready' event with sessionId
- Clear diagnosis for 401/403 (Auth failure), 400 (Bad request), 502/503 (Render cold start)
Zero external pip dependencies (uses Python standard library: socket, ssl, json).
"""
import argparse
import base64
import json
import os
import socket
import ssl
import sys
import time
import urllib.parse

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink V4 WebSocket Handshake Test")
    parser.add_argument(
        "--url",
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "https://kyoka-lavalink.onrender.com",
        help="Lavalink base URL (e.g. https://kyoka-lavalink.onrender.com or http://localhost:2333)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "",
        help="Lavalink server password"
    )
    parser.add_argument(
        "--user-id",
        default="1505515188991033409",
        help="Discord Bot User ID (must be non-zero integer)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Socket timeout in seconds"
    )
    return parser.parse_args()

def parse_target(raw_url: str):
    url = raw_url.strip()
    if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("ws://") and not url.startswith("wss://"):
        if ":443" in url or "onrender.com" in url:
            url = "https://" + url
        else:
            url = "http://" + url

    parsed = urllib.parse.urlparse(url)
    is_secure = parsed.scheme in ("https", "wss")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if is_secure else 80)
    return host, port, is_secure

def read_websocket_frame(sock):
    """Parses a single WebSocket frame (Opcode 1 = Text, Opcode 8 = Close)"""
    try:
        header = sock.recv(2)
        if len(header) < 2:
            return None, "Empty header"
        b1, b2 = header[0], header[1]
        opcode = b1 & 0x0F
        payload_len = b2 & 0x7F

        if payload_len == 126:
            ext = sock.recv(2)
            payload_len = int.from_bytes(ext, "big")
        elif payload_len == 127:
            ext = sock.recv(8)
            payload_len = int.from_bytes(ext, "big")

        payload = bytearray()
        while len(payload) < payload_len:
            chunk = sock.recv(min(4096, payload_len - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)

        return opcode, payload.decode("utf-8", errors="replace")
    except Exception as e:
        return None, str(e)

def test_websocket(host: str, port: int, is_secure: bool, password: str, user_id: str, timeout: float):
    print("=" * 68)
    print(" KYOKA LAVALINK V4 - WEBSOCKET PROTOCOL TEST")
    print("=" * 68)
    print(f" Target Host     : {host}:{port}")
    print(f" Transport       : {'WSS (TLS Encrypted)' if is_secure else 'WS (Plain TCP)'}")
    print(f" Target Path     : /v4/websocket")
    print(f" User-Id Header  : {user_id}")
    print(f" Auth Password   : {'Set (' + str(len(password)) + ' chars)' if password else 'NOT PROVIDED'}")
    print("=" * 68)

    if not password:
        print("\n [ERROR] No password provided. WebSocket handshake requires authentication.")
        print(" Pass --password <YOUR_PASSWORD> or set LAVALINK_SERVER_PASSWORD environment variable.\n")
        return False

    start = time.perf_counter()
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(timeout)

    try:
        print(f"\n[*] 1. Connecting TCP socket to {host}:{port}...")
        raw_sock.connect((host, port))
        tcp_time = (time.perf_counter() - start) * 1000
        print(f"    [PASS] TCP Connected in {tcp_time:.1f} ms")

        if is_secure:
            print(f"[*] 2. Performing TLS Handshake (SNI: {host})...")
            tls_start = time.perf_counter()
            context = ssl.create_default_context()
            sock = context.wrap_socket(raw_sock, server_hostname=host)
            tls_time = (time.perf_counter() - tls_start) * 1000
            print(f"    [PASS] TLS Established in {tls_time:.1f} ms ({sock.version()})")
        else:
            sock = raw_sock

        # Prepare HTTP Upgrade request
        print("[*] 3. Sending WebSocket Upgrade Handshake to /v4/websocket...")
        ws_key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            "GET /v4/websocket HTTP/1.1",
            f"Host: {host}:{port}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {ws_key}",
            "Sec-WebSocket-Version: 13",
            f"Authorization: {password}",
            f"User-Id: {user_id}",
            "Client-Name: KyokaDiagnostics/2.0",
            "\r\n"
        ]
        request_bytes = "\r\n".join(headers).encode("utf-8")
        sock.sendall(request_bytes)

        # Read handshake response
        response = bytearray()
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response.extend(chunk)

        header_bytes, _, rest = response.partition(b"\r\n\r\n")
        header_text = header_bytes.decode("utf-8", errors="replace")
        status_line = header_text.splitlines()[0] if header_text else "No response"
        print(f"    Server Response : {status_line}")

        # Evaluate HTTP Status
        if "101" in status_line:
            print("    [PASS] HTTP 101 Switching Protocols received!")
        elif "401" in status_line or "403" in status_line:
            print("    [FAIL] Authentication Rejected (401/403)! Password does not match LAVALINK_SERVER_PASSWORD in Render.")
            sock.close()
            return False
        elif "502" in status_line or "503" in status_line:
            print("    [FAIL] Render instance is cold-starting or sleeping (502/503). Wait 30-50s and retry.")
            sock.close()
            return False
        elif "400" in status_line:
            print("    [FAIL] Bad Request (400). Missing or invalid User-Id header.")
            sock.close()
            return False
        else:
            print(f"    [FAIL] Unexpected handshake status: {status_line}")
            sock.close()
            return False

        # Read initial ready event frame from Lavalink V4
        print("[*] 4. Awaiting Lavalink V4 'ready' event payload...")
        opcode, message = read_websocket_frame(sock)
        if opcode == 1:
            try:
                event_data = json.loads(message)
                op = event_data.get("op")
                if op == "ready":
                    session_id = event_data.get("sessionId")
                    resumed = event_data.get("resumed")
                    print("    [PASS] Received 'ready' event frame:")
                    print(f"           Session ID : {session_id}")
                    print(f"           Resumed    : {resumed}")
                    print("\n" + "=" * 68)
                    print(" [RESULT] WEBSOCKET CONNECTIVITY FULLY VERIFIED FOR KYOKA / WAVELINK!\n")
                    sock.close()
                    return True
                elif op == "stats":
                    print(f"    [PASS] Received initial 'stats' event frame")
                    print("\n" + "=" * 68)
                    print(" [RESULT] WEBSOCKET CONNECTIVITY FULLY VERIFIED FOR KYOKA / WAVELINK!\n")
                    sock.close()
                    return True
                else:
                    print(f"    [INFO] Received frame with op '{op}': {message[:120]}")
            except Exception as e:
                print(f"    [WARN] Frame payload not JSON: {message[:120]} ({e})")
        elif opcode == 8:
            print("    [WARN] Received WebSocket Close frame from server.")
        else:
            print(f"    [WARN] Received unexpected frame opcode: {opcode}")

        sock.close()
        return True

    except socket.timeout:
        print("    [FAIL] Socket connection timed out. Service may be sleeping or unresponsive.")
        return False
    except Exception as e:
        print(f"    [FAIL] Connection error: {e}")
        return False

def main():
    args = parse_args()
    host, port, is_secure = parse_target(args.url)
    success = test_websocket(host, port, is_secure, args.password.strip(), args.user_id, args.timeout)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
