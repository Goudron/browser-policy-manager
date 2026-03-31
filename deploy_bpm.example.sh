#!/usr/bin/env bash
set -euo pipefail

# Browser Policy Manager deployment template.
#
# Usage:
#   1. Copy this file to `deploy_bpm.sh`
#   2. Fill in REMOTE_USER / REMOTE_HOST / REMOTE_PATH
#   3. Run: `bash deploy_bpm.sh`
#
# Optional overrides:
#   REMOTE_USER=my-user REMOTE_HOST=example.com REMOTE_PATH=/var/www/site/bpm \
#   bash deploy_bpm.sh

REMOTE_USER="${REMOTE_USER:-your-user}"
REMOTE_HOST="${REMOTE_HOST:-example.com}"
REMOTE_PATH="${REMOTE_PATH:-/var/www/example.com/bpm/}"
LOCAL_PATH="${LOCAL_PATH:-.}"

if [[ "${REMOTE_USER}" == "your-user" || "${REMOTE_HOST}" == "example.com" ]]; then
  echo "Fill in REMOTE_USER, REMOTE_HOST, and REMOTE_PATH before running this script."
  exit 1
fi

EXCLUDES=(
  "--exclude=.htaccess"
  "--exclude=.ssh/"
  "--exclude=*.ssh"
  "--exclude=deploy_bpm.sh"
  "--exclude=__pycache__/"
  "--exclude=*.py[cod]"
  "--exclude=.venv/"
  "--exclude=venv/"
  "--exclude=ENV/"
  "--exclude=env/"
  "--exclude=env.bak/"
  "--exclude=node_modules/"
  "--exclude=npm-debug.log*"
  "--exclude=yarn-debug.log*"
  "--exclude=yarn-error.log*"
  "--exclude=.pnpm-debug.log*"
  "--exclude=dist/"
  "--exclude=build/"
  "--exclude=.vscode/"
  "--exclude=.idea/"
  "--exclude=*.swp"
  "--exclude=*.swo"
  "--exclude=.DS_Store"
  "--exclude=Thumbs.db"
  "--exclude=.env"
  "--exclude=.env.*"
  "--exclude=*.log"
  "--exclude=logs/"
  "--exclude=*.coverage"
  "--exclude=.coverage*"
  "--exclude=coverage.xml"
  "--exclude=htmlcov/"
  "--exclude=.mypy_cache/"
  "--exclude=.pytest_cache/"
  "--exclude=.ruff_cache/"
  "--exclude=.cache/"
  "--exclude=pytestdebug.log"
  "--exclude=*.egg-info/"
  "--exclude=.eggs/"
  "--exclude=*.egg"
  "--exclude=*.whl"
  "--exclude=*.zip"
  "--exclude=*.tar.gz"
  "--exclude=*.orig"
  "--exclude=*.rej"
  "--exclude=*.db"
  "--exclude=*.sqlite"
  "--exclude=*.sqlite3"
  "--exclude=*.db-shm"
  "--exclude=*.db-wal"
  "--exclude=*.sqlite-shm"
  "--exclude=*.sqlite-wal"
  "--exclude=data/"
  "--exclude=.git/"
)

echo ">>> Deploying BPM to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
echo ">>> Local path: ${LOCAL_PATH}"

rsync -avz --delete \
  -e "ssh" \
  "${EXCLUDES[@]}" \
  "${LOCAL_PATH}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

echo ">>> Done."
