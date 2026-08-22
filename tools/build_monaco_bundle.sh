#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ESBUILD_BIN="${ESBUILD_BIN:-$ROOT_DIR/node_modules/.bin/esbuild}"
MONACO_EDITOR_ROOT="${MONACO_EDITOR_ROOT:-$ROOT_DIR/node_modules/monaco-editor}"
DOMPURIFY_ROOT="${DOMPURIFY_ROOT:-$ROOT_DIR/node_modules/dompurify}"

if [[ ! -x "$ESBUILD_BIN" ]]; then
    echo "Missing esbuild binary at $ESBUILD_BIN" >&2
    echo "Install frontend dev dependencies first, then rerun the build." >&2
    exit 1
fi

if [[ ! -d "$MONACO_EDITOR_ROOT/esm" ]]; then
    echo "Missing Monaco ESM sources at $MONACO_EDITOR_ROOT/esm" >&2
    echo "Install frontend dev dependencies first, then rerun the build." >&2
    exit 1
fi

# Monaco 0.56.0 vendors DOMPurify 3.4.8 inside its ESM tree even when npm resolves the patched
# 3.4.14 dependency. Overlay the locked patched ESM source before bundling so the checked-in
# browser asset contains the audited implementation rather than merely reporting a clean npm tree.
DOMPURIFY_SOURCE="$DOMPURIFY_ROOT/dist/purify.es.mjs"
MONACO_DOMPURIFY_SOURCE="$MONACO_EDITOR_ROOT/esm/vs/base/browser/dompurify/dompurify.js"
if [[ ! -f "$DOMPURIFY_SOURCE" || ! -f "$MONACO_DOMPURIFY_SOURCE" ]]; then
    echo "Missing locked DOMPurify or Monaco overlay target." >&2
    exit 1
fi
if ! grep -q "DOMPurify 3.4.14" "$DOMPURIFY_SOURCE"; then
    echo "Resolved DOMPurify source is not the locked 3.4.14 implementation." >&2
    exit 1
fi
install -m 0644 "$DOMPURIFY_SOURCE" "$MONACO_DOMPURIFY_SOURCE"

cd "$ROOT_DIR"

mkdir -p app/static/vendor/monaco-assets

"$ESBUILD_BIN" app/static_src/profiles_monaco_entry.js \
    --bundle \
    --platform=browser \
    --format=iife \
    --target=es2020 \
    --outfile=app/static/vendor/profiles_monaco.js \
    --loader:.css=css \
    --loader:.ttf=file \
    --alias:monaco-editor="$MONACO_EDITOR_ROOT" \
    --asset-names=vendor/monaco-assets/[name]-[hash] \
    --public-path=/static

"$ESBUILD_BIN" "$MONACO_EDITOR_ROOT/esm/vs/editor/editor.worker.js" \
    --bundle \
    --platform=browser \
    --format=iife \
    --target=es2020 \
    --outfile=app/static/vendor/monaco-editor.worker.js \
    --loader:.css=css \
    --loader:.ttf=file \
    --asset-names=vendor/monaco-assets/[name]-[hash] \
    --public-path=/static

"$ESBUILD_BIN" "$MONACO_EDITOR_ROOT/esm/vs/language/json/json.worker.js" \
    --bundle \
    --platform=browser \
    --format=iife \
    --target=es2020 \
    --outfile=app/static/vendor/monaco-json.worker.js \
    --loader:.css=css \
    --loader:.ttf=file \
    --asset-names=vendor/monaco-assets/[name]-[hash] \
    --public-path=/static
