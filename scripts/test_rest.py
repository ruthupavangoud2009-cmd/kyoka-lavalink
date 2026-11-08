#!/usr/bin/env python3
"""
REST API Audio Source & Track Resolution Test for Kyoka Lavalink V4.

Tests search queries and resolution across configured audio sources:
- YouTube (via dev.lavalink.youtube plugin)
- SoundCloud (built-in source)
- Direct HTTP Audio stream / Internet Radio
- Spotify search (via LavaSrc plugin)

Accurately handles:
- HTTPS / TLS connections
- HTTP Authorization header
- 401/403 password mismatch errors
- 502/503 Render cold start and sleep/wake detection
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink V4 Track Resolution Test")
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
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds"
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

def test_resolve(base_url: str, password: str, identifier: str, source_name: str, timeout: float):
    encoded_id = urllib.parse.quote(identifier)
    endpoint = f"{base_url}/v4/loadtracks?identifier={encoded_id}"
    print(f"\n[*] Testing {source_name} Resolution:")
    print(f"    Query    : {identifier}")

    if not password:
        print("    [FAIL] No password provided. REST resolution requires authentication.")
        return False

    req = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": password,
            "User-Agent": "KyokaRestTest/2.0"
        }
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            load_type = data.get("loadType")
            print(f"    Status   : HTTP 200 OK ({elapsed:.1f} ms)")
            print(f"    LoadType : {load_type}")

            if load_type in ("track", "playlist", "search"):
                tracks = data.get("data", [])
                if isinstance(tracks, list):
                    count = len(tracks)
                    first_title = tracks[0].get("info", {}).get("title") if count > 0 else "None"
                    first_author = tracks[0].get("info", {}).get("author") if count > 0 else "None"
                elif isinstance(tracks, dict):
                    count = 1
                    first_title = tracks.get("info", {}).get("title", "Unknown")
                    first_author = tracks.get("info", {}).get("author", "Unknown")
                else:
                    count = 0
                    first_title = "None"
                    first_author = "None"

                print(f"    Found    : {count} tracks")
                print(f"    Sample   : \"{first_title}\" by {first_author}")
                print(f"    Result   : [PASS] {source_name} resolution operational")
                return True
            elif load_type == "empty":
                print(f"    Result   : [WARN] Query returned 0 tracks (loadType: empty)")
                return True
            else:
                severity = data.get("data", {}).get("severity", "UNKNOWN")
                message = data.get("data", {}).get("message", "No message provided")
                print(f"    Result   : [FAIL] loadType '{load_type}' - Severity: {severity}, Msg: {message}")
                return False

    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        if e.code in (401, 403):
            print(f"    Result   : [FAIL] HTTP {e.code} Forbidden/Unauthorized ({elapsed:.1f} ms) - Password does not match LAVALINK_SERVER_PASSWORD in Render.")
        elif e.code in (502, 503):
            print(f"    Result   : [FAIL] HTTP {e.code} Bad Gateway ({elapsed:.1f} ms) - Render instance is cold-starting or sleeping. Wait 30-50s.")
        else:
            print(f"    Result   : [FAIL] HTTP {e.code}: {e.reason} ({elapsed:.1f} ms)")
        return False
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"    Result   : [FAIL] Connection error ({elapsed:.1f} ms): {e}")
        return False

def main():
    args = parse_args()
    base_url = clean_url(args.url)

    print("=" * 68)
    print(" KYOKA LAVALINK V4 - REST API TRACK RESOLUTION TEST")
    print("=" * 68)
    print(f" Target Endpoint : {base_url}")
    print(f" Password Config : {'Set (' + str(len(args.password)) + ' chars)' if args.password else 'NOT PROVIDED'}")
    print(f" Timeout Budget  : {args.timeout:.1f}s")
    print("=" * 68)

    if not args.password:
        print("\n [ERROR] Please provide --password or set LAVALINK_SERVER_PASSWORD environment variable.\n")
        sys.exit(1)

    results = []

    # 1. YouTube Search (via dev.lavalink.youtube plugin)
    yt_ok = test_resolve(
        base_url, args.password,
        "ytsearch:Lofi Hip Hop Chill Beats",
        "YouTube (youtube-plugin)",
        args.timeout
    )
    results.append(("YouTube Search", yt_ok))

    # 2. SoundCloud Search
    sc_ok = test_resolve(
        base_url, args.password,
        "scsearch:Alan Walker Faded",
        "SoundCloud",
        args.timeout
    )
    results.append(("SoundCloud Search", sc_ok))

    # 3. Direct HTTP Audio Stream (Internet Radio MP3)
    radio_url = "https://stream.nightride.fm/chillsynth.mp3"
    http_ok = test_resolve(
        base_url, args.password,
        radio_url,
        "Direct HTTP / Internet Radio",
        args.timeout
    )
    results.append(("Direct HTTP Audio", http_ok))

    # 4. Spotify Search via LavaSrc
    sp_ok = test_resolve(
        base_url, args.password,
        "spsearch:Daft Punk Get Lucky",
        "Spotify (LavaSrc Plugin)",
        args.timeout
    )
    results.append(("Spotify (LavaSrc)", sp_ok))

    print("\n" + "=" * 68)
    print(" TRACK RESOLUTION RESULTS SUMMARY")
    print("=" * 68)
    all_ok = True
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status:<8} {name}")
        if not success:
            all_ok = False
    print("=" * 68 + "\n")

    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
