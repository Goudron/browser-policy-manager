from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = REPO_ROOT / "docs/firefox_policies_json_migration_notes_2026-04-14.md"


def test_firefox_policies_migration_notes_document_breaking_export_change():
    notes = NOTES_PATH.read_text()
    readme = (REPO_ROOT / "README.md").read_text()

    assert "Firefox Enterprise `policies.json`" in notes
    assert "final wizard step" in notes
    assert "only the Firefox `policies.json` handoff file" in notes
    assert "Breaking API Change" in notes
    assert "There is no compatibility export route for BPM internal JSON/YAML" in notes

    removed_routes = [
        "GET /api/export/profiles",
        "GET /api/export/profiles/{profile_id}",
        "GET /api/export/profiles/{profile_id}?fmt=json",
        "GET /api/export/profiles/{profile_id}?fmt=yaml",
        "GET /api/export/profiles/{profile_id}.json",
        "GET /api/export/profiles/{profile_id}.yaml",
    ]
    for route in removed_routes:
        assert route in notes

    assert "GET /api/export/profiles/{profile_id}/firefox/policies.json" in notes
    assert "docs/firefox_policies_json_migration_notes_2026-04-14.md" in readme
