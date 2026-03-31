from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_JS = REPO_ROOT / "app" / "static" / "profiles_workspace.js"


def test_workspace_update_download_links_sets_firefox_policies_href_for_saved_profile():
    source = WORKSPACE_JS.read_text(encoding="utf-8")

    assert (
        "firefoxPoliciesLink.href = `/api/export/profiles/${getCurrentId()}/firefox/policies.json`;"
        in source
    )
    assert "wizardExportFirefoxPoliciesEl.href = firefoxPoliciesLink.href;" in source


def test_workspace_update_download_links_resets_firefox_policies_href_when_export_unavailable():
    source = WORKSPACE_JS.read_text(encoding="utf-8")

    assert 'const firefoxPoliciesLink = documentRef.getElementById("download-firefox-policies");' in source
    assert "firefoxPoliciesLink.href = \"#\";" in source
    assert "wizardExportFirefoxPoliciesEl.href = \"#\";" in source
