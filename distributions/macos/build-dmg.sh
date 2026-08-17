#!/usr/bin/env bash
# Build one BPM native macOS application bundle and wrap it in a DMG.
set -euo pipefail

usage() {
    echo "Usage: $0 --source-root PATH --output-directory PATH --source-revision SHA --target ID --architecture x64|arm64 --artifact NAME.dmg" >&2
    exit 64
}

SOURCE_ROOT=""
OUTPUT_DIRECTORY=""
SOURCE_REVISION=""
TARGET=""
ARCHITECTURE=""
ARTIFACT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source-root) SOURCE_ROOT="$2"; shift 2 ;;
        --output-directory) OUTPUT_DIRECTORY="$2"; shift 2 ;;
        --source-revision) SOURCE_REVISION="$2"; shift 2 ;;
        --target) TARGET="$2"; shift 2 ;;
        --architecture) ARCHITECTURE="$2"; shift 2 ;;
        --artifact) ARTIFACT="$2"; shift 2 ;;
        *) usage ;;
    esac
done
[[ -n "$SOURCE_ROOT" && -n "$OUTPUT_DIRECTORY" && -n "$SOURCE_REVISION" && -n "$TARGET" && -n "$ARCHITECTURE" && -n "$ARTIFACT" ]] || usage
[[ "$(uname -s)" == "Darwin" ]] || { echo "[macos-build] native macOS host required" >&2; exit 2; }

case "$ARCHITECTURE" in
    x64) EXPECTED_MACHINE="x86_64"; PYINSTALLER_ARCHITECTURE="x86_64" ;;
    arm64) EXPECTED_MACHINE="arm64"; PYINSTALLER_ARCHITECTURE="arm64" ;;
    *) echo "[macos-build] unsupported architecture: $ARCHITECTURE" >&2; exit 64 ;;
esac
[[ "$(uname -m)" == "$EXPECTED_MACHINE" ]] || {
    echo "[macos-build] target $ARCHITECTURE requires $EXPECTED_MACHINE host, found $(uname -m)" >&2
    exit 2
}

readonly BPM_VERSION="0.9.5"
readonly APP_NAME="Browser Policy Manager.app"
readonly PYTHON="${PYTHON_EXECUTABLE:-python}"
readonly WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/bpm-macos-build.XXXXXX")"

cleanup() { rm -rf "$WORK_ROOT"; }
trap cleanup EXIT

log() { printf '[macos-build] target=%s %s\n' "$TARGET" "$*" >&2; }

sha256() { shasum -a 256 "$1" | awk '{print $1}'; }

DOC_ARCHIVE="$SOURCE_ROOT/documentation/dist/bpm-documentation-${BPM_VERSION}.tar.gz"
DOC_CHECKSUM="${DOC_ARCHIVE}.sha256"
[[ -f "$DOC_ARCHIVE" && -f "$DOC_CHECKSUM" ]] || {
    echo "[macos-build] verified documentation archive is required" >&2; exit 2;
}
(cd "$(dirname "$DOC_ARCHIVE")" && shasum -a 256 -c "$(basename "$DOC_CHECKSUM")")

mkdir -p "$OUTPUT_DIRECTORY"
rm -f "$OUTPUT_DIRECTORY/$ARTIFACT" "$OUTPUT_DIRECTORY/$ARTIFACT.sha256" \
    "$OUTPUT_DIRECTORY/build-environment.json"

log "create isolated build environment"
"$PYTHON" -c 'import platform, sys; assert sys.version_info[:2] == (3, 14), sys.version; assert platform.machine() in ("x86_64", "arm64"), platform.machine()'
"$PYTHON" -m venv "$WORK_ROOT/venv"
"$WORK_ROOT/venv/bin/python" -m pip install --disable-pip-version-check --upgrade pip==25.3
"$WORK_ROOT/venv/bin/python" -m pip install --disable-pip-version-check \
    --requirement "$SOURCE_ROOT/distributions/macos/requirements.macos.lock"
export BPM_BUILD_PYTHON="$WORK_ROOT/venv/bin/python"

