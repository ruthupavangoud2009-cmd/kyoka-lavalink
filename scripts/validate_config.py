#!/usr/bin/env python3
"""
Configuration and Pre-flight Validator for Kyoka Lavalink V4 with Nginx Gateway.
Verifies all configuration files, memory limits, port bindings, and plugin definitions.
Runs without external dependencies (pure Python 3 standard library).
"""
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def log_check(name: str, passed: bool, detail: str = ""):
    status = " [PASS] " if passed else " [FAIL] "
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    msg = f"{color}{status}{reset} {name}"
    if detail:
        msg += f" -> {detail}"
    print(msg)
    return passed

def validate_files():
    print("=" * 70)
    print(" 1. PROJECT FILES VALIDATION")
    print("=" * 70)
    required_files = [
        "Dockerfile",
        "entrypoint.sh",
        "nginx.conf.template",
        "public/index.html",
        "application.yml",
        "render.yaml",
        ".gitignore",
        ".dockerignore",
        ".env.example",
        "README.md"
    ]
    all_ok = True
    for fname in required_files:
        path = ROOT_DIR / fname
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        all_ok = log_check(fname, exists, f"{size} bytes") and all_ok
    return all_ok

def validate_dockerfile():
    print("\n" + "=" * 70)
    print(" 2. DOCKERFILE VALIDATION")
    print("=" * 70)
    df_path = ROOT_DIR / "Dockerfile"
    if not df_path.exists():
        return False
    content = df_path.read_text(encoding="utf-8")

    all_ok = True
    has_base = "ghcr.io/lavalink-devs/lavalink:4-alpine" in content
    all_ok = log_check("Official Base Image (ghcr.io/lavalink-devs/lavalink:4-alpine)", has_base) and all_ok

    has_nginx = "apk add" in content and "nginx" in content
    all_ok = log_check("Nginx Package Installation", has_nginx) and all_ok

    has_healthcheck = "HEALTHCHECK" in content and "/healthz" in content
    all_ok = log_check("Container Healthcheck pointing to /healthz", has_healthcheck) and all_ok

    has_entrypoint = "ENTRYPOINT" in content and "entrypoint.sh" in content
    all_ok = log_check("Entrypoint Configuration (entrypoint.sh)", has_entrypoint) and all_ok

    return all_ok

def validate_nginx_template():
    print("\n" + "=" * 70)
    print(" 3. NGINX CONFIGURATION TEMPLATE VALIDATION")
    print("=" * 70)
    ng_path = ROOT_DIR / "nginx.conf.template"
    if not ng_path.exists():
        return False
    content = ng_path.read_text(encoding="utf-8")

    all_ok = True
    has_homepage = "location = / {" in content and "alias /var/www/html/index.html" in content
    all_ok = log_check("Direct Homepage Alias (Prevents 404 rewrite trap)", has_homepage) and all_ok

    has_favicon = "location = /favicon.ico {" in content and "return 204;" in content
    all_ok = log_check("Favicon 204 Handler (Eliminates Spring 404 logs)", has_favicon) and all_ok

    has_healthz = "location = /healthz {" in content and "auth_request /_internal_backend_probe;" in content
    all_ok = log_check("Backend Probing /healthz (Uses auth_request)", has_healthz) and all_ok

    has_ws = "location = /v4/websocket {" in content and "proxy_set_header Upgrade" in content
    all_ok = log_check("WebSocket Upgrade Proxy with Headers", has_ws) and all_ok

    has_drop = "location / {" in content and "return 404" in content
    all_ok = log_check("Unknown Route Drop (Local 404 without hitting Java)", has_drop) and all_ok

    return all_ok

