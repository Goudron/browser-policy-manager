import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TARGET_VERSION = "0.9.5.1"
RELEASE_SECTION_HEADING_RE = re.compile(
    r"^#{1,6}\s*(?:changelog|release (?:history|notes)|what['’]s new)\b",
    re.IGNORECASE | re.MULTILINE,
)
RELEASE_PLACEHOLDER_RE = re.compile(
    r"^(?:release )?(?:status|planned(?: release work)?|completion)\s*:",
    re.IGNORECASE | re.MULTILINE,
)


def test_readme_documents_firefox_policies_contract_and_schema_choice():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "BPM imports and exports the Firefox Enterprise `policies.json` shape" in readme
    assert "`POST /api/profiles/import/firefox/policies.json`" in readme
    assert "`GET /api/export/profiles/{id}/firefox/policies.json`" in readme
    assert "Choose the Firefox schema channel before import." in readme
    assert "The selected `schema_version` controls" in readme
    assert '"schema_version": "esr-140.13"' in readme
    assert '"policies": {' in readme


def test_readme_states_current_schema_support_and_manual_conversion_boundary():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    for channel in ("release-153", "esr-153.0", "esr-140.13", "esr-115.39"):
        assert f"`{channel}`" in readme
    assert "limited security support through March 2027 and a scheduled recheck" in readme
    assert "BPM recommends it for profiles using either older ESR channel." in readme
    assert "Select a supported target to create a read-only conversion preview" in normalized_readme
    assert "explicitly confirm before BPM updates the saved profile" in normalized_readme
    assert "BPM leaves the profile unchanged" in normalized_readme


def test_readme_is_version_neutral_and_excludes_maintainer_implementation_details():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert TARGET_VERSION not in readme
    assert "0.9.4" not in readme
    assert "0.9.3" not in readme
    assert RELEASE_SECTION_HEADING_RE.search(readme) is None
    assert RELEASE_PLACEHOLDER_RE.search(readme) is None
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
