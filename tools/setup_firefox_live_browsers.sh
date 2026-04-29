#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/.bpm-test-browsers"
CHANNEL="${1:-release}"
GECKODRIVER_VERSION="${GECKODRIVER_VERSION:-0.36.0}"

case "${CHANNEL}" in
  release)
    FIREFOX_URL="https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US"
    ;;
  esr)
    FIREFOX_URL="https://download.mozilla.org/?product=firefox-esr-latest&os=linux64&lang=en-US"
    ;;
  *)
    echo "Unsupported channel: ${CHANNEL}. Use 'release' or 'esr'." >&2
    exit 2
    ;;
esac

mkdir -p "${TARGET_DIR}/firefox" "${TARGET_DIR}/geckodriver"

echo "Downloading Firefox (${CHANNEL}) into ${TARGET_DIR}/firefox ..."
curl -fL "${FIREFOX_URL}" -o "${TARGET_DIR}/firefox/firefox.tar.xz"
rm -rf "${TARGET_DIR}/firefox/firefox"
tar -xJf "${TARGET_DIR}/firefox/firefox.tar.xz" -C "${TARGET_DIR}/firefox"

echo "Downloading geckodriver ${GECKODRIVER_VERSION} into ${TARGET_DIR}/geckodriver ..."
curl -fL \
  "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
  -o "${TARGET_DIR}/geckodriver/geckodriver.tar.gz"
tar -xzf "${TARGET_DIR}/geckodriver/geckodriver.tar.gz" -C "${TARGET_DIR}/geckodriver"
chmod +x "${TARGET_DIR}/geckodriver/geckodriver"

FIREFOX_VERSION="$("${TARGET_DIR}/firefox/firefox/firefox" --version)"
GECKODRIVER_INSTALLED_VERSION="$("${TARGET_DIR}/geckodriver/geckodriver" --version | head -n 1)"

cat <<EOF

Live Firefox test binaries are ready in:
  ${TARGET_DIR}

Installed versions:
  ${FIREFOX_VERSION}
  ${GECKODRIVER_INSTALLED_VERSION}

The test harness will find them automatically, so you can run:
  .venv/bin/pytest -m firefox_live -q

EOF
