from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "docs/architecture/compact-ui-user-documentation-review-0.9.2.md"
EVIDENCE = ROOT / "docs/architecture/compact-ui-screenshot-refresh-0.9.2.md"
MATRIX = ROOT / "documentation/config/user-guide-screenshot-matrix-0.9.1.json"
LOCALES = {"en", "ru", "de", "zh-CN", "fr", "es-ES"}
SCENARIOS = {
    "library-overview",
    "guided-editor-overview",
    "all-settings-review",
    "json-editor",
    "compare-profiles",
}

pytestmark = pytest.mark.docs_contract


def test_compact_ui_refresh_uses_only_invalidated_matrix_scenarios() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    rows = [row for row in matrix["matrix"] if row["scenario_id"] in SCENARIOS]

    assert len(rows) == len(SCENARIOS) * len(LOCALES)
    assert {row["scenario_id"] for row in rows} == SCENARIOS
    assert {row["locale"] for row in rows} == LOCALES
    for row in rows:
        asset = ROOT / row["asset_path"]
        assert asset.is_file(), row["id"]
        assert asset.stat().st_size > 1024, row["id"]


def test_compact_ui_refresh_record_closes_screenshot_blocker_without_faking_locale_signoff() -> None:
    review = REVIEW.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")

    assert review.count("recaptured M11-03") == len(SCENARIOS)
    assert "automated capture complete; release review remains governed by locale sign-off" in evidence
    assert "30 captured of 30 expected rows" in evidence
    assert "final locale/editorial acceptance remains governed by the release gate" in review
