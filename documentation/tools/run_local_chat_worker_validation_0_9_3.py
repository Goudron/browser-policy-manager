"""Run one checksum-verified, progress-visible local worker probe per BPM locale.

The report deliberately stores only outcome metadata and output digests. It is an M6 transport and
lifecycle validation, not an answer-quality or grounded-chat benchmark; M7 owns those guarantees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.ai.local_inference_worker import (  # noqa: E402
    InferenceRequest,
    InferenceResult,
    LocalInferenceWorker,
)

LOCALE_PROBES: tuple[tuple[str, str], ...] = (
    ("en", "Briefly confirm that BPM documentation is available."),
    ("ru", "Кратко подтвердите, что документация BPM доступна."),
    ("de", "Bestätigen Sie kurz, dass die BPM-Dokumentation verfügbar ist."),
    ("zh-CN", "请简要确认 BPM 文档可用。"),
    ("fr", "Confirmez brièvement que la documentation BPM est disponible."),
    ("es-ES", "Confirme brevemente que la documentación de BPM está disponible."),
)
DEFAULT_OUTPUT = REPOSITORY_ROOT / "documentation/.cache/bpm093-m6-07/runtime-validation.json"


class ValidationError(RuntimeError):
    """The one-pass real artifact probe could not produce complete safe evidence."""


def _safe_output_path(path: Path) -> Path:
    cache_root = (REPOSITORY_ROOT / "documentation/.cache").resolve()
    resolved = path.resolve()
    if cache_root not in (resolved, *resolved.parents):
        raise ValidationError("output must remain under documentation/.cache")
    return resolved


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _generate_with_progress(
    worker: LocalInferenceWorker, request: InferenceRequest, locale: str
) -> InferenceResult:
    """Wait for one real generation while reporting only worker state and elapsed time."""

    result: list[InferenceResult] = []
    failure: list[BaseException] = []

    def generate() -> None:
        try:
            result.append(worker.generate(request))
        except BaseException as error:  # Re-raise the direct worker failure below.
            failure.append(error)

    started = time.monotonic()
    thread = threading.Thread(target=generate, daemon=True)
    thread.start()
    while thread.is_alive():
        thread.join(timeout=5)
        if thread.is_alive():
            elapsed = round(time.monotonic() - started, 1)
            print(
                f"M6-07: {locale}: worker phase={worker.health().state}, elapsed={elapsed}s",
                flush=True,
            )
    if failure:
        raise failure[0]
    if len(result) != 1:
        raise ValidationError(f"{locale}: worker returned no result")
    return result[0]


def run(output_path: Path) -> dict[str, Any]:
    """Run a single sequential six-locale transport probe and write a digest-only report."""

    output_path = _safe_output_path(output_path)
    worker = LocalInferenceWorker.for_default_installation(enabled=True)
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    print(
        "M6-07: local worker validation: verifying artifacts and starting six locale probes",
        flush=True,
    )
    try:
        for completed, (locale, question) in enumerate(LOCALE_PROBES, start=1):
            print(
                f"M6-07: {locale}: runtime probe {completed}/{len(LOCALE_PROBES)} started",
                flush=True,
            )
            evidence = json.dumps(
                {
                    "locale": locale,
                    "source_kind": "validation",
                    "text": "BPM documentation is available.",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            result = _generate_with_progress(
                worker, InferenceRequest(locale, question, evidence), locale
            )
            encoded = result.text.encode("utf-8")
            if (
                not result.text.strip()
                or "<think" in result.text.lower()
                or "</think>" in result.text.lower()
            ):
                raise ValidationError(f"{locale}: unsafe or empty display output")
            if result.locale != locale:
                raise ValidationError(f"{locale}: worker returned a different locale")
            results.append(
                {
                    "locale": locale,
                    "status": "passed",
                    "output_characters": len(result.text),
                    "output_utf8_bytes": len(encoded),
                    "output_sha256": hashlib.sha256(encoded).hexdigest(),
                }
            )
            print(
                f"M6-07: {locale}: runtime probe {completed}/{len(LOCALE_PROBES)} passed",
                flush=True,
            )
    finally:
        worker.unload()
        print("M6-07: worker unloaded", flush=True)

    report = {
        "backlog_item": "BPM093-M6-07",
        "status": "passed",
        "locale_results": results,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "report_boundary": "No prompts, evidence, model output, paths, or raw runtime diagnostics are retained.",
    }
    if len(results) != len(LOCALE_PROBES):
        raise ValidationError("locale matrix is incomplete")
    _write_report(output_path, report)
    print(
        f"M6-07: completed {len(results)}/{len(LOCALE_PROBES)} locale probes; digest-only report written",
        flush=True,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    command = subparsers.add_parser("run", help="run the sequential six-locale local worker probe")
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    try:
        run(arguments.output)
    except ValidationError as error:
        print(f"M6-07: failed: {error}", file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