def validate_application_yml():
    print("\n" + "=" * 70)
    print(" 4. APPLICATION.YML VALIDATION")
    print("=" * 70)
    app_path = ROOT_DIR / "application.yml"
    if not app_path.exists():
        return False
    content = app_path.read_text(encoding="utf-8")

    all_ok = True

    # Check loopback isolation
    has_loopback = bool(re.search(r"address:\s*127\.0\.0\.1", content))
    all_ok = log_check("Loopback Isolation (address: 127.0.0.1)", has_loopback) and all_ok

    # Check port 2333
    has_port = bool(re.search(r"port:\s*2333", content))
    all_ok = log_check("Internal Port 2333", has_port) and all_ok

    # Check YouTube plugin and disabled built-in source
    has_yt_plugin = "dev.lavalink.youtube:youtube-plugin:1.18.2" in content
    all_ok = log_check("YouTube Plugin Dependency (1.18.2)", has_yt_plugin) and all_ok

    has_yt_disabled = bool(re.search(r"sources:\s*[^}]*?youtube:\s*false", content, re.DOTALL))
    all_ok = log_check("Deprecated Built-in YouTube source disabled", has_yt_disabled) and all_ok

    # Check LavaSrc plugin
    has_lavasrc = "com.github.topi314.lavasrc:lavasrc-plugin:4.8.3" in content
    all_ok = log_check("LavaSrc Plugin Dependency (4.8.3)", has_lavasrc) and all_ok

    # Check Metrics enabled
    has_metrics = "prometheus:" in content and "enabled: true" in content and "endpoint: /metrics" in content
    all_ok = log_check("Prometheus Metrics Enabled for /healthz internal probe", has_metrics) and all_ok

    # Check Password parameterization without insecure default
    has_strict_pw = bool(re.search(r'password:\s*"\$\{LAVALINK_SERVER_PASSWORD\}"', content))
    all_ok = log_check("Strict Password Requirement (No insecure default fallback)", has_strict_pw) and all_ok

    no_insecure_default = "youshallnotpass" not in content
    all_ok = log_check("Zero Insecure Default Passwords in application.yml", no_insecure_default) and all_ok

    return all_ok

def validate_render_yaml():
    print("\n" + "=" * 70)
    print(" 5. RENDER.YAML BLUEPRINT VALIDATION")
    print("=" * 70)
    r_path = ROOT_DIR / "render.yaml"
    if not r_path.exists():
        return False
    content = r_path.read_text(encoding="utf-8")

    all_ok = True

    has_free_plan = bool(re.search(r"plan:\s*free", content))
    all_ok = log_check("Render Plan set to FREE ONLY (No unexpected charges)", has_free_plan) and all_ok

    has_docker = bool(re.search(r"runtime:\s*docker", content))
    all_ok = log_check("Runtime set to Docker", has_docker) and all_ok

    has_healthpath = "healthCheckPath: /healthz" in content
    all_ok = log_check("Render Health Check Path points to /healthz", has_healthpath) and all_ok

    has_memory_opts = "-Xmx256m" in content
    all_ok = log_check("Conservative Heap Limit configured (-Xmx256m)", has_memory_opts) and all_ok

    return all_ok

def validate_entrypoint():
    print("\n" + "=" * 70)
    print(" 6. ENTRYPOINT SUPERVISOR VALIDATION")
    print("=" * 70)
    ep_path = ROOT_DIR / "entrypoint.sh"
    if not ep_path.exists():
        return False
    content = ep_path.read_text(encoding="utf-8")

    all_ok = True
    has_bash = content.startswith("#!/bin/bash")
    all_ok = log_check("Bash Interpreter Declared", has_bash) and all_ok

    has_pw_check = "LAVALINK_SERVER_PASSWORD" in content and "exit 1" in content
    all_ok = log_check("Strict Startup Password Guard (Fails if empty)", has_pw_check) and all_ok

    has_traps = "trap cleanup SIGTERM SIGINT" in content
    all_ok = log_check("SIGTERM & SIGINT Traps Configured", has_traps) and all_ok

    has_proc_check = "/proc/$pid/stat" in content
    all_ok = log_check("Zombie-Safe Process State Inspection", has_proc_check) and all_ok

    has_nginx_t = "nginx -t" in content
    all_ok = log_check("Pre-flight Nginx Syntax Test", has_nginx_t) and all_ok

    return all_ok

def main():
    print("\nKYOKA LAVALINK V4 - ARCHITECTURAL VALIDATION\n")
    ok1 = validate_files()
    ok2 = validate_dockerfile()
    ok3 = validate_nginx_template()
    ok4 = validate_application_yml()
    ok5 = validate_render_yaml()
    ok6 = validate_entrypoint()

    print("\n" + "=" * 70)
    if ok1 and ok2 and ok3 and ok4 and ok5 and ok6:
        print("\033[92m [SUCCESS] ALL ARCHITECTURAL REQUIREMENTS FULLY SATISFIED!\033[0m")
        print("=" * 70 + "\n")
        return 0
    else:
        print("\033[91m [ERROR] VALIDATION FAILED! Please inspect errors above.\033[0m")
        print("=" * 70 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
