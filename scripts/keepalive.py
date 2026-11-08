#!/usr/bin/env python3
"""
24/7 Keep-Alive Worker for Kyoka Lavalink on Render Free.
Sends periodic lightweight HTTP GET requests to /version to prevent Render from idling.
Supports both continuous daemon mode and single-shot execution for cron / GitHub Actions.
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
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "",
        help="Render service URL (e.g. https://kyoka-lavalink.onrender.com)"
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

def ping_endpoint(url: str, timeout: float = 30.0):
    endpoint = f"{url}/version"
    req = urllib.request.Request(endpoint, headers={"User-Agent": "KyokaKeepAlive/2.0"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - start) * 1000
            content = resp.read().decode("utf-8").strip()
            return True, resp.status, latency, content
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        return False, e.code, latency, str(e)
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return False, 0, latency, str(e)

def wake_up(url: str, max_timeout: int):
    """Aggressive retry to wake a sleeping Render instance upon initial boot"""
    print(f"[*] Checking initial node state: {url}")
    start_time = time.time()
    attempt = 1
    while time.time() - start_time < max_timeout:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ok, code, lat, res = ping_endpoint(url, timeout=25.0)
        if ok:
            print(f"[{ts}] [AWAKE] Node is active! Status: {code}, Latency: {lat:.1f}ms, Version: {res}")
            return True
        print(f"[{ts}] [WAITING] Attempt {attempt}: Node warming up... ({res[:60]})")
        attempt += 1
        time.sleep(10)
    print(f"[FAIL] Node did not wake up within {max_timeout} seconds.")
    return False

def main():
    args = parse_args()
    if not args.url:
        print("[ERROR] Please provide --url or set RENDER_SERVICE_URL environment variable.")
        print("Example: python scripts/keepalive.py --url https://kyoka-lavalink.onrender.com")
        return 1

    base_url = clean_url(args.url)
    print("=" * 64)
    print(" KYOKA LAVALINK V4 - 24/7 KEEP-ALIVE SYSTEM")
    print("=" * 64)
    print(f" Target Service   : {base_url}")
    print(f" Ping Endpoint    : {base_url}/version")
    print(f" Keep-Alive Mode  : {'Single Shot' if args.once else f'Continuous (Every {args.interval}s)'}")
    print("=" * 64)

    # Initial wake-up attempt
    awake = wake_up(base_url, args.wake_timeout)
    if not awake:
        if args.once:
            return 1

    if args.once:
        print("[SUCCESS] Single keep-alive ping complete.")
        return 0

    print(f"\n[*] Entering 24/7 keep-alive loop. Press Ctrl+C to terminate.")
    ping_count = 0
    try:
        while True:
            time.sleep(args.interval)
            ping_count += 1
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            ok, code, lat, res = ping_endpoint(base_url, timeout=20.0)
            status_tag = "[PONG-OK]" if ok else "[PONG-FAIL]"
            print(f"[{ts}] {status_tag} #{ping_count} Status: {code} | Latency: {lat:.1f}ms | Resp: {res}")
    except KeyboardInterrupt:
        print("\n[*] Keep-alive process stopped by user.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
