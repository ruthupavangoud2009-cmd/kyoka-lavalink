#!/usr/bin/env python3
"""
24/7 Keep-Alive Worker for Kyoka Lavalink on Render Free.

Pings /healthz periodically to reset Render's 15-minute inactivity idle timer.
Validates that the Nginx edge gateway and the Lavalink backend are healthy,
producing zero 'Authorization missing' warnings in the server logs.
"""
import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink 24/7 Keep-Alive")
    parser.add_argument(
        "--url",
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "https://kyoka-lavalink.onrender.com",
        help="Render service URL (e.g. https://kyoka-lavalink.onrender.com)"
    )
    parser.add_argument(
        "--endpoint",
        default="/healthz",
        help="Health check endpoint path (default: /healthz)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "",
        help="Optional authorization password if pinging /version directly"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=540,
        help="Interval between pings in seconds (default: 540s = 9 minutes, below Render 15m idle limit)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ping check and exit (ideal for GitHub Actions scheduled workflows)"
    )
    parser.add_argument(
        "--wake-timeout",
        type=int,
        default=120,
        help="Max seconds to wait when waking up a sleeping instance"
    )
    return parser.parse_args()

def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        if ":443" in url or "onrender.com" in url:
            url = "https://" + url
        else:
            url = "http://" + url
    return url.rstrip("/")

def ping_endpoint(url: str, endpoint: str, password: str = None, timeout: float = 25.0):
    full_url = f"{url}{endpoint}"
    headers = {"User-Agent": "KyokaKeepAlive/3.0"}
    if password:
        headers["Authorization"] = password

    req = urllib.request.Request(full_url, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - start) * 1000
            content = resp.read().decode("utf-8", errors="replace").strip()
            return True, resp.status, latency, content
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        content = f"HTTP {e.code} {e.reason}"
        return (e.code == 200), e.code, latency, content
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return False, 0, latency, str(e)

def wake_up(url: str, endpoint: str, password: str, max_timeout: int):
    print(f"[*] Checking initial node state: {url}{endpoint}")
    start_time = time.time()
    attempt = 1
    while time.time() - start_time < max_timeout:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ok, code, lat, res = ping_endpoint(url, endpoint, password=password, timeout=20.0)
        if ok and code == 200:
            print(f"[{ts}] [AWAKE] Node is active! Status: HTTP 200 OK, Latency: {lat:.1f}ms, Resp: {res}")
            return True
        print(f"[{ts}] [WAITING] Attempt {attempt}: Node warming up / cold-starting... ({res[:60]})")
        attempt += 1
        time.sleep(10)
    print(f"[FAIL] Node did not respond within {max_timeout} seconds.")
    return False

def main():
    args = parse_args()
    base_url = clean_url(args.url)
    endpoint = args.endpoint if args.endpoint.startswith("/") else f"/{args.endpoint}"
    password = args.password.strip()

    print("=" * 70)
    print(" KYOKA LAVALINK V4 - 24/7 KEEP-ALIVE WORKER")
    print("=" * 70)
    print(f" Target Service   : {base_url}")
    print(f" Ping Target      : {base_url}{endpoint}")
    print(f" Execution Mode   : {'Single Shot' if args.once else f'Continuous Loop (Every {args.interval}s)'}")
    print("=" * 70)

    awake = wake_up(base_url, endpoint, password, args.wake_timeout)
    if not awake and args.once:
        sys.exit(1)

    if args.once:
        print("[SUCCESS] Keep-alive ping successfully delivered to container.")
        sys.exit(0)

    print(f"\n[*] Entering 24/7 keep-alive loop. Press Ctrl+C to terminate.")
    ping_count = 0
    try:
        while True:
            time.sleep(args.interval)
            ping_count += 1
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            ok, code, lat, res = ping_endpoint(base_url, endpoint, password=password, timeout=20.0)
            status_tag = "[PONG-OK]" if ok else "[PONG-FAIL]"
            print(f"[{ts}] {status_tag} #{ping_count} Status: {code} | Latency: {lat:.1f}ms | Resp: {res[:40]}")
    except KeyboardInterrupt:
        print("\n[*] Keep-alive process stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
