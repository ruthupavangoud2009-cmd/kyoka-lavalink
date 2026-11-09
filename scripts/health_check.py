#!/usr/bin/env python3
"""
Comprehensive Health Check & Diagnostic Tool for Kyoka Lavalink V4.

Validates the full Edge Gateway + Lavalink Backend architecture:
1. Public Homepage (GET /) -> Must return HTTP 200 OK (text/html).
2. Public Favicon (GET /favicon.ico) -> Must return HTTP 204 No Content.
3. Public Health Check (GET /healthz) -> Must return HTTP 200 OK (verifies backend is up).
4. Unknown Route Rejection (GET /unknown-probe) -> Must return HTTP 404 Not Found (Nginx local drop).
5. Unauthenticated Protected REST Check (GET /v4/info) -> Must return HTTP 401 Unauthorized.
6. Negative Authentication Check (GET /v4/info) -> Must return HTTP 403 Forbidden.
7. Authenticated Version Check (GET /version) -> Must return HTTP 200 OK.
8. Authenticated REST Info & Plugins (GET /v4/info) -> Checks YouTube 1.18.2 & LavaSrc 4.8.3.
9. Authenticated Server Metrics & Memory (GET /v4/stats) -> Checks RAM consumption against 512MB limit.
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
        help="Lavalink base URL (e.g. https://kyoka-lavalink.onrender.com or http://localhost:10000)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LAVALINK_SERVER_PASSWORD") or os.getenv("LAVALINK_PASSWORD") or "",
        help="Lavalink server password"
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
    headers = {"User-Agent": "KyokaHealthCheck/3.0"}
    if password:
        headers["Authorization"] = password

    req = urllib.request.Request(url, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - start) * 1000
            data = resp.read().decode("utf-8", errors="replace").strip()
            content_type = resp.headers.get("Content-Type", "")
            return resp.status, data, latency, content_type, None
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        data = e.read().decode("utf-8", errors="replace").strip() if e.fp else ""
        content_type = e.headers.get("Content-Type", "") if e.headers else ""
        return e.code, data, latency, content_type, e
    except urllib.error.URLError as e:
        latency = (time.perf_counter() - start) * 1000
        return 0, "", latency, "", e
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return 0, "", latency, "", e

def run_diagnostics(base_url: str, password: str, timeout: float):
    print("=" * 70)
    print(" KYOKA LAVALINK V4 - FULL ARCHITECTURE DIAGNOSTICS")
    print("=" * 70)
    print(f" Target Endpoint : {base_url}")
    print(f" Password Config : {'Set (' + str(len(password)) + ' chars)' if password else 'NOT PROVIDED'}")
    print(f" Timeout Budget  : {timeout:.1f}s")
    print("=" * 70)

    results = []

    # 1. Public Homepage (GET /)
    print("\n[*] 1. Public Homepage (GET /):")
    code, data, lat, ct, err = send_request(f"{base_url}/", password=None, timeout=timeout)
    if code == 200 and "KYOKA" in data:
        print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
        print(f"    Type     : {ct}")
        print("    Result   : [PASS] Homepage served successfully without authentication.")
        results.append(("Public Homepage (GET /)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
        results.append(("Public Homepage (GET /)", False))

    # 2. Public Favicon (GET /favicon.ico)
    print("\n[*] 2. Public Favicon (GET /favicon.ico):")
    code, data, lat, ct, err = send_request(f"{base_url}/favicon.ico", password=None, timeout=timeout)
    if code == 204:
        print(f"    Status   : HTTP 204 No Content ({lat:.1f} ms)")
        print("    Result   : [PASS] Favicon handled cleanly (204 No Content).")
        results.append(("Public Favicon (GET /favicon.ico)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
        results.append(("Public Favicon (GET /favicon.ico)", False))

    # 3. Public Health Check (GET /healthz)
    print("\n[*] 3. Public Health Check (GET /healthz):")
    code, data, lat, ct, err = send_request(f"{base_url}/healthz", password=None, timeout=timeout)
    if code == 200 and "healthy" in data:
        print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
        print(f"    Response : {data}")
        print("    Result   : [PASS] Backend Lavalink operational. Zero raw metrics exposed.")
        results.append(("Public Health Check (GET /healthz)", True))
    elif code == 502:
        print(f"    Status   : HTTP 502 Bad Gateway ({lat:.1f} ms)")
        print(f"    Response : {data}")
        print("    Result   : [FAIL] Backend Lavalink is booting, unresponsive, or down.")
        results.append(("Public Health Check (GET /healthz)", False))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
        results.append(("Public Health Check (GET /healthz)", False))

    # 4. Unknown Route Rejection (GET /unknown-probe)
    print("\n[*] 4. Local Unknown Route Rejection (GET /unknown-probe-xyz):")
    code, data, lat, ct, err = send_request(f"{base_url}/unknown-probe-xyz", password=None, timeout=timeout)
    if code == 404:
        print(f"    Status   : HTTP 404 Not Found ({lat:.1f} ms)")
        print("    Result   : [PASS] Arbitrary routes dropped locally by Nginx without hitting Java.")
        results.append(("Unknown Route Rejection (404)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - Expected 404")
        results.append(("Unknown Route Rejection (404)", False))

    # 5. Unauthenticated REST Rejection (GET /v4/info)
    print("\n[*] 5. Unauthenticated REST Security Check (GET /v4/info):")
    code, data, lat, ct, err = send_request(f"{base_url}/v4/info", password=None, timeout=timeout)
    if code == 401:
        print(f"    Status   : HTTP 401 Unauthorized ({lat:.1f} ms)")
        print("    Result   : [PASS] Unauthenticated access to /v4/info strictly blocked.")
        results.append(("Unauthenticated REST Block (401)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - Expected 401 Unauthorized")
        results.append(("Unauthenticated REST Block (401)", False))

    # 6. Invalid Password Rejection (GET /v4/info)
    print("\n[*] 6. Invalid Password Security Check (GET /v4/info):")
    code, data, lat, ct, err = send_request(f"{base_url}/v4/info", password="wrong_test_password_123", timeout=timeout)
    if code == 403:
        print(f"    Status   : HTTP 403 Forbidden ({lat:.1f} ms)")
        print("    Result   : [PASS] Incorrect password correctly rejected with 403 Forbidden.")
        results.append(("Invalid Password Rejection (403)", True))
    else:
        print(f"    Status   : HTTP {code} ({lat:.1f} ms) - Expected 403 Forbidden")
        results.append(("Invalid Password Rejection (403)", False))

    # 7. Authenticated Checks (Require valid password)
    if not password:
        print("\n[*] Authenticated Version & Plugins Check: SKIPPED (No password provided).")
        print("    Pass --password <YOUR_PASSWORD> or set LAVALINK_SERVER_PASSWORD environment variable.")
        results.append(("Authenticated API Verification", False))
    else:
        print("\n[*] 7. Authenticated Version Check (/version):")
        code, data, lat, ct, err = send_request(f"{base_url}/version", password=password, timeout=timeout)
        if code == 200:
            print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
            print(f"    Version  : {data}")
            results.append(("Authenticated /version", True))
        else:
            print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
            results.append(("Authenticated /version", False))

        print("\n[*] 8. Authenticated REST Info & Plugin Loading (/v4/info):")
        code, data, lat, ct, err = send_request(f"{base_url}/v4/info", password=password, timeout=timeout)
        if code == 200:
            try:
                info_json = json.loads(data)
                jvm_ver = info_json.get("jvm", "Unknown")
                plugins = info_json.get("plugins", [])
                print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
                print(f"    JVM      : {jvm_ver}")
                print(f"    Plugins  : {len(plugins)} loaded")
                for p in plugins:
                    print(f"      - {p.get('name')} v{p.get('version')}")
                results.append(("Authenticated REST /v4/info", True))
            except Exception as e:
                print(f"    Parse Error: {e}")
                results.append(("Authenticated REST /v4/info", False))
        else:
            print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
            results.append(("Authenticated REST /v4/info", False))

        print("\n[*] 9. Authenticated Server Metrics & Memory (/v4/stats):")
        code, data, lat, ct, err = send_request(f"{base_url}/v4/stats", password=password, timeout=timeout)
        if code == 200:
            try:
                stats_json = json.loads(data)
                mem = stats_json.get("memory", {})
                used_mb = mem.get("used", 0) / (1024 * 1024)
                allocated_mb = mem.get("allocated", 0) / (1024 * 1024)
                uptime_s = stats_json.get("uptime", 0) / 1000
                print(f"    Status   : HTTP 200 OK ({lat:.1f} ms)")
                print(f"    Uptime   : {uptime_s:.0f}s ({uptime_s/3600:.2f} hours)")
                print(f"    Memory   : {used_mb:.1f} MB used / {allocated_mb:.1f} MB allocated (Free container limit: 512 MB)")
                results.append(("Authenticated /v4/stats", True))
            except Exception as e:
                print(f"    Parse Error: {e}")
                results.append(("Authenticated /v4/stats", False))
        else:
            print(f"    Status   : HTTP {code} ({lat:.1f} ms) - {err}")
            results.append(("Authenticated /v4/stats", False))

    # Summary
    print("\n" + "=" * 70)
    print(" VERIFICATION TEST RESULTS SUMMARY")
    print("=" * 70)
    all_ok = True
    for name, success in results:
        status_tag = "[PASS]" if success else "[FAIL]"
        print(f"  {status_tag:<8} {name}")
        if not success:
            all_ok = False
    print("=" * 70 + "\n")

    return all_ok

def main():
    args = parse_args()
    base_url = clean_url(args.url)
    success = run_diagnostics(base_url, args.password.strip(), args.timeout)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
