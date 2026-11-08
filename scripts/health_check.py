#!/usr/bin/env python3
"""
Comprehensive Health Check for Kyoka Lavalink V4.
Tests:
- Unauthenticated /version endpoint
- Authenticated /v4/info endpoint (checks loaded plugins)
- Authenticated /v4/stats endpoint (checks memory, uptime, players)
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink V4 Health Check")
    parser.add_argument(
        "--url",
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "http://localhost:2333",
        help="Lavalink base URL (e.g. https://kyoka-lavalink.onrender.com or http://localhost:2333)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "youshallnotpass",
        help="Lavalink server password"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds"
    )
    return parser.parse_args()

def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        # If port 443 or onrender.com default to https
        if ":443" in url or "onrender.com" in url:
            url = "https://" + url
        else:
            url = "http://" + url
    return url.rstrip("/")

def check_version(base_url: str, timeout: float):
    url = f"{base_url}/version"
    print(f"\n[*] 1. Probing unauthenticated endpoint: {url}")
    start = time.perf_counter()
    req = urllib.request.Request(url, headers={"User-Agent": "KyokaHealthCheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            version = resp.read().decode("utf-8").strip()
            print(f"    Status   : {resp.status} OK")
            print(f"    Latency  : {elapsed:.1f} ms")
            print(f"    Version  : {version}")
            if version.startswith("4"):
                print("    Check    : [PASS] Lavalink V4 verified")
                return True, version
            else:
                print(f"    Check    : [WARN] Unexpected version string: {version}")
                return True, version
    except urllib.error.HTTPError as e:
        print(f"    [FAIL] HTTP Error {e.code}: {e.reason}")
        return False, None
    except Exception as e:
        print(f"    [FAIL] Connection failed: {e}")
        return False, None

def check_info(base_url: str, password: str, timeout: float):
    url = f"{base_url}/v4/info"
    print(f"\n[*] 2. Probing authenticated REST endpoint: {url}")
    start = time.perf_counter()
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": password,
            "User-Agent": "KyokaHealthCheck/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            print(f"    Status   : {resp.status} OK (Authentication Successful)")
            print(f"    Latency  : {elapsed:.1f} ms")
            
            # Extract plugins
            plugins = data.get("plugins", [])
            print(f"    Loaded Plugins ({len(plugins)}):")
            for p in plugins:
                print(f"      - {p.get('name')} v{p.get('version')}")

            # Extract source managers
            sources = data.get("sourceManagers", [])
            print(f"    Active Sources: {', '.join(sources)}")
            print("    Check    : [PASS] REST API and plugins verified")
            return True, data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("    [FAIL] 401 Unauthorized! The password does not match LAVALINK_SERVER_PASSWORD.")
        else:
            print(f"    [FAIL] HTTP Error {e.code}: {e.reason}")
        return False, None
    except Exception as e:
        print(f"    [FAIL] Connection failed: {e}")
        return False, None

def check_stats(base_url: str, password: str, timeout: float):
    url = f"{base_url}/v4/stats"
    print(f"\n[*] 3. Probing server metrics endpoint: {url}")
    start = time.perf_counter()
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": password,
            "User-Agent": "KyokaHealthCheck/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            players = data.get("players", 0)
            playing = data.get("playingPlayers", 0)
            uptime_s = data.get("uptime", 0) / 1000
            mem = data.get("memory", {})
            used_mb = mem.get("used", 0) / (1024 * 1024)
            allocated_mb = mem.get("allocated", 0) / (1024 * 1024)

            print(f"    Status   : {resp.status} OK")
            print(f"    Latency  : {elapsed:.1f} ms")
            print(f"    Uptime   : {uptime_s:.0f} seconds ({uptime_s/3600:.2f} hours)")
            print(f"    Players  : {playing} playing / {players} active")
            print(f"    Memory   : {used_mb:.1f} MB used / {allocated_mb:.1f} MB allocated (Limit: 512 MB)")
            print("    Check    : [PASS] Server statistics operational")
            return True, data
    except urllib.error.HTTPError as e:
        print(f"    [FAIL] HTTP Error {e.code}: {e.reason}")
        return False, None
    except Exception as e:
        print(f"    [FAIL] Connection failed: {e}")
        return False, None

def main():
    args = parse_args()
    base_url = clean_url(args.url)
    
    print("=" * 64)
    print(" KYOKA LAVALINK V4 - HEALTH CHECK & DIAGNOSTICS")
    print("=" * 64)
    print(f" Target Endpoint : {base_url}")
    print(f" Password Length : {len(args.password)} chars (auth configured)")
    print(f" Timeout         : {args.timeout}s")
    print("=" * 64)

    ok_ver, _ = check_version(base_url, args.timeout)
    ok_info, _ = check_info(base_url, args.password, args.timeout)
    ok_stats, _ = check_stats(base_url, args.password, args.timeout)

    print("\n" + "=" * 64)
    if ok_ver and ok_info and ok_stats:
        print(" [RESULT] LAVALINK NODE IS HEALTHY, ONLINE, AND READY FOR KYOKA!")
        print("=" * 64 + "\n")
        return 0
    elif ok_ver and not ok_info:
        print(" [RESULT] LAVALINK IS RUNNING BUT AUTHENTICATION FAILED.")
        print(" Verify that LAVALINK_SERVER_PASSWORD matches on Render and client.")
        print("=" * 64 + "\n")
        return 2
    else:
        print(" [RESULT] LAVALINK NODE IS UNREACHABLE OR SLEEPING.")
        print(" If on Render Free: The service may be cold-starting (takes ~30-60s).")
        print("=" * 64 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