log "prepare immutable application payload"
mkdir -p "$WORK_ROOT/documentation/site"
tar --extract --gzip --file "$DOC_ARCHIVE" --strip-components=1 \
    --directory "$WORK_ROOT/documentation/site"

log "freeze BPM with the target-native Python runtime"
"$WORK_ROOT/venv/bin/python" -m PyInstaller --noconfirm --clean --onedir \
    --name bpm \
    --target-architecture "$PYINSTALLER_ARCHITECTURE" \
    --paths "$SOURCE_ROOT" \
    --hidden-import app.main \
    --hidden-import app.documentation.conversation_context \
    --hidden-import app.documentation.conversation_stream \
    --hidden-import migration_support.retirement_owner_v1 \
    --hidden-import migration_support.retirement_revision_materializer_v1 \
    --add-data "$SOURCE_ROOT/app/static:app/static" \
    --add-data "$SOURCE_ROOT/app/templates:app/templates" \
    --add-data "$SOURCE_ROOT/app/i18n:app/i18n" \
    --add-data "$SOURCE_ROOT/alembic:alembic" \
    --add-data "$SOURCE_ROOT/alembic.ini:." \
    --add-data "$SOURCE_ROOT/pyproject.toml:." \
    --add-data "$WORK_ROOT/documentation/site:documentation/site" \
    --add-data "$SOURCE_ROOT/LICENSE:." \
    --distpath "$WORK_ROOT/dist" \
    --workpath "$WORK_ROOT/work" \
    --specpath "$WORK_ROOT/spec" \
    "$SOURCE_ROOT/distributions/macos/launcher.py"

APP_ROOT="$WORK_ROOT/$APP_NAME"
mkdir -p "$APP_ROOT/Contents/MacOS" "$APP_ROOT/Contents/Resources"
cp -R "$WORK_ROOT/dist/bpm/." "$APP_ROOT/Contents/MacOS/"
install -m 0644 "$SOURCE_ROOT/distributions/macos/Info.plist.in" "$APP_ROOT/Contents/Info.plist"
printf 'APPL????' >"$APP_ROOT/Contents/PkgInfo"

log "apply ad-hoc test signature"
while IFS= read -r -d '' candidate; do
    if file --brief "$candidate" | grep --quiet 'Mach-O'; then
        codesign --force --sign - "$candidate"
    fi
done < <(find "$APP_ROOT/Contents/MacOS" -type f -print0)
codesign --force --sign - "$APP_ROOT"
codesign --verify --deep --strict "$APP_ROOT"

DMG_STAGE="$WORK_ROOT/dmg-root"
mkdir -p "$DMG_STAGE"
cp -R "$APP_ROOT" "$DMG_STAGE/$APP_NAME"
install -m 0755 "$SOURCE_ROOT/distributions/macos/BPM Migrate.command.in" \
    "$DMG_STAGE/BPM Migrate.command"
install -m 0644 "$SOURCE_ROOT/distributions/macos/README.md" "$DMG_STAGE/README.txt"
ln -s /Applications "$DMG_STAGE/Applications"

log "create compressed DMG"
hdiutil create -volname "Browser Policy Manager ${BPM_VERSION}" -srcfolder "$DMG_STAGE" \
    -ov -format UDZO "$OUTPUT_DIRECTORY/$ARTIFACT" >/dev/null
printf '%s  %s\n' "$(sha256 "$OUTPUT_DIRECTORY/$ARTIFACT")" "$ARTIFACT" \
    >"$OUTPUT_DIRECTORY/$ARTIFACT.sha256"

"$BPM_BUILD_PYTHON" - "$OUTPUT_DIRECTORY/build-environment.json" <<'PY'
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

output = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "host_architecture": platform.machine(),
    "macos_version": subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip(),
    "python_version": platform.python_version(),
    "pyinstaller_version": subprocess.check_output(
        [os.environ["BPM_BUILD_PYTHON"], "-m", "PyInstaller", "--version"], text=True
    ).strip(),
    "signing": "ad-hoc-test-only",
    "notarization": "not-submitted",
}
output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

log "DMG built: $OUTPUT_DIRECTORY/$ARTIFACT sha256=$(sha256 "$OUTPUT_DIRECTORY/$ARTIFACT")"
