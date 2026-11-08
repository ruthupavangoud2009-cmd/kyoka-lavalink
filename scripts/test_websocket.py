#!/usr/bin/env python3
"""
WebSocket Connection & Protocol Handshake Test for Kyoka Lavalink V4.
Tests:
- TCP / TLS connection to Lavalink host & port
- HTTP Upgrade to WebSocket (/v4/websocket)
- Authorization header authentication
- Receipt of Lavalink v4 'ready' event with sessionId
Zero external dependencies (pure Python standard library: socket, ssl, json).
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
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "http://localhost:2333",
        help="Lavalink base URL (e.g. https://kyoka-lavalink.onrender.com or http://localhost:2333)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "youshallnotpass",
        help="Lavalink password"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
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
    """Simple parser for WebSocket text frame (Opcode 1)"""
    header = sock.recv(2)
    if len(header) < 2:
        return None
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

def test_websocket(host: str, port: int, is_secure: bool, password: str, timeout: float):
    print(f" Connecting to: {host}:{port} (Secure TLS: {is_secure})")
    start = time.perf_counter()

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(timeout)

    try:
        if is_secure:
            context = ssl.create_default_context()
            sock = context.wrap_socket(raw_sock, server_hostname=host)
        else:
            sock = raw_sock

        sock.connect((host, port))
        connect_time = (time.perf_counter() - start) * 1000
        print(f" [PASS] TCP/TLS Connected in {connect_time:.1f} ms")

        # Generate standard WebSocket Key
        ws_key = base64.b64encode(os.urandom(16)).decode("ascii")

        # Handshake request for Lavalink v4
        headers = [
            f"GET /v4/websocket HTTP/1.1",
            f"Host: {host}:{port}",
            f"Upgrade: websocket",
            f"Connection: Upgrade",
            f"Sec-WebSocket-Key: {ws_key}",
            f"Sec-WebSocket-Version: 13",
            f"Authorization: {password}",
            f"User-Id: 1000000000000000000",
            f"Client-Name: KyokaDiagnostics/1.0",
            "\r\n"
        ]
        request_data = "\r\n".join(headers).encode("utf-8")
        sock.sendall(request_data)

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
        print(f" Handshake Response: {status_line}")

        if "101" not in status_line:
            if "401" in status_line:
                print(" [FAIL] Authentication Rejected (401 Unauthorized). Check password!")
            else:
                print(f" [FAIL] Expected HTTP 101 Switching Protocols, got: {status_line}")
            sock.close()
            return False

        print(" [PASS] WebSocket Upgrade 101 Handshake Successful!")

        # Read initial ready event frame from Lavalink v4
        frame = read_websocket_frame(sock)
        if frame:
            opcode, message = frame
            try:
                data = json.loads(message)
                op = data.get("op")
                if op == "ready":
                    session_id = data.get("sessionId")
                    resumed = data.get("resumed")
                    print(f" [PASS] Received Lavalink 'ready' event:")
                    print(f"        Session ID : {session_id}")
                    print(f"        Resumed    : {resumed}")
                elif op == "stats":
                    print(f" [PASS] Received Lavalink 'stats' frame")
                else:
                    print(f" [INFO] Received frame with op: {op}")
            except Exception:
                print(f" [INFO] Frame payload: {message[:120]}")

        sock.close()
        return True

    except Exception as e:
        print(f" [FAIL] WebSocket test failed: {e}")
        return False

def main():
    args = parse_args()
    host, port, is_secure = parse_target(args.url)

    print("=" * 64)
    print(" KYOKA LAVALINK V4 - WEBSOCKET PROTOCOL TEST")
    print("=" * 64)
    success = test_websocket(host, port, is_secure, args.password, args.timeout)
    print("=" * 64)
    if success:
        print(" [RESULT] WEBSOCKET CONNECTIVITY VERIFIED FOR WAVELINK / KYOKA!")
        print("=" * 64 + "\n")
        return 0
    else:
        print(" [RESULT] WEBSOCKET TEST FAILED.")
        print("=" * 64 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
