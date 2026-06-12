from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bpm087_m2_04_decision_removes_profile_comparison_from_existing_surfaces() -> None:
    decision_note = (
        REPO_ROOT / "docs" / "architecture" / "profile-comparison-entrypoint-audit.md"
    ).read_text(encoding="utf-8")
    normalized_decision_note = " ".join(decision_note.split())
    backlog = (
        REPO_ROOT
        / "docs"
        / "bpm_0_8_7_profile_comparison_clone_owner_cleanup_backlog_2026-06-05.md"
    ).read_text(encoding="utf-8")

    assert "## BPM087-M2-04 Comparison Ownership Decision" in decision_note
    assert (
        "Profile comparison must be removed from every existing product surface and "
        "reintroduced only through"
    ) in normalized_decision_note
    assert "Library keeps a single general navigation control" in decision_note
    assert "opens `/profiles/compare`" in decision_note
    assert "Editor/workspace routes must also retire" in decision_note
    assert (
        "Existing internal equality checks used for wizard dirty detection, preset matching, "
        "or search-engine helper logic are not profile comparison entrypoints"
    ) in normalized_decision_note
    assert "`/profiles/compare` becomes the only profile comparison workflow" in backlog
    assert "Milestone 4A: Remove Comparison From Editor And Workspace" in backlog
