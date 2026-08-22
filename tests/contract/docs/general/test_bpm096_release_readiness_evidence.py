"""Release-history and documentation-drift closeout guard for BPM096-M11-09."""

from __future__ import annotations

from pathlib import Path

from tests.docs_index import doc_path_from_index

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "docs/architecture/release-readiness-evidence-0.9.6.md"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"
BACKLOG = ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def test_bpm096_readiness_evidence_is_indexed_and_preserves_handoff_boundary() -> None:
    assert (
        doc_path_from_index("architecture/release-readiness-evidence-0.9.6.md", status="active")
        == EVIDENCE
    )
    source = EVIDENCE.read_text(encoding="utf-8")
    for required in (
        "BPM096-M11-09",
        "not a release, tag, push, or CI result",
        "BPM096-M11-01` through `BPM096-M11-08",
        "BPM096-M11-10",
        "BPM096-M11-11",
        "Schema, CIS, locale, Administrator/DevOps, update, and release",
    ):
        assert required in source


def test_bpm096_current_surfaces_close_old_workflow_and_release_claim_drift() -> None:
    changelog = CHANGELOG.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert changelog.index("## 0.9.6") < changelog.index("## 0.9.5.1")
    assert "Reviewed commit and CI handoff remain." in changelog
    assert "0.9.5.1" not in readme
    assert "eight focused task-first steps" in readme
    assert "Unsaved drafts stay in the guided editor" not in readme
    assert "Named clone drafts" not in readme
    assert "schema selector" not in readme.casefold()

    for locale in LOCALES:
        source = (
            ROOT
            / "documentation/src/dita"
            / locale
            / "admin/admin-reference-minimum-system-requirements.dita"
        ).read_text(encoding="utf-8")
        assert "0.9.5.1" not in source


def test_bpm096_backlog_records_the_documentation_closeout() -> None:
    source = BACKLOG.read_text(encoding="utf-8")
    assert "### BPM096-M11-09 — Changelog, README, index, and drift closeout" in source
