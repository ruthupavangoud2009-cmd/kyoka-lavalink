#!/usr/bin/env python3
"""
24/7 Keep-Alive Worker for Kyoka Lavalink on Render Free.

Pings the server periodically to reset Render's 15-minute inactivity idle timer.
Sends the Authorization header when provided to avoid triggering 'Authorization missing'
warnings in Lavalink's server logs.
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
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "",
        help="Lavalink server password (optional, avoids 'Authorization missing' logs when provided)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=540,
        help="Interval between pings in seconds (default: 540s = 9 minutes, well below Render's 15m idle limit)"
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

def ping_endpoint(url: str, password: str = None, timeout: float = 25.0):
    endpoint = f"{url}/version"
    headers = {"User-Agent": "KyokaKeepAlive/2.0"}
    if password:
        headers["Authorization"] = password

    req = urllib.request.Request(endpoint, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - start) * 1000
            content = resp.read().decode("utf-8", errors="replace").strip()
            return True, resp.status, latency, content
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        # 401 still hits Render container and resets idle timer, but logs auth warning
        content = f"HTTP {e.code} {e.reason}"
        return (e.code == 401 or e.code == 200), e.code, latency, content
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return False, 0, latency, str(e)

def wake_up(url: str, password: str, max_timeout: int):
    print(f"[*] Checking initial node state: {url}")
    start_time = time.time()
    attempt = 1
    while time.time() - start_time < max_timeout:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ok, code, lat, res = ping_endpoint(url, password=password, timeout=20.0)
        if ok:
            status_desc = "Authenticated (200 OK)" if code == 200 else f"Online (HTTP {code})"
            print(f"[{ts}] [AWAKE] Node is active! Status: {status_desc}, Latency: {lat:.1f}ms")
            return True
        print(f"[{ts}] [WAITING] Attempt {attempt}: Node warming up / cold-starting... ({res[:60]})")
        attempt += 1
        time.sleep(10)
    print(f"[FAIL] Node did not respond within {max_timeout} seconds.")
    return False

def main():
    args = parse_args()
    if not args.url:
        print("[ERROR] Please provide --url or set RENDER_SERVICE_URL environment variable.")
        sys.exit(1)

    base_url = clean_url(args.url)
    password = args.password.strip()

    print("=" * 68)
    print(" KYOKA LAVALINK V4 - 24/7 KEEP-ALIVE WORKER")
    print("=" * 68)
    print(f" Target Service   : {base_url}")
    print(f" Ping Target      : {base_url}/version")
    print(f" Auth Header      : {'Configured (Clean 200 OK pings)' if password else 'None (Container awake via 401 probe)'}")
    print(f" Execution Mode   : {'Single Shot' if args.once else f'Continuous Loop (Every {args.interval}s)'}")
    print("=" * 68)

    awake = wake_up(base_url, password, args.wake_timeout)
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
            ok, code, lat, res = ping_endpoint(base_url, password=password, timeout=20.0)
            status_tag = "[PONG-OK]" if ok else "[PONG-FAIL]"
            print(f"[{ts}] {status_tag} #{ping_count} Status: {code} | Latency: {lat:.1f}ms | Resp: {res[:40]}")
    except KeyboardInterrupt:
        print("\n[*] Keep-alive process stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
