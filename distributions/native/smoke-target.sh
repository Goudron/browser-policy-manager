#!/usr/bin/env bash
# Install one generated native package into a fresh target userspace and prove
# the explicit-migration, runtime, documentation, and restart contract.
set -euo pipefail

required_environment=(BPM_NATIVE_TARGET BPM_NATIVE_FORMAT BPM_NATIVE_ARTIFACT)
for variable_name in "${required_environment[@]}"; do
    if [[ -z "${!variable_name:-}" ]]; then
        echo "[native-smoke] missing required environment: ${variable_name}" >&2
        exit 64
    fi
done

readonly PACKAGE_FILE="/packages/${BPM_NATIVE_ARTIFACT}"

log() {
    printf '[native-smoke] target=%s %s\n' "$BPM_NATIVE_TARGET" "$*" >&2
}

install_package() {
    test -f "$PACKAGE_FILE"
    case "$BPM_NATIVE_FORMAT" in
        deb)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update
            apt-get install --yes --no-install-recommends ca-certificates curl
            apt-get install --yes "$PACKAGE_FILE"
            ;;
        rpm)
            dnf install --assumeyes ca-certificates curl "$PACKAGE_FILE"
            ;;
        arch)
            pacman -Syu --noconfirm --needed ca-certificates curl
            test "$(pacman-mirrors -G)" = "stable"
            pacman -U --noconfirm "$PACKAGE_FILE"
            ;;
        *)
            echo "[native-smoke] unsupported package format: $BPM_NATIVE_FORMAT" >&2
            exit 64
            ;;
    esac
}

wait_ready() {
    local attempt
    for attempt in $(seq 1 30); do
        if curl --fail --silent --show-error http://127.0.0.1:8000/health/ready \
            | grep --fixed-strings '"ready":true' >/dev/null; then
            return 0
        fi
        sleep 1
    done
    return 1
}

start_and_verify() {
    local process_id
    runuser -u bpm -- /usr/bin/bpm serve >/tmp/bpm-native-smoke.log 2>&1 &
    process_id=$!
    if ! wait_ready; then
        cat /tmp/bpm-native-smoke.log >&2 || true
        kill "$process_id" 2>/dev/null || true
        wait "$process_id" 2>/dev/null || true
        return 1
    fi
    curl --fail --silent --show-error http://127.0.0.1:8000/ \
        | grep --fixed-strings '"version":"0.9.5.1"' >/dev/null
    curl --fail --silent --show-error --location http://127.0.0.1:8000/help/ >/dev/null
    curl --fail --silent --show-error http://127.0.0.1:8000/profiles >/dev/null
    curl --fail --silent --show-error http://127.0.0.1:8000/api/profiles \
        | grep --fixed-strings '[]' >/dev/null
    kill "$process_id"
    # The expected SIGTERM exit from the foreground server is not a smoke
    # failure; the next invocation proves restartability.
    wait "$process_id" || true
}

main() {
    log "install generated package"
    install_package
    id bpm
    test -f /usr/lib/systemd/system/bpm.service
    test -f /opt/bpm/release-manifest.json
    /usr/bin/bpm version | grep --fixed-strings '0.9.5.1'
    /opt/bpm/venv/bin/python -I -c "
import importlib.util
assert all(importlib.util.find_spec(name) is None for name in ('numpy', 'onnxruntime', 'tokenizers'))
"
    log "apply migration explicitly"
    /usr/bin/bpm-migrate
    log "start, verify, stop, and restart BPM"
    start_and_verify
    start_and_verify
    log "native package smoke: OK"
}

main "$@"
