from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
HUMAN_QA = DOC_ROOT / "config" / "locale-human-qa-0.9.1.json"
VISUAL_QA = DOC_ROOT / "config" / "user-guide-screenshot-visual-qa-0.9.1.json"
MATRIX = DOC_ROOT / "config" / "user-guide-screenshot-matrix-0.9.1.json"
SOURCE_I18N = ROOT / "app" / "i18n_src"
RUNTIME_I18N = ROOT / "app" / "i18n"

LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
EXPECTED_CLOSED_BLOCKERS = {
    "SHOT-QA-LOC-DE-001",
    "SHOT-QA-LOC-FR-001",
    "SHOT-QA-LOC-ES-001",
    "SHOT-QA-LOC-ZH-001",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _localized_catalog_text(locale: str) -> str:
    chunks: list[str] = []
    for path in sorted((SOURCE_I18N / locale).glob("*.json")):
        chunks.extend(value for value in _json(path).values() if isinstance(value, str))
    chunks.extend(
        value for value in _json(RUNTIME_I18N / f"{locale}.json").values() if isinstance(value, str)
    )
    return "\n".join(chunks)


def test_locale_human_qa_records_accepted_screenshot_release_scope() -> None:
    qa = _json(HUMAN_QA)
    matrix = _json(MATRIX)

    assert qa["schema_version"] == 1
    assert qa["backlog_item"] == "BPM091-M7-05"
    assert qa["target_bpm_version"] == "0.9.1"
    assert qa["status"] == "accepted"
    assert qa["locales"] == list(LOCALES)
    assert qa["screenshot_visual_qa"] == (
        "documentation/config/user-guide-screenshot-visual-qa-0.9.1.json"
    )
    assert qa["capture_report"].endswith("user-guide-screenshots-0.9.1.json")
    assert qa["contact_sheet"].endswith("contact-sheet.png")
    assert len(matrix["matrix"]) == 36
    assert set(qa["blocked_items_closed"]) == EXPECTED_CLOSED_BLOCKERS
    assert "Broader non-screenshot locale phrasing debt" in " ".join(
        qa["known_not_closed_by_this_item"]
    )


def test_locale_human_qa_accepts_visual_qa_and_closes_blockers() -> None:
    qa = _json(HUMAN_QA)
    visual = _json(VISUAL_QA)

    assert visual["status"] == "accepted"
    assert visual["release_ready"] is True
    assert visual["release_blockers"] == []
    assert visual["required_follow_up"] == []
    assert visual["screenshot_regeneration"]["backlog_item"] == "BPM091-M7-05"
    assert visual["screenshot_regeneration"]["rows_captured"] == 36
    assert set(visual["coverage"]["locales_reviewed"]) == {"en", *LOCALES}
    assert set(visual["screenshot_regeneration"]["last_reviewed_locales"]) == set(LOCALES)
    assert qa["status"] == visual["screenshot_regeneration"]["status"]


def test_locale_human_qa_records_each_non_english_locale_result() -> None:
    qa = _json(HUMAN_QA)

    assert set(qa["locale_results"]) == set(LOCALES)
    for locale, result in qa["locale_results"].items():
        assert result["status"] == "accepted", locale
        assert result["remaining_english"] == "allowlisted only in reviewed surfaces"
        assert result["notes"], locale


def test_locale_human_qa_forbidden_visible_fragments_do_not_return() -> None:
    qa = _json(HUMAN_QA)

    for finding in qa["fixed_visible_findings"]:
        locale = finding["locale"]
        text = _localized_catalog_text(locale)
        assert finding["source_refs"], locale
        assert finding["verification"], locale
        for fragment in finding["examples_before"]:
            assert fragment not in text, (locale, fragment)


def test_locale_human_qa_remaining_english_is_allowlisted() -> None:
    qa = _json(HUMAN_QA)
    visual = _json(VISUAL_QA)

    visual_allowlist = set(visual["allowlisted_english"])
    categories = {entry["category"] for entry in qa["remaining_allowlisted_rationale"]}
    assert categories <= {
        "brand",
        "abbreviation",
        "schema channel identifier",
        "policy identifier",
        "managed preference identifier",
        "command/path/API",
    }
    for entry in qa["remaining_allowlisted_rationale"]:
        term = entry["term"]
        assert entry["rationale"]
        assert term in visual_allowlist or entry["category"] in {
            "policy identifier",
            "managed preference identifier",
        }
