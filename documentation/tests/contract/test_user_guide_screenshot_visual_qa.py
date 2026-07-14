from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
MATRIX = DOCUMENTATION_ROOT / "config/user-guide-screenshot-matrix-0.9.1.json"
VISUAL_QA = DOCUMENTATION_ROOT / "config/user-guide-screenshot-visual-qa-0.9.1.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_user_guide_screenshot_visual_qa_records_complete_review_scope() -> None:
    matrix = _json(MATRIX)
    qa = _json(VISUAL_QA)
    matrix_rows = matrix["matrix"]
    scenario_ids = {scenario["scenario_id"] for scenario in matrix["scenarios"]}

    assert qa["schema_version"] == 1
    assert qa["target_bpm_version"] == "0.9.1"
    assert qa["backlog_item"] == "BPM091-M5-05"
    assert qa["source_matrix"] == "documentation/config/user-guide-screenshot-matrix-0.9.1.json"
    assert qa["status"] in {"accepted", "blocked"}
    assert qa["qa_artifacts"]["contact_sheet"].endswith("contact-sheet.png")
    assert qa["qa_artifacts"]["ocr_directory"].endswith("visual-qa/ocr/")
    assert set(qa["review_methods"]) >= {
        "manual contact-sheet review of all 36 localized User Guide screenshots",
        "matrix reconciliation against locale, scenario, viewport, theme, filename, and asset path",
    }

    coverage = qa["coverage"]
    assert coverage["rows_expected"] == len(matrix_rows)
    assert coverage["rows_reviewed"] == len(matrix_rows)
    assert coverage["locales_reviewed"] == list(LOCALES)
    assert set(coverage["scenarios_reviewed"]) == scenario_ids
    assert set(coverage["viewports_reviewed"]) == {row["viewport"] for row in matrix_rows}
    assert set(coverage["themes_reviewed"]) == {row["theme"] for row in matrix_rows}


def test_user_guide_screenshot_visual_qa_blocks_release_until_locale_findings_close() -> None:
    qa = _json(VISUAL_QA)
    criteria = qa["criteria"]

    for criterion in (
        "asset_presence",
        "dimensions_match_matrix",
        "readability",
        "clipped_labels",
        "stale_ui",
    ):
        assert criteria[criterion] == "pass"

    if qa["status"] == "accepted":
        assert qa["release_ready"] is True
        assert criteria["locale_correctness"] == "pass"
        assert criteria["non_english_accidental_english"] == "pass"
        assert qa["release_blockers"] == []
        return

    assert qa["status"] == "blocked"
    assert qa["release_ready"] is False
    assert criteria["locale_correctness"] == "blocked"
    assert criteria["non_english_accidental_english"] == "blocked"
    assert len(qa["release_blockers"]) >= 1
    if cleanup := qa.get("source_terminology_cleanup"):
        assert cleanup["backlog_item"] == "BPM091-M7-03"
        assert cleanup["status"] == "accepted"
        assert cleanup["evidence"] == (
            "documentation/config/locale-anglicism-replacement-0.9.1.json"
        )
        assert qa["blocked_by_backlog_items"] == ["BPM091-M7-05"]
    else:
        assert {"BPM091-M7-01", "BPM091-M7-03", "BPM091-M7-05"} <= set(
            qa["blocked_by_backlog_items"]
        )
    blocker_locales = {blocker["locale"] for blocker in qa["release_blockers"]}
    assert {"de", "fr", "es-ES", "zh-CN"} <= blocker_locales
    for blocker in qa["release_blockers"]:
        assert blocker["severity"] == "release-blocker"
        assert blocker["examples"]
        assert blocker["affected_scenarios"]
    assert qa["required_follow_up"]
