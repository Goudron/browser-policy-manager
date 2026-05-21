from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_firefox_policies_contract_and_schema_choice():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "BPM imports and exports the Firefox Enterprise `policies.json` shape" in readme
    assert "`POST /api/profiles/import/firefox/policies.json`" in readme
    assert "`GET /api/export/profiles/{id}/firefox/policies.json`" in readme
    assert "Choose the Firefox schema channel before import." in readme
    assert "The selected `schema_version` controls" in readme
    assert '"schema_version": "esr-140.11"' in readme
    assert '"policies": {' in readme
