from __future__ import annotations

from bs4 import BeautifulSoup

from app.main import app
from tests.support import build_profile_payload, make_test_client
from tests.web_profiles_page_helpers import static_source, template_source


def test_all_settings_route_renders_triage_mode_controls_inside_current_surface():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="All Settings Triage Contract"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/settings")
    soup = BeautifulSoup(response.text, "html.parser")

    assert response.status_code == 200
    assert soup.select_one("#settings-panel")
    assert soup.select_one("#all-settings-review-panel")
    assert soup.select_one("#all-settings-list-panel")
    assert soup.select_one("#all-settings-detail-panel")

    mode_bar = soup.select_one("[data-settings-mode-bar]")
    assert mode_bar is not None
    assert mode_bar.get("role") == "group"

    mode_buttons = mode_bar.select("[data-settings-mode]")
    assert [button["data-settings-mode"] for button in mode_buttons] == [
        "review",
        "configured",
        "catalog",
    ]
    assert mode_buttons[0].get("aria-pressed") == "true"
    assert [button.get("aria-pressed") for button in mode_buttons[1:]] == ["false", "false"]

    rendered_links = [
        link.get("href", "")
        for link in soup.select("a[href]")
        if "/settings" in link.get("href", "")
    ]
    assert all("/settings/review" not in href for href in rendered_links)
    assert all("/settings/configured" not in href for href in rendered_links)
    assert all("/settings/catalog" not in href for href in rendered_links)


def test_all_settings_triage_mode_contract_is_backed_by_state_and_bootstrap():
    settings_template = template_source("_page_settings_workspace.html")
    state_source = static_source("profiles_all_settings_state.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    list_source = static_source("profiles_all_settings_list.js")

    for snippet in (
        "data-settings-mode-bar",
        '("review", "profiles.settings_mode_review")',
        '("configured", "profiles.settings_mode_configured")',
        '("catalog", "profiles.settings_mode_catalog")',
    ):
        assert snippet in settings_template

    for snippet in (
        'const DEFAULT_MODE = "review";',
        "activeMode: normalizeMode(initialState.activeMode)",
        "function setActiveMode(mode)",
        "setActiveMode,",
    ):
        assert snippet in state_source

    for snippet in (
        "function readAllSettingsModeFromUrl()",
        "function replaceAllSettingsModeUrl(mode)",
        'params.set("settingsMode", mode);',
        'params.delete("settingsMode");',
        'documentRef.querySelectorAll("[data-settings-mode]")',
        "function syncAllSettingsModeButtons()",
        'reviewPanel.hidden = activeMode !== "review";',
        "allSettingsCatalogAdvancedEl,",
        'allSettingsCatalogAdvancedEl.hidden = activeMode !== "catalog" && !focusOpen;',
        'allSettingsRouteState.setActiveMode(button.dataset.settingsMode || "review");',
        'allSettingsRouteState.setActiveFilter("all");',
        "onModeChange: (mode, options = {}) => {",
        "if (options.updateUrl) {",
        "allSettingsList?.render?.();",
        "syncAllSettingsModeButtons();",
    ):
        assert snippet in bootstrap_source

    for snippet in (
        "entryMatchesReview(entry, reviewKind)",
        'reviewKind === "cis-review"',
        "profiles.settings_review_cis_title",
        "profiles.settings_review_cis_body",
        "function renderReviewQueue(item)",
        "function renderReviewSuccessState()",
        'data-settings-review-mode="configured"',
        'data-settings-review-mode="catalog"',
        "reviewSourceLabel(entry)",
        "reviewReasonLabel(entry, reviewKind)",
        "entryNeedsReview(entry)",
    ):
        assert snippet in list_source
