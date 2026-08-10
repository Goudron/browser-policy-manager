from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT_PATH = doc_path_from_index(
    "documentation-audience-status-leakage-audit-0.9.2.md", status="audit"
)


def test_m10_audience_and_status_audit_records_all_required_decisions():
    audit = AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `BPM092-M10-01`" in audit
    for guide in ("CIS Guide", "Firefox Policy Guide", "Administrator/DevOps Guide"):
        assert guide in audit
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in audit
    for disposition in (
        "**remove**",
        "**rewrite as current support boundary**",
        "**move to maintainer docs**",
        "**retain as genuine API-integrator content**",
    ):
        assert disposition in audit


def test_m10_audience_and_status_audit_preserves_follow_up_scope():
    audit = AUDIT_PATH.read_text(encoding="utf-8")

    for topic in (
        "cis/cis-concept-orientation.dita",
        "admin/admin-concept-integration-audience.dita",
        "admin/admin-troubleshoot-documentation-portal-build-links.dita",
        "admin/admin-troubleshoot-failed-startup-probes.dita",
        "firefox/fx-concept-release-esr-differences.dita",
    ):
        assert f"`{topic}`" in audit
    assert "BPM092-M10-02" in audit
    assert "BPM092-M10-03" in audit
