#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python}"
fi

cd "$ROOT_DIR"

if [[ ! -f package-lock.json ]]; then
    echo "Missing package-lock.json; run npm install --package-lock-only --ignore-scripts first." >&2
    exit 1
fi

echo "Frontend vendor rebuild: phase 1/6 — installing pinned frontend dependencies with npm ci..."
npm ci

echo "Frontend vendor rebuild: phase 2/6 — building Monaco vendor bundles..."
npm run build:monaco

echo "Frontend vendor rebuild: phase 3/6 — synchronizing bundled dependency license notices..."
install -m 0644 node_modules/monaco-editor/LICENSE app/static/vendor/monaco.LICENSE
install -m 0644 node_modules/monaco-editor/ThirdPartyNotices.txt app/static/vendor/monaco.ThirdPartyNotices.txt
install -m 0644 node_modules/dompurify/LICENSE app/static/vendor/dompurify.LICENSE-APACHE
install -m 0644 node_modules/dompurify/LICENSE-MPL app/static/vendor/dompurify.LICENSE-MPL
install -m 0644 node_modules/marked/LICENSE app/static/vendor/marked.LICENSE

echo "Frontend vendor rebuild: phase 4/6 — verifying vendor license notices..."
"$PYTHON_BIN" tools/verify_frontend_vendor.py --check-licenses

echo "Frontend vendor rebuild: phase 5/6 — vendor size diff before lock update:"
"$PYTHON_BIN" tools/verify_frontend_vendor.py --size-report

echo "Frontend vendor rebuild: phase 6/6 — updating and verifying vendor checksum lock..."
"$PYTHON_BIN" tools/verify_frontend_vendor.py --write

"$PYTHON_BIN" tools/verify_frontend_vendor.py
echo "Frontend vendor rebuild: completed 6/6 phases."
