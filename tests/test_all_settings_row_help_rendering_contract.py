from pathlib import Path

from tests.web_profiles_page_helpers import static_source, template_source

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_all_settings_row_help_links_use_manifest_resolved_sibling_controls():
    context = (REPO_ROOT / "app/web/profiles_context.py").read_text(encoding="utf-8")
    catalogs = static_source("profiles_catalogs.js")
    bootstrap = static_source("profiles_bootstrap_core.js")
    rows = static_source("profiles_all_settings_list.js")
    template = template_source("_page_catalog_scripts.html")

    assert "resolve_all_settings_row_help_links" in context
    assert 'id="all-settings-row-help-links"' in template
    assert 'readEmbeddedJson(documentRef, "all-settings-row-help-links")' in catalogs
    assert "documentationRowHelpLinks: catalogs.allSettingsRowHelpLinks || {}" in bootstrap
    for snippet in (
            "function documentationTargetId(entry)",
            "function rowHelpState(entry)",
            "function renderRowHelp(entry, location)",
        'class="all-settings-list-row-shell${selected ? " is-selected" : ""}"',
        "data-settings-entry-select",
        'class="context-help-icon-link all-settings-row-help-link"',
        'target="_blank"',
        'rel="noopener noreferrer"',
        "data-documentation-links=",
        "data-all-settings-help-target=",
        'data-settings-entry-help-disposition="linked"',
        'if (event.target.closest("[data-all-settings-help-target]")) return;',
    ):
        assert snippet in rows


def test_all_settings_search_results_render_separate_manifest_help_links():
    search = static_source("profiles_settings_search.js")

    for snippet in (
        'shell.className = "wizard-settings-search-result-shell"',
        "shell.appendChild(button)",
        "documentationRowHelpLinks[targetId]",
        'link.className = "context-help-icon-link all-settings-row-help-link"',
        'link.dataset.allSettingsHelpLocation = "search"',
        'link.dataset.settingsEntryHelpDisposition = "linked"',
        "shell.appendChild(link)",
    ):
        assert snippet in search


def test_all_settings_row_help_layout_has_stable_reserved_columns():
    desktop = static_source("profiles_css/20-editor-wizard.css")
    responsive = static_source("profiles_css/30-responsive.css")

    assert ".all-settings-list-row-shell {" in desktop
    assert "grid-template-columns: minmax(0, 1fr) 2.75rem;" in desktop
    assert ".wizard-settings-search-result-shell {" in desktop
    assert ".all-settings-row-help-link {" in desktop
    assert ".all-settings-list-row-shell," in responsive
    assert "grid-template-columns: minmax(0, 1fr) 2.5rem;" in responsive
