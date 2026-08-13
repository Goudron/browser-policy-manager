#!/bin/sh
# BPM's database contract requires an explicit Alembic operation.  In
# particular, `serve` must never upgrade a persistent database implicitly.
set -eu

command_name="${1:-serve}"
case "$command_name" in
    migrate)
        shift
        if [ "$#" -ne 0 ]; then
            echo "bpm migrate accepts no additional arguments" >&2
            exit 64
        fi
        exec alembic -c /opt/bpm/alembic.ini upgrade head
        ;;
    serve)
        shift
        exec uvicorn app.main:app --host "$BPM_HOST" --port "$BPM_PORT" "$@"
        ;;
    *)
        exec "$@"
        ;;
esac
