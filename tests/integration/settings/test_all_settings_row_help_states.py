from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = REPO_ROOT / "app/static"


def test_search_no_link_indicators_are_noninteractive_and_localized():
    source = (STATIC_ROOT / "profiles_settings_search.js").read_text(encoding="utf-8")

    assert 'const indicator = documentRef.createElement("span")' in source
    assert 'indicator.setAttribute("role", "img")' in source
    assert 'indicator.setAttribute("aria-disabled", "true")' in source
    assert "indicator.dataset.settingsEntryHelpDisposition = disposition" in source
