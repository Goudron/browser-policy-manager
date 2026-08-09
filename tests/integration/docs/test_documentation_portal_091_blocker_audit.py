from __future__ import annotations

from tests.docs_index import doc_path_from_index


def test_documentation_portal_091_blocker_audit_is_indexed_and_bounded():
    audit = doc_path_from_index(
        "architecture/documentation-portal-blocker-audit-0.9.1.md",
        status="audit",
    ).read_text(encoding="utf-8")

    assert "Backlog item: `BPM091-M2-01`" in audit
    assert "Historical 0.9.0 architecture contracts" in audit
    assert "regenerated through the documentation build pipeline" in " ".join(audit.split())
    assert "does not approve broad 0.9.0-to-0.9.1 replacement" in " ".join(audit.split())

    for gap in range(1, 9):
        assert f"`DOC091-AUDIT-G{gap:02d}`" in audit

    for required_surface in (
        "app/documentation/site/manifest.json",
        "app/documentation/site/ui-target-map.json",
        "documentation/assets/screenshots/{locale}/",
        "documentation/assets/theme/bpm-docs.css",
        "documentation/config/search-facets-filters-0.9.0.json",
        "documentation/tools/build_docs.py",
        "app/static/profiles_all_settings_list.js",
    ):
        assert required_surface in audit


def test_documentation_portal_091_blocker_audit_routes_gaps_to_backlog_tasks():
    audit = doc_path_from_index(
        "architecture/documentation-portal-blocker-audit-0.9.1.md",
        status="audit",
    ).read_text(encoding="utf-8")

    for task_id in (
        "BPM091-M2-02",
        "BPM091-M2-03",
        "BPM091-M2-04",
        "BPM091-M2-05",
        "BPM091-M2-06",
        "BPM091-M2-07",
        "BPM091-M2-08",
        "BPM091-M4-01",
        "BPM091-M4-03",
        "BPM091-M4-05",
        "BPM091-M5-02",
        "BPM091-M6-05",
        "BPM091-M7-03",
        "BPM091-M8-03",
        "BPM091-M12-05",
    ):
        assert f"`{task_id}`" in audit
