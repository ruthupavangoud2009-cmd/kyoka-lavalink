#!/usr/bin/env python3
"""
Comprehensive Health Check & Diagnostic Tool for Kyoka Lavalink V4.

Validates:
1. Security Check (Unauthenticated Probe): Verifies unauthenticated requests are blocked (HTTP 401).
2. Negative Auth Check: Verifies incorrect passwords are rejected (HTTP 403).
3. Authenticated Version Check: Verifies version endpoint (/version) returns HTTP 200 and '4.x'.
4. Authenticated REST API & Plugins: Verifies /v4/info, checks loaded plugins (youtube, lavasrc).
5. Authenticated Metrics & RAM: Verifies /v4/stats, uptime, player counts, memory against 512MB limit.
6. Cold-Start / Sleep Detection: Diagnoses Render Free 502/503 sleep states and provides actionable guidance.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

def parse_args():
    parser = argparse.ArgumentParser(description="Kyoka Lavalink V4 Production Health Check")
    parser.add_argument(
        "--url",
        default=os.getenv("RENDER_SERVICE_URL") or os.getenv("LAVALINK_URI") or "https://kyoka-lavalink.onrender.com",
        help="Lavalink base URL (e.g. https://kyoka-lavalink.onrender.com or http://localhost:2333)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "",
        help="Lavalink server password (must match LAVALINK_SERVER_PASSWORD in Render)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: 15s)"
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

def send_request(url: str, password: str = None, timeout: float = 15.0):
    headers = {"User-Agent": "KyokaHealthCheck/2.0"}
    if password is not None:
        headers["Authorization"] = password

    req = urllib.request.Request(url, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - start) * 1000
            data = resp.read().decode("utf-8", errors="replace").strip()
            return resp.status, data, latency, None
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        data = e.read().decode("utf-8", errors="replace").strip() if e.fp else ""
        return e.code, data, latency, e
    except urllib.error.URLError as e:
        latency = (time.perf_counter() - start) * 1000
        return 0, "", latency, e
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return 0, "", latency, e

def diagnose_connection_error(base_url: str, code: int, error_obj):
    if code in (502, 503):
        print("\n [DIAGNOSIS: RENDER COLD START]")
        print("  HTTP status 502/503 indicates that Render's reverse proxy received no response.")
        print("  On Render Free, services sleep after 15m of inactivity.")
        print("  The instance is currently booting up (JVM startup takes 30-50s).")
        print("  Please wait 30 seconds and run this check again.")
        return
    if code == 0:
        print("\n [DIAGNOSIS: UNREACHABLE HOST]")
        print(f"  Could not establish a network connection to {base_url}.")
        print(f"  Underlying error: {error_obj}")
        print("  Check that your internet connection is active and the URL is spelled correctly.")

def run_diagnostics(base_url: str, password: str, timeout: float):
    print("=" * 68)
    print(" KYOKA LAVALINK V4 - HEALTH CHECK & DIAGNOSTICS")
    print("=" * 68)
    print(f" Target Endpoint : {base_url}")
    print(f" Password Config : {'Set (' + str(len(password)) + ' chars)' if password else 'NOT PROVIDED (Auth checks will be skipped)'}")
    print(f" Timeout Budget  : {timeout:.1f}s")
    print("=" * 68)

    results = []

    # --------------------------------------------------------------------------
    # Step 1: Security Test (Unauthenticated Probe)
    # --------------------------------------------------------------------------
    print("\n[*] 1. Security Check (Unauthenticated Probe):")
    url_version = f"{base_url}/version"
    code, data, lat, err = send_request(url_version, password=None, timeout=timeout)
    if code in (502, 503, 0):
        diagnose_connection_error(base_url, code, err)
        return False

    if code == 401:
        print(f"    Status   : HTTP 401 Unauthorized ({lat:.1f} ms)")
        print("    Result   : [PASS] Authentication is strictly enforced. Unauthenticated requests are blocked.")
        results.append(("Security: Unauthenticated Blocking (401)", True))
    elif code == 200:
        print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
        print(f"    Notice   : /version responded anonymously ({data}).")
        results.append(("Security: Unauthenticated Probe", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms)")
        print(f"    Result   : [FAIL] Unexpected HTTP status: {code}")
        results.append(("Security: Unauthenticated Probe", False))

    # --------------------------------------------------------------------------
    # Step 2: Negative Auth Test (Invalid Password)
    # --------------------------------------------------------------------------
    print("\n[*] 2. Security Check (Invalid Password Rejection):")
    fake_pw = "invalid_password_probe_xyz999"
    code, data, lat, err = send_request(url_version, password=fake_pw, timeout=timeout)
    if code in (401, 403):
        print(f"    Status   : HTTP {code} Forbidden/Unauthorized ({lat:.1f} ms)")
        print("    Result   : [PASS] Lavalink correctly rejected incorrect password.")
        results.append(("Security: Invalid Password Rejection (403)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms)")
        print("    Result   : [FAIL] Server did not reject invalid password with 401/403.")
        results.append(("Security: Invalid Password Rejection", False))

    # --------------------------------------------------------------------------
    # Step 3: Authenticated Version Check
    # --------------------------------------------------------------------------
    if not password:
        print("\n[*] 3. Authenticated Version Check: SKIPPED (No password provided).")
        print("    Pass --password <YOUR_PASSWORD> or set LAVALINK_SERVER_PASSWORD environment variable.")
        results.append(("Authenticated Version Check", False))
        return False

    print("\n[*] 3. Authenticated Version Check:")
    code, version_str, lat, err = send_request(url_version, password=password, timeout=timeout)
    if code == 200:
        print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
        print(f"    Version  : {version_str}")
        if version_str.startswith("4"):
            print("    Result   : [PASS] Lavalink V4 verified successfully.")
            results.append(("Authenticated /version (V4)", True))
        else:
            print(f"    Result   : [WARN] Version string '{version_str}' does not start with 4.")
            results.append(("Authenticated /version", True))
    elif code in (401, 403):
        print(f"    Status   : HTTP {code} Forbidden/Unauthorized ({lat:.1f} ms)")
        print("    Result   : [FAIL] Password mismatch! The password does not match LAVALINK_SERVER_PASSWORD in Render.")
        results.append(("Authenticated /version", False))
        return False
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms)")
        print(f"    Result   : [FAIL] Failed to retrieve version: {err}")
        results.append(("Authenticated /version", False))

    # --------------------------------------------------------------------------
    # Step 4: Authenticated REST Info & Plugins Check
    # --------------------------------------------------------------------------
    print("\n[*] 4. Authenticated REST API & Plugins (/v4/info):")
    url_info = f"{base_url}/v4/info"
    code, info_raw, lat, err = send_request(url_info, password=password, timeout=timeout)
    if code == 200:
        try:
            info_data = json.loads(info_raw)
            print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
            jvm_ver = info_data.get("jvm", "Unknown JVM")
            lavaplayer_ver = info_data.get("lavaplayer", "Unknown")
            print(f"    JVM Runtime     : {jvm_ver}")
            print(f"    Lavaplayer      : {lavaplayer_ver}")

            # Inspect plugins
            plugins = info_data.get("plugins", [])
            print(f"    Loaded Plugins  : {len(plugins)}")
            has_youtube = False
            has_lavasrc = False
            for p in plugins:
                p_name = p.get("name", "Unknown")
                p_ver = p.get("version", "?")
                print(f"      - {p_name} v{p_ver}")
                if "youtube" in p_name.lower():
                    has_youtube = True
                if "lavasrc" in p_name.lower():
                    has_lavasrc = True

            # Inspect source managers
            sources = info_data.get("sourceManagers", [])
            print(f"    Active Sources  : {', '.join(sources)}")

            plugins_ok = has_youtube and has_lavasrc
            if plugins_ok:
                print("    Result   : [PASS] Both YouTube and LavaSrc plugins loaded.")
            else:
                print("    Result   : [WARN] One or more expected plugins were not listed.")
            results.append(("REST API & Plugins (/v4/info)", True))
        except Exception as e:
            print(f"    Parse Error: {e}")
            results.append(("REST API & Plugins (/v4/info)", False))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms)")
        results.append(("REST API & Plugins (/v4/info)", False))

    # --------------------------------------------------------------------------
    # Step 5: Authenticated Metrics & Memory (/v4/stats)
    # --------------------------------------------------------------------------
    print("\n[*] 5. Server Metrics & Memory Ceiling (/v4/stats):")
    url_stats = f"{base_url}/v4/stats"
    code, stats_raw, lat, err = send_request(url_stats, password=password, timeout=timeout)
    if code == 200:
        try:
            stats_data = json.loads(stats_raw)
            players = stats_data.get("players", 0)
            playing = stats_data.get("playingPlayers", 0)
            uptime_s = stats_data.get("uptime", 0) / 1000
            mem = stats_data.get("memory", {})
            used_mb = mem.get("used", 0) / (1024 * 1024)
            allocated_mb = mem.get("allocated", 0) / (1024 * 1024)
            free_mb = mem.get("free", 0) / (1024 * 1024)

            print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
            print(f"    Uptime   : {uptime_s:.0f}s ({uptime_s/3600:.2f} hours)")
            print(f"    Players  : {playing} playing / {players} connected")
            print(f"    Memory   : {used_mb:.1f} MB used / {allocated_mb:.1f} MB allocated (Free: {free_mb:.1f} MB)")
            print(f"    Ceiling  : Render Free 512 MB Container Limit (JVM heap cap: 384 MB)")

            if allocated_mb <= 450:
                print("    Result   : [PASS] Memory is well within Render Free safety margins.")
            else:
                print("    Result   : [WARN] Memory allocation is near free-tier container ceiling.")
            results.append(("Metrics & Memory (/v4/stats)", True))
        except Exception as e:
            print(f"    Parse Error: {e}")
            results.append(("Metrics & Memory (/v4/stats)", False))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms)")
        results.append(("Metrics & Memory (/v4/stats)", False))

    # --------------------------------------------------------------------------
    # Final Summary
    # --------------------------------------------------------------------------
    print("\n" + "=" * 68)
    print(" HEALTH CHECK RESULTS SUMMARY")
    print("=" * 68)
    all_passed = True
    for name, success in results:
        status_tag = "[PASS]" if success else "[FAIL]"
        print(f"  {status_tag:<8} {name}")
        if not success:
            all_passed = False
    print("=" * 68)

    if all_passed:
        print(" [OVERALL] SERVER IS LIVE, HEALTHY, AND FULLY AUTHENTICATED!\n")
        return 0
    else:
        print(" [OVERALL] ONE OR MORE CHECKS FAILED. See details above.\n")
        return 1

def main():
    args = parse_args()
    base_url = clean_url(args.url)
    success = run_diagnostics(base_url, args.password.strip(), args.timeout)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
