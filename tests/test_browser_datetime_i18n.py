from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_library_and_editor_timestamps_use_browser_locale_formatters():
    workspace_source = _read("app/static/profiles_workspace.js")
    library_source = _read("app/static/profiles_library_bootstrap.js")
    review_source = _read("app/static/profiles_review.js")

    assert "new Intl.DateTimeFormat(getCurrentLang(), {" in workspace_source
    assert "new Intl.DateTimeFormat(getCurrentLang(), {" in library_source
    assert (
        "new Intl.DateTimeFormat(documentRef.documentElement.lang || undefined, {"
        in review_source
    )
    for source in (workspace_source, library_source, review_source):
        assert 'dateStyle: "medium"' in source
        assert 'timeStyle: "short"' in source


def test_editor_initial_metadata_does_not_server_render_raw_updated_timestamp():
    template = _read("app/templates/profiles/_page_editor_chrome.html")

    assert "initial_profile.updated_at" not in template
    assert 'id="current-meta"' in template
    assert 't("profiles.meta_updated").replace("{value}", formatTimestamp(profile.updated_at))' in _read(
        "app/static/profiles_workspace.js"
    )


def test_conflict_copy_timestamp_uses_locale_formatter_instead_of_manual_utc_slice():
    workspace_source = _read("app/static/profiles_workspace.js")

    assert "const stamp = formatTimestamp(new Date());" in workspace_source
    assert '.toISOString().slice(0, 19).replace("T", " ")' not in workspace_source
