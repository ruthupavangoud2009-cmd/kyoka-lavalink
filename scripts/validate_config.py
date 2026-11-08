#!/usr/bin/env python3
"""
Configuration and Pre-flight Validator for Kyoka Lavalink V4.
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
    print("=" * 68)
    print(" 1. PROJECT FILES VALIDATION")
    print("=" * 68)
    required_files = [
        "Dockerfile",
        "entrypoint.sh",
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
    print("\n" + "=" * 68)
    print(" 2. DOCKERFILE VALIDATION")
    print("=" * 68)
    df_path = ROOT_DIR / "Dockerfile"
    if not df_path.exists():
        return False
    content = df_path.read_text(encoding="utf-8")

    all_ok = True
    has_base = "ghcr.io/lavalink-devs/lavalink:4-alpine" in content
    all_ok = log_check("Official Base Image (ghcr.io/lavalink-devs/lavalink:4-alpine)", has_base) and all_ok

    has_entrypoint = "ENTRYPOINT" in content and "entrypoint.sh" in content
    all_ok = log_check("Entrypoint Configuration (entrypoint.sh)", has_entrypoint) and all_ok

    has_apk = "apk add" in content and "curl" in content
    all_ok = log_check("Lightweight Network Utilities (curl)", has_apk) and all_ok

    return all_ok

def validate_application_yml():
    print("\n" + "=" * 68)
    print(" 3. APPLICATION.YML VALIDATION")
    print("=" * 68)
    app_path = ROOT_DIR / "application.yml"
    if not app_path.exists():
        return False
    content = app_path.read_text(encoding="utf-8")

    all_ok = True

    # Check port handling
    has_port = bool(re.search(r"port:\s*\$\{PORT:\d+\}", content))
    all_ok = log_check("Dynamic Port Variable (${PORT:...})", has_port) and all_ok

    # Check 0.0.0.0 bind
    has_bind = bool(re.search(r"address:\s*0\.0\.0\.0", content))
    all_ok = log_check("Listen Address 0.0.0.0", has_bind) and all_ok

    # Check YouTube plugin and disabled built-in source
    has_yt_plugin = "dev.lavalink.youtube:youtube-plugin" in content
    all_ok = log_check("YouTube Plugin Dependency declared", has_yt_plugin) and all_ok

    has_yt_disabled = bool(re.search(r"sources:\s*[^}]*?youtube:\s*false", content, re.DOTALL))
    all_ok = log_check("Deprecated Built-in YouTube source disabled", has_yt_disabled) and all_ok

    # Check LavaSrc plugin
    has_lavasrc = "com.github.topi314.lavasrc:lavasrc-plugin" in content
    all_ok = log_check("LavaSrc Plugin Dependency declared", has_lavasrc) and all_ok

    # Check HTTP & SoundCloud
    has_sc = bool(re.search(r"soundcloud:\s*true", content))
    has_http = bool(re.search(r"http:\s*true", content))
    all_ok = log_check("SoundCloud & Direct HTTP sources enabled", has_sc and has_http) and all_ok

    # Check Password parameterization
    has_pw = "LAVALINK_SERVER_PASSWORD" in content or "LAVALINK_PASSWORD" in content
    all_ok = log_check("Password Parameterization via Environment Variable", has_pw) and all_ok

    return all_ok

def validate_render_yaml():
    print("\n" + "=" * 68)
    print(" 4. RENDER.YAML BLUEPRINT VALIDATION")
    print("=" * 68)
    r_path = ROOT_DIR / "render.yaml"
    if not r_path.exists():
        return False
    content = r_path.read_text(encoding="utf-8")

    all_ok = True

    has_free_plan = bool(re.search(r"plan:\s*free", content))
    all_ok = log_check("Render Plan set to FREE ONLY (No unexpected charges)", has_free_plan) and all_ok

    has_docker = bool(re.search(r"runtime:\s*docker", content))
    all_ok = log_check("Runtime set to Docker", has_docker) and all_ok

    # Verify no unauthenticated HTTP healthCheckPath is configured
    no_incompatible_health = "healthCheckPath: /version" not in content
    all_ok = log_check("Render TCP Port Health Check Strategy (Prevents 401 Health Check Failures)", no_incompatible_health) and all_ok

    has_memory_opts = "-Xmx384m" in content
    all_ok = log_check("JVM Memory Heap Limit tuned for Free Tier (-Xmx384m)", has_memory_opts) and all_ok

    has_pw_var = "LAVALINK_SERVER_PASSWORD" in content
    all_ok = log_check("LAVALINK_SERVER_PASSWORD declared in blueprint", has_pw_var) and all_ok

    return all_ok

def main():
    print("\nKYOKA LAVALINK V4 - PRE-FLIGHT VALIDATION\n")
    ok1 = validate_files()
    ok2 = validate_dockerfile()
    ok3 = validate_application_yml()
    ok4 = validate_render_yaml()

    print("\n" + "=" * 68)
    if ok1 and ok2 and ok3 and ok4:
        print("\033[92m [SUCCESS] ALL CONFIGURATIONS ARE VALID AND READY FOR DEPLOYMENT!\033[0m")
        print("=" * 68 + "\n")
        return 0
    else:
        print("\033[91m [ERROR] VALIDATION FAILED! Please inspect errors above.\033[0m")
        print("=" * 68 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
