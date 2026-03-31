#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ESBUILD_BIN="${ESBUILD_BIN:-$ROOT_DIR/node_modules/.bin/esbuild}"
MONACO_EDITOR_ROOT="${MONACO_EDITOR_ROOT:-$ROOT_DIR/node_modules/monaco-editor}"

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
