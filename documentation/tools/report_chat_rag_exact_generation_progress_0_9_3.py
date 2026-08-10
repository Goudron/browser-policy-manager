"""Report progress of a local exact-vector RAG generation without modifying it."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from generate_chat_rag_exact_generations_0_9_3 import (
    CONFIG_PATH,
    _compatibility_key,
    _decision_candidate,
    _passage,
    _read_cached_vector,
    _read_json,
    _validate_chunks,
)


def _process_state(pid: int | None) -> dict[str, Any] | None:
    if pid is None:
        return None
    stat_path = Path("/proc") / str(pid) / "stat"
    if not stat_path.is_file():
        return {"pid": pid, "running": False}
    fields = stat_path.read_text(encoding="utf-8").split()
    return {"pid": pid, "running": True, "state": fields[2]}


def _active_stage(output_root: Path) -> Path | None:
    stages = sorted(
        path for path in output_root.glob(".staging-*") if path.is_dir() and not path.is_symlink()
    )
    return stages[-1] if stages else None


def progress(
    chunks_path: Path,
    output_root: Path,
    cache_root: Path,
    pid: int | None = None,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    """Return an exact cache/staging snapshot; this function never writes artifacts."""
    config = _read_json(config_path)
    candidate = _decision_candidate(config)
    manifest = _read_json(chunks_path)
    grouped = _validate_chunks(config, manifest)
    stage = _active_stage(output_root)
    dimension = config["matrix"]["dimension"]
    active_pointer = output_root / config["matrix"]["active_pointer_file_name"]
    active_root: Path | None = None
    if active_pointer.is_file():
        pointer = _read_json(active_pointer)
        generation_id = pointer.get("generation_id")
        if isinstance(generation_id, str):
            candidate_root = output_root / "generations" / generation_id
            if candidate_root.is_dir() and not candidate_root.is_symlink():
                active_root = candidate_root
    inspection_root = stage or active_root
    locales: list[dict[str, Any]] = []
    for locale in config["input"]["locales"]:
        compatibility = _compatibility_key(config, manifest, candidate, locale)
        cached = sum(
            _read_cached_vector(cache_root, compatibility, _passage(chunk), dimension) is not None
            for chunk in grouped[locale]
        )
        staged = bool(
            inspection_root
            and (inspection_root / locale / config["matrix"]["locale_manifest_file_name"]).is_file()
        )
        locales.append(
            {
                "locale": locale,
                "chunk_count": len(grouped[locale]),
                "cached_vectors": cached,
                "staged": staged,
                "state": (
                    "complete"
                    if active_root and staged
                    else "staged"
                    if staged
                    else "embedding_or_waiting"
                ),
            }
        )
    complete = sum(entry["staged"] for entry in locales)
    cache_complete = sum(entry["cached_vectors"] for entry in locales)
    total = sum(entry["chunk_count"] for entry in locales)
    result: dict[str, Any] = {
        "state": (
            "activated" if active_pointer.is_file() else "building" if stage else "not_started"
        ),
        "stage": str(stage) if stage else None,
        "active_pointer": str(active_pointer) if active_pointer.is_file() else None,
        "locales_complete": complete,
        "locales_total": len(locales),
        "cached_vectors": cache_complete,
        "total_vectors": total,
        "locales": locales,
    }
    process = _process_state(pid)
    if process is not None:
        result["process"] = process
    return result


def _render(snapshot: dict[str, Any]) -> str:
    lines = [
        f"RAG generation: {snapshot['state']}",
        f"Locales: {snapshot['locales_complete']}/{snapshot['locales_total']}; "
        f"cached vectors: {snapshot['cached_vectors']}/{snapshot['total_vectors']}",
    ]
    process = snapshot.get("process")
    if process:
        state = process.get("state", "stopped") if process["running"] else "stopped"
        lines.append(f"Process {process['pid']}: {state}")
    for locale in snapshot["locales"]:
        marker = locale["state"] if locale["staged"] else "in progress / queued"
        lines.append(
            f"  {locale['locale']}: {marker}; cache {locale['cached_vectors']}/{locale['chunk_count']}"
        )
    if snapshot["state"] == "building":
        lines.append(
            "The active index has not changed; activation happens only after every locale validates."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--config", default=CONFIG_PATH, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Refresh until interrupted.")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    while True:
        snapshot = progress(args.chunks, args.output_root, args.cache_root, args.pid, args.config)
        print(
            (
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
                if args.json
                else _render(snapshot)
            ),
            flush=True,
        )
        if not args.watch:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
