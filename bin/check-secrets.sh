#!/usr/bin/env bash
# Scan everything git tracks or has staged for secrets. Same rules as the pre-commit hook.
# Ignored files (jumpbox-setup/.env, private/) are not scanned: they are meant to hold secrets locally.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
git ls-files -z | xargs -0 python -I bin/sanitize.py check
