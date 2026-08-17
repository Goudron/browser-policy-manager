#!/usr/bin/env bash
# Install a generated BPM DMG into a disposable directory and prove its
# explicit migration and restart lifecycle on native macOS.
set -euo pipefail

usage() {
    echo "Usage: $0 --dmg PATH --architecture x64|arm64" >&2
    exit 64
}

DMG=""
ARCHITECTURE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dmg) DMG="$2"; shift 2 ;;
        --architecture) ARCHITECTURE="$2"; shift 2 ;;
        *) usage ;;
    esac
done
[[ -n "$DMG" && -n "$ARCHITECTURE" && -f "$DMG" ]] || usage
[[ "$(uname -s)" == "Darwin" ]] || { echo "[macos-smoke] native macOS host required" >&2; exit 2; }

case "$ARCHITECTURE" in
    x64) EXPECTED_MACHINE="x86_64" ;;
    arm64) EXPECTED_MACHINE="arm64" ;;
    *) usage ;;
esac
[[ "$(uname -m)" == "$EXPECTED_MACHINE" ]] || {
    echo "[macos-smoke] target $ARCHITECTURE requires $EXPECTED_MACHINE host" >&2; exit 2;
}

readonly WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/bpm-macos-smoke.XXXXXX")"
readonly MOUNT_POINT="$WORK_ROOT/mount"
readonly INSTALL_ROOT="$WORK_ROOT/Applications"
readonly STATE_ROOT="$WORK_ROOT/state"
readonly PORT=18000
PROCESS_ID=""

log() { printf '[macos-smoke] architecture=%s %s\n' "$ARCHITECTURE" "$*" >&2; }

cleanup() {
    if [[ -n "$PROCESS_ID" ]]; then
        kill "$PROCESS_ID" 2>/dev/null || true
        wait "$PROCESS_ID" 2>/dev/null || true
    fi
    if mount | grep --fixed-strings --quiet "on $MOUNT_POINT "; then
        hdiutil detach "$MOUNT_POINT" -quiet || true
    fi
    rm -rf "$WORK_ROOT"
}
trap cleanup EXIT

wait_ready() {
    local attempt
    for attempt in $(seq 1 30); do
        if curl --fail --silent --show-error "http://127.0.0.1:${PORT}/health/ready" \
            | grep --fixed-strings '"ready":true' >/dev/null; then
            return 0
        fi
        sleep 1
    done
    return 1
}

start_verify_stop() {
    local executable="$1"
    "$executable" serve --state-directory "$STATE_ROOT" --port "$PORT" \
        >"$WORK_ROOT/bpm.log" 2>&1 &
    PROCESS_ID=$!
    if ! wait_ready; then
        cat "$WORK_ROOT/bpm.log" >&2 || true
        return 1
    fi
    curl --fail --silent --show-error "http://127.0.0.1:${PORT}/" \
        | grep --fixed-strings '"version":"0.9.5"' >/dev/null
    curl --fail --silent --show-error --location "http://127.0.0.1:${PORT}/help/" >/dev/null
    curl --fail --silent --show-error "http://127.0.0.1:${PORT}/api/profiles" \
        | grep --fixed-strings '[]' >/dev/null
    kill "$PROCESS_ID"
    wait "$PROCESS_ID" || true
    PROCESS_ID=""
}

log "attach generated DMG"
mkdir -p "$MOUNT_POINT" "$INSTALL_ROOT"
hdiutil attach -readonly -nobrowse -mountpoint "$MOUNT_POINT" "$DMG" >/dev/null
test -x "$MOUNT_POINT/Browser Policy Manager.app/Contents/MacOS/bpm"
test -x "$MOUNT_POINT/BPM Migrate.command"
ditto "$MOUNT_POINT/Browser Policy Manager.app" "$INSTALL_ROOT/Browser Policy Manager.app"
EXECUTABLE="$INSTALL_ROOT/Browser Policy Manager.app/Contents/MacOS/bpm"
codesign --verify --deep --strict "$INSTALL_ROOT/Browser Policy Manager.app"
lipo -archs "$EXECUTABLE" | tr ' ' '\n' | grep --fixed-strings "$EXPECTED_MACHINE" >/dev/null

log "prove migration is explicit, then migrate"
test ! -e "$STATE_ROOT/bpm.db"
"$EXECUTABLE" migrate --state-directory "$STATE_ROOT"
test -f "$STATE_ROOT/bpm.db"

log "start, verify, stop, and restart BPM"
start_verify_stop "$EXECUTABLE"
start_verify_stop "$EXECUTABLE"
log "DMG smoke: OK"
