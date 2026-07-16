from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
DITA_ROOT = DOC_ROOT / "src" / "dita"
REVIEW = DOC_ROOT / "config" / "visible-english-prose-review-0.9.1.json"

LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
BLOCK_RE = re.compile(
    r"<(?P<tag>title|navtitle|shortdesc|p|cmd|entry|note|figdesc|alt)\b[^>]*>"
    r"(?P<body>.*?)</(?P=tag)>",
    re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
STRONG_ENGLISH = {
    "the", "this", "that", "these", "those", "use", "open", "close", "select", "choose",
    "expected", "result", "before", "after", "when", "while", "where", "with", "without",
    "from", "into", "through", "between", "should", "must", "cannot", "does", "not", "and",
    "your", "profile", "setting", "settings", "user", "guide", "topic", "workflow", "review",
    "save", "export", "import", "return", "continue", "confirm", "current", "available", "only",
}
TECHNICAL_RESIDUAL_MARKERS = (
    "$BPM_BASE_URL",
    "/api/",
    "ProfileRead",
    "Expected object with policy mappings",
    "added_from_cis",
)
GERMAN_FALSE_POSITIVE_PATHS = {
    "documentation/src/dita/de/admin/admin-task-gate-control-product-startup.dita",
    "documentation/src/dita/de/admin/admin-troubleshoot-wsl-networking-dependencies.dita",
    "documentation/src/dita/de/user/ug-concept-schema-aware-behavior.dita",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _blocks(path: Path) -> list[tuple[str, str]]:
    source = path.read_text(encoding="utf-8")
    return [
        (
            match.group("tag"),
            html.unescape(" ".join(TAG_RE.sub(" ", match.group("body")).split())),
        )
        for match in BLOCK_RE.finditer(source)
    ]


def _source_paths(locale: str) -> list[Path]:
    return sorted(
        path
        for path in (DITA_ROOT / locale).rglob("*")
        if path.suffix in {".dita", ".ditamap"}
    )


def test_visible_english_review_records_complete_source_scope() -> None:
    review = _json(REVIEW)

    assert review["schema_version"] == 1
    assert review["backlog_item"] == "BPM091-M10-06"
    assert review["target_bpm_version"] == "0.9.1"
    assert review["status"] == "accepted"
    assert review["scope"]["locales"] == list(LOCALES)
    assert set(review["scope"]["visible_elements"]) == {
        "title", "navtitle", "shortdesc", "p", "cmd", "entry", "note", "figdesc", "alt"
    }

    actual_counts = {locale: len(_source_paths(locale)) for locale in LOCALES}
    assert actual_counts == review["scope"]["source_files_per_locale"]
    assert sum(actual_counts.values()) == review["scope"]["source_files_reviewed"] == 805


def test_visible_english_review_has_no_release_blocking_exact_peer_carryover() -> None:
    review = _json(REVIEW)
    allowed = {
        (entry["locale"], entry["source"], entry["text"])
        for entry in review["reviewed_exact_peer_homographs"]
    }
    actual_allowed: set[tuple[str, str, str]] = set()
    blocking: list[tuple[str, str, str]] = []

    for locale in LOCALES:
        for local_path in _source_paths(locale):
            relative = local_path.relative_to(DITA_ROOT / locale)
            english_path = DITA_ROOT / "en" / relative
            if not english_path.exists():
                continue
            local_blocks = _blocks(local_path)
            english_blocks = _blocks(english_path)
            if len(local_blocks) != len(english_blocks):
                continue
            for local_block, english_block in zip(local_blocks, english_blocks, strict=True):
                if local_block != english_block or not re.search(r"[A-Za-z]{2}", local_block[1]):
                    continue
                source = local_path.relative_to(ROOT).as_posix()
                item = (locale, source, local_block[1])
                if item in allowed:
                    actual_allowed.add(item)
                elif len(WORD_RE.findall(local_block[1])) >= 6 and len(local_block[1]) >= 35:
                    blocking.append(item)

    assert blocking == []
    assert actual_allowed == allowed
    assert review["result"]["release_blocking_exact_peer_carryover_blocks"] == 0


def test_visible_english_review_residual_candidates_are_technical_or_false_positive() -> None:
    review = _json(REVIEW)
    actual: dict[str, int] = {}

    for locale in LOCALES:
        candidates = []
        for path in _source_paths(locale):
            if path.suffix != ".dita":
                continue
            for _tag, text in _blocks(path):
                words = [word.casefold() for word in WORD_RE.findall(text)]
                strong = sum(word in STRONG_ENGLISH for word in words)
                if len(words) >= 6 and strong >= 3:
                    candidates.append((path, text))
        actual[locale] = len(candidates)
        for path, text in candidates:
            source = path.relative_to(ROOT).as_posix()
            assert (
                any(marker in text for marker in TECHNICAL_RESIDUAL_MARKERS)
                or source in GERMAN_FALSE_POSITIVE_PATHS
            ), (
                path,
                text,
            )

    assert actual == review["result"]["remaining_high_signal_candidates"]
    assert sum(actual.values()) == review["result"]["remaining_high_signal_candidate_total"] == 28


def test_visible_english_review_has_no_translation_markers_or_baseline_sentences() -> None:
    review = _json(REVIEW)
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for locale in LOCALES
        for path in _source_paths(locale)
    )

    for marker in ("BPMTOKEN", "ZXQTOKEN", "BPMSEG", "BPMFRAG"):
        assert marker not in combined
    for sentence in (
        "Use the current liveness and readiness probes",
        "A successful health or readiness response does not authenticate callers",
        "Export has no ETag, precondition header, bulk endpoint",
        "If import, validation, read-back, or export evidence differs",
    ):
        assert sentence not in combined

    assert review["result"]["temporary_translation_markers_remaining"] == 0
    assert review["closure"] == {
        "release_blocker": "DOC091-M10-VISIBLE-ENGLISH",
        "status": "closed",
        "next_backlog_item": "BPM091-M10-07",
        "drift_gate_owner": "BPM091-M10-08",
    }
