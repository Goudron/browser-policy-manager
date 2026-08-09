from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_readme_documents_firefox_policies_contract_and_schema_choice():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "BPM imports and exports the Firefox Enterprise `policies.json` shape" in readme
    assert "`POST /api/profiles/import/firefox/policies.json`" in readme
    assert "`GET /api/export/profiles/{id}/firefox/policies.json`" in readme
    assert "Choose the Firefox schema channel before import." in readme
    assert "The selected `schema_version` controls" in readme
    assert '"schema_version": "esr-140.13"' in readme
    assert '"policies": {' in readme


def test_readme_is_version_neutral_and_excludes_maintainer_implementation_details():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "0.9.4" not in readme
    assert "0.9.3" not in readme
    assert "documentation/src/dita/" not in readme
    assert "app/schemas/policies/" not in readme
    assert "app/i18n/" not in readme
    assert "python -m venv .venv" not in readme
    assert "pip install ." not in readme
    assert "make dev" not in readme
    assert "future work" not in readme.lower()
    assert "The primary UI source language is English." in readme
    assert "BPM is available in these locales:" in readme
    for entrypoint in ("/profiles", "/help/", "/docs"):
        assert entrypoint in readme
