#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "=== Running Configuration Validation ==="
python3 "$DIR/scripts/validate_config.py"

