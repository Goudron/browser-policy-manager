from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TECHNICAL_PROCEDURES = (
    "docs/architecture/current-system-map.md",
    "docs/architecture/pytest-parallelism-decision-0.9.4.md",
    "docs/architecture/database-upgrade-matrix-0.9.5.md",
    "docs/firefox-schema-update-runbook.md",
    "docs/firefox-live-testing.md",
    "documentation/runbooks/documentation-update-for-future-epics.md",
)
REMOVED_PROCEDURE_TERMS = (
    "raw-schema",
    "raw schema",
    "marker-list",
    "marker list",
    "sync-adapter",
    "sync adapter",
    "floating-browser",
    "floating browser",
    "documentation-freeze",
    "documentation freeze",
)


def _text(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8").casefold()


def test_m11_technical_procedures_name_current_owners_and_targets() -> None:
    system_map = _text("docs/architecture/current-system-map.md")
    test_runbook = _text("docs/architecture/pytest-parallelism-decision-0.9.4.md")
    database = _text("docs/architecture/database-upgrade-matrix-0.9.5.md")
    schema = _text("docs/firefox-schema-update-runbook.md")
    browser = _text("docs/firefox-live-testing.md")
    release = _text("documentation/runbooks/documentation-update-for-future-epics.md")

    assert "native async engine" in system_map
    assert "route-specific native esm entry" in system_map
    assert "make check-profile-frontend-bundles" in system_map
    assert "exclusive primary layers" in test_runbook
    assert "make test-postgres-integration" in test_runbook
    assert "alembic" in database and "postgresql" in database
    assert "`alembic upgrade head` is the sole schema and stored-channel upgrade path" in schema
    assert "firefox_live_browsers_manifest_0_9_4.json" in browser
    assert all(channel in browser for channel in ("release", "esr153", "esr140", "esr115"))
    assert "documentation/buildlib/" in release
    assert "make docs-release-check" in release


def test_m11_technical_procedures_do_not_reintroduce_removed_workflows() -> None:
    combined = "\n".join(_text(path) for path in TECHNICAL_PROCEDURES)

    for term in REMOVED_PROCEDURE_TERMS:
        assert term not in combined
