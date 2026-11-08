#!/usr/bin/env python3
"""
REST API Audio Source & Track Resolution Test for Kyoka Lavalink V4.
Tests search queries and resolution across configured audio sources:
- YouTube (via dev.lavalink.youtube plugin)
- SoundCloud (built-in)
- Direct HTTP Audio URL
- Spotify search (via LavaSrc plugin, if enabled)
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink V4 Track Resolution Test")
    parser.add_argument(
        "--url",
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "http://localhost:2333",
        help="Lavalink base URL"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "youshallnotpass",
        help="Lavalink password"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
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
    start = time.perf_counter()
    req = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": password,
            "User-Agent": "KyokaRestTest/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            load_type = data.get("loadType")
            print(f"    Latency  : {elapsed:.1f} ms")
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
                print(f"    Result   : [PASS] {source_name} resolution working")
                return True
            elif load_type == "empty":
                print(f"    Result   : [WARN] No tracks found for query (loadType: empty)")
                return True
            else:
                severity = data.get("data", {}).get("severity", "UNKNOWN")
                message = data.get("data", {}).get("message", "No message provided")
                print(f"    Result   : [FAIL] loadType '{load_type}' - Severity: {severity}, Msg: {message}")
                return False
    except urllib.error.HTTPError as e:
        print(f"    Result   : [FAIL] HTTP {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"    Result   : [FAIL] Error: {e}")
        return False

def main():
    args = parse_args()
    base_url = clean_url(args.url)

    print("=" * 64)
    print(" KYOKA LAVALINK V4 - REST API TRACK RESOLUTION TEST")
    print("=" * 64)
    print(f" Endpoint : {base_url}")
    print("=" * 64)

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
        "scsearch:Synthwave Chill",
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

    print("\n" + "=" * 64)
    print(" TEST RESULTS SUMMARY")
    print("=" * 64)
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f" {status:<8} {name}")
    print("=" * 64 + "\n")

    # If at least the primary sources work, exit 0
    if yt_ok or sc_ok or http_ok:
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
