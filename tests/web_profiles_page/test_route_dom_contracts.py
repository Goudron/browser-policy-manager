# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_profile_page_context_building_lives_in_dedicated_service():
    root = REPO_ROOT
    profiles_source = (root / "app" / "web" / "profiles.py").read_text(encoding="utf-8")
    context_source = (root / "app" / "web" / "profiles_context.py").read_text(
        encoding="utf-8"
    )

    assert "from app.web.profiles_context import (" in profiles_source
    assert "return build_profiles_page_context(" in profiles_source
    assert "def build_profiles_page_context(" in context_source
    assert "def resolve_request_locale(" in context_source
    assert "def resolve_profiles_asset_version(" in context_source
    assert "get_all_settings_category_catalog" in context_source
    assert "get_manual_policy_controls_catalog" in context_source
    assert "get_wizard_starter_catalog" in context_source
    assert "build_schema_channels_catalog" in context_source
    assert "get_all_settings_category_catalog" not in profiles_source
    assert "get_manual_policy_controls_catalog" not in profiles_source
    assert "get_wizard_starter_catalog" not in profiles_source
    assert "build_schema_channels_catalog" not in profiles_source


def test_profile_asset_version_wrapper_uses_current_settings(monkeypatch):
    import app.web.profiles as web_profiles

    captured = {}

    def fake_resolve(settings_obj):
        captured["settings"] = settings_obj
        return "asset-version"

    monkeypatch.setattr(web_profiles, "resolve_profiles_asset_version", fake_resolve)

    assert web_profiles._resolve_profiles_asset_version() == "asset-version"
    assert captured["settings"] is web_profiles.settings


def test_profile_editor_routes_render_wizard_shells():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Route Skeleton Profile"),
    )
    profile_id = create_response.json()["id"]

    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")
    missing_response = client.get("/profiles/999999/edit")
    missing_settings_response = client.get("/profiles/999999/settings")
    missing_json_response = client.get("/profiles/999999/json")

    assert new_response.status_code == 200
    assert edit_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert missing_response.status_code == 404
    assert missing_settings_response.status_code == 404
    assert missing_json_response.status_code == 404
    assert "<title>New profile draft — Guided editor — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Route Skeleton Profile — Guided editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        "<title>Route Skeleton Profile — All settings — Browser Policy Manager</title>"
        in settings_response.text
    )
    assert "Advanced settings" not in settings_response.text
    assert "Search mapped controls and apply policy changes without opening the JSON editor." in settings_response.text
    assert "<title>Route Skeleton Profile — JSON editor — Browser Policy Manager</title>" in json_response.text
    assert 'data-profiles-route-mode="new"' in new_response.text
    assert 'data-profiles-route-mode="edit"' in edit_response.text
    assert 'data-profiles-route-mode="settings"' in settings_response.text
    assert 'data-profiles-route-mode="json"' in json_response.text
    assert 'data-profiles-template-kind="editor"' in new_response.text
    assert 'data-profiles-template-kind="editor"' in edit_response.text
    assert 'data-profiles-template-kind="settings"' in settings_response.text
    assert 'data-profiles-template-kind="json"' in json_response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert f'data-editing-profile-id="{profile_id}"' in settings_response.text
    assert f'data-editing-profile-id="{profile_id}"' in json_response.text
    assert_contains_all(new_response.text, ('id="wizard-panel"', 'id="wizard-schema"', 'id="editor-mode-settings"'))
    assert_contains_all(edit_response.text, ('id="wizard-panel"', 'id="wizard-schema"', 'id="editor-mode-settings"'))
    assert 'id="format"' not in new_response.text
    assert 'id="format"' not in edit_response.text
    assert_contains_all(
        settings_response.text,
        (
            'id="settings-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-panel"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'id="all-settings-add-preference"',
            'data-settings-list-filter="all"',
            'data-settings-list-filter="configured"',
            'data-settings-list-filter="available"',
            'data-settings-list-filter="guided-covered"',
            'data-settings-list-filter="all-settings-only"',
            'data-settings-list-filter="invalid"',
            'data-settings-list-filter="deprecated"',
            'data-settings-list-filter="raw"',
            'data-settings-list-filter="unknown"',
            'id="settings-category-browser-access"',
            'id="settings-category-home-startup"',
            'id="settings-category-search-navigation"',
            'id="settings-category-privacy-security"',
            'id="settings-category-users-addons-sites"',
            'id="settings-category-ai-smart-features"',
            'id="settings-category-raw-unmapped"',
            'data-settings-category-link="browser-access"',
            'id="wizard-settings-search-input"',
            'id="settings-schema-shell-step-2"',
            'data-settings-nav',
            'id="settings-preferences-general"',
            'id="wizard-preferences-general-presets"',
            'id="editor-mode-guided"',
            'id="editor-mode-settings"',
            'id="editor-mode-json"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert 'id="format"' not in settings_response.text
    assert 'id="editor-panel"' not in new_response.text
    assert 'id="editor-panel"' not in edit_response.text
    assert 'id="editor"' not in new_response.text
    assert 'id="editor"' not in edit_response.text
    assert 'id="details-panel"' not in new_response.text
    assert 'id="details-panel"' not in edit_response.text
    assert_contains_all(
        json_response.text,
        (
            'id="editor-mode-guided"',
            'id="editor-mode-settings"',
            'id="editor-mode-json"',
            'id="editor-panel"',
            'id="editor"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="download-firefox-policies"',
            'rel="noopener"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="json-context-panel"' not in json_response.text
    assert 'id="json-download-strip"' not in json_response.text
    assert 'id="json-review-strip"' not in json_response.text


def test_profile_workspace_routes_smoke_dom_contracts():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Route Smoke Profile"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    assert library_response.status_code == 200
    assert new_response.status_code == 200
    assert edit_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200

    assert_contains_all(
        library_response.text,
        (
            'data-profiles-route-mode="library"',
            'data-profiles-template-kind="library"',
            'id="library-panel"',
            'id="search"',
            'id="library-schema-filter"',
            'id="library-lifecycle-filter"',
            'id="library-validation-filter"',
            'id="sort"',
            'id="order"',
            'id="create-profile-link"',
            'id="status"',
            'href="/profiles/new"',
            'id="list"',
            'id="compare-panel"',
        ),
    )
    assert 'data-editing-profile-id="' not in library_response.text
    assert 'id="overview-panel"' not in library_response.text
    assert 'id="current-name"' not in library_response.text
    assert 'id="profile-state-badge"' not in library_response.text
    assert 'id="workspace-signal"' not in library_response.text
    assert 'id="profile-clone-handoff-panel"' not in library_response.text
    assert 'id="profile-lifecycle-panel"' not in library_response.text
    assert 'id="profile-compliance-panel"' not in library_response.text
    assert 'id="wizard-panel"' not in library_response.text
    assert 'id="command-deck"' not in library_response.text
    assert 'id="editor-panel"' not in library_response.text
    for response, route_mode in ((new_response, "new"), (edit_response, "edit")):
        assert_contains_all(
            response.text,
            (
                f'data-profiles-route-mode="{route_mode}"',
                'data-profiles-template-kind="editor"',
                'id="wizard-panel"',
                'id="wizard-schema"',
                'id="wizard-starter-catalog"',
                'id="editor-mode-settings"',
            ),
        )
        assert 'id="library-panel"' not in response.text
        assert 'id="search"' not in response.text
        assert 'id="create-profile-link"' not in response.text
        assert 'id="list"' not in response.text
        assert 'id="compare-panel"' not in response.text
        assert 'id="details-panel"' not in response.text
        assert 'id="editor-panel"' not in response.text
        assert 'id="editor"' not in response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert_contains_all(
        settings_response.text,
        (
            'data-profiles-route-mode="settings"',
            'data-profiles-template-kind="settings"',
            'id="settings-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-panel"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'data-settings-list-filter="all"',
            'data-settings-list-filter="configured"',
            'data-settings-list-filter="available"',
            'data-settings-list-filter="guided-covered"',
            'data-settings-list-filter="all-settings-only"',
            'data-settings-list-filter="invalid"',
            'data-settings-list-filter="deprecated"',
            'data-settings-list-filter="raw"',
            'data-settings-list-filter="unknown"',
            'id="settings-category-browser-access"',
            'id="settings-category-home-startup"',
            'id="settings-category-search-navigation"',
            'id="settings-category-privacy-security"',
            'id="settings-category-users-addons-sites"',
            'id="settings-category-ai-smart-features"',
            'id="settings-category-raw-unmapped"',
            'id="wizard-settings-search-input"',
            'id="settings-schema-shell-step-2"',
            'data-settings-nav',
            'id="settings-preferences-general"',
            'id="wizard-preferences-general-presets"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert_contains_all(
        json_response.text,
        (
            'data-profiles-route-mode="json"',
            'data-profiles-template-kind="json"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="editor-panel"',
            'id="editor"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="json-context-panel"' not in json_response.text
    assert 'id="json-download-strip"' not in json_response.text
    assert 'id="json-review-strip"' not in json_response.text


def test_profile_library_exposes_complete_manager_control_surface():
    client = make_test_client(app)
    response = client.get("/profiles")

    assert response.status_code == 200
    assert_contains_all(
        response.text,
        (
            'id="library-schema-filter"',
            'id="library-lifecycle-filter"',
            'id="library-validation-filter"',
            'value="not_validated"',
            'id="sort"',
            'id="order"',
            'id="import-firefox-policies"',
            'id="import-firefox-policies-status"',
            'id="compare-panel"',
            'id="status"',
        ),
    )


def test_duplicate_route_marks_existing_profile_as_clone_source():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Duplicate Route Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/new?clone_from={profile_id}")

    assert response.status_code == 200
    assert 'data-profiles-route-mode="new"' in response.text
    assert f'data-clone-source-id="{profile_id}"' in response.text


def test_profile_editor_modes_explicitly_exclude_unrelated_ui_surfaces():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Mode Absence Contract Profile"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    guided_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    for token in (
        'id="wizard-panel"',
        'id="settings-panel"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
    ):
        assert token not in library_response.text

    for token in (
        'id="library-panel"',
        'id="search"',
        'id="compare-panel"',
        'id="settings-panel"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
        'id="format"',
    ):
        assert token not in guided_response.text

    for token in (
        'id="library-panel"',
        'id="compare-panel"',
        'id="wizard-panel"',
        'id="wizard-step-actions"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
        'id="format"',
    ):
        assert token not in settings_response.text

    for token in (
        'id="library-panel"',
        'id="compare-panel"',
        'id="wizard-panel"',
        'id="settings-panel"',
        'id="wizard-settings-search-input"',
        'id="settings-preferences-general"',
        'id="wizard-preferences-general-presets"',
        'id="json-context-panel"',
        'id="json-download-strip"',
        'id="json-review-strip"',
    ):
        assert token not in json_response.text


def test_shared_editor_chrome_dom_contract_is_present_across_editor_modes():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Shared Editor Chrome Contract Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    shared_tokens = (
        'id="overview-panel"',
        'id="current-name"',
        'id="profile-state-badge"',
        'id="workspace-signal"',
        'id="save"',
        'id="validate"',
        'id="profile-name"',
        'id="profile-type"',
        'id="editor-profile-id"',
        'id="overview-schema"',
        'id="validation-preview"',
        'id="overview-context"',
        'id="editor-mode-guided"',
        'id="editor-mode-settings"',
        'id="editor-mode-json"',
    )

    for response in (guided_response, settings_response, json_response):
        assert response.status_code == 200
        assert_contains_all(response.text, shared_tokens)


def test_visual_editor_routes_do_not_render_json_editor_surface():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Inline Advanced Split Profile"),
    )
    profile_id = create_response.json()["id"]

    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    assert 'class="content-grid grid gap-4 support-hidden"' not in new_response.text
    assert 'class="content-grid grid gap-4 support-hidden"' not in edit_response.text
    assert f'href="/profiles/{profile_id}/json?focus=editor"' in edit_response.text
    assert f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit"' in edit_response.text
    assert 'id="settings-panel"' in settings_response.text
    assert 'data-settings-runtime-backing' not in settings_response.text
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="details-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert 'id="details-panel"' not in new_response.text
    assert 'id="details-panel"' not in edit_response.text
    assert 'id="editor-panel"' not in new_response.text
    assert 'id="editor-panel"' not in edit_response.text
    assert 'id="editor"' not in new_response.text
    assert 'id="editor"' not in edit_response.text
    assert_contains_all(
        json_response.text,
        (
            'data-profiles-route-mode="json"',
            'data-profiles-template-kind="json"',
            'id="editor-panel"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="json-context-panel"' not in json_response.text
    assert 'id="json-download-strip"' not in json_response.text
    assert 'id="json-review-strip"' not in json_response.text


def test_deleted_profile_routes_require_include_deleted_and_preserve_archived_chrome():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Route Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_response = client.get(f"/profiles/{profile_id}/edit")
    archived_response = client.get(f"/profiles/{profile_id}/edit?include_deleted=true")
    archived_settings_response = client.get(f"/profiles/{profile_id}/settings?include_deleted=true")
    archived_json_response = client.get(f"/profiles/{profile_id}/json?include_deleted=true")

    assert hidden_response.status_code == 404
    assert archived_response.status_code == 200
    assert archived_settings_response.status_code == 200
    assert archived_json_response.status_code == 200
    assert 'data-include-deleted="true"' in archived_response.text
    assert 'data-i18n="profiles.badge_deleted"' in archived_response.text
    assert 'href="/profiles/' + str(profile_id) + '/edit?include_deleted=true"' in archived_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue"'
        in archived_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=editor"'
        in archived_response.text
    )

    archived_soup = BeautifulSoup(archived_response.text, "html.parser")
    assert archived_soup.find(id="current-name").get_text(strip=True) == "Archived Route Profile"
    assert archived_soup.find(id="profile-state-badge").get_text(strip=True) == "Deleted"
    assert archived_soup.find(id="overview-context").get_text(strip=True) == "Archived profile"

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200
    restored_response = client.get(f"/profiles/{profile_id}/edit")
    assert restored_response.status_code == 200
    restored_soup = BeautifulSoup(restored_response.text, "html.parser")
    assert restored_soup.find(id="profile-state-badge").get_text(strip=True) == "Active"
    assert restored_soup.find(id="overview-context").get_text(strip=True) == "Saved profile"


def test_guided_wizard_ai_step_stays_separate_from_users_addons_sites_step():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Wizard Step Seven Structure Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    wizard_panels = soup.find("div", class_="wizard-panels")
    step_four = soup.find(id="wizard-step-4")
    step_five = soup.find(id="wizard-step-5")
    bookmarks = soup.find(id="wizard-step-4-bookmarks")
    websites = soup.find(id="wizard-step-4-websites")

    assert wizard_panels is not None
    assert step_four is not None
    assert step_five is not None
    assert bookmarks is not None
    assert websites is not None
    assert step_four in wizard_panels.find_all("section", recursive=False)
    assert step_five in wizard_panels.find_all("section", recursive=False)
    assert bookmarks in step_four.descendants
    assert websites in step_four.descendants
    assert step_five not in step_four.descendants


def test_guided_wizard_all_steps_stay_as_direct_wizard_panels_and_keep_own_subsections():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Wizard Structure Audit Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    wizard_panels = soup.find("div", class_="wizard-panels")
    assert wizard_panels is not None

    direct_panel_ids = [
        child.get("id")
        for child in wizard_panels.find_all(recursive=False)
        if getattr(child, "name", None) == "section" and child.get("id", "").startswith("wizard-step-")
    ]
    assert direct_panel_ids == [f"wizard-step-{step}" for step in range(1, 7)]

    step_expected_descendants = {
        1: ("wizard-name", "wizard-schema", "wizard-starter-grid"),
        2: (
            "wizard-step-2-basics",
            "wizard-step-2-proxy",
            "wizard-step-2-trust",
            "wizard-home-surface-startup",
            "wizard-home-surface-new-tab",
            "wizard-home-surface-firefox-home",
            "wizard-step-2-default-search",
            "wizard-step-2-managed-engines",
            "wizard-step-2-suggestions",
            "wizard-step-2-review",
        ),
        3: ("wizard-hardening-presets", "wizard-cleanup-presets", "wizard-site-data-presets"),
        4: ("wizard-step-4-accounts", "wizard-step-4-language", "wizard-step-4-extensions", "wizard-step-4-bookmarks", "wizard-step-4-websites"),
        5: ("wizard-ai-posture-presets", "wizard-ai-policy-controls", "wizard-visual-search-enabled-card"),
        6: ("wizard-export-ready-card", "wizard-export-summary-ai", "wizard-export-summary-features"),
    }

    top_level_panels = {
        step: soup.find(id=f"wizard-step-{step}")
        for step in range(1, 7)
    }
    for step, panel in top_level_panels.items():
        assert panel is not None
        assert panel.parent is wizard_panels
        for descendant_id in step_expected_descendants[step]:
            descendant = soup.find(id=descendant_id)
            assert descendant is not None
            assert descendant in panel.descendants

    for step, panel in top_level_panels.items():
        other_step_prefixes = tuple(f"wizard-step-{other}-" for other in range(1, 7) if other != step)
        leaking_ids = [
            descendant.get("id")
            for descendant in panel.find_all(attrs={"id": True})
            if descendant.get("id", "").startswith(other_step_prefixes)
        ]
        assert leaking_ids == [], f"Unexpected cross-step ids inside wizard-step-{step}: {leaking_ids}"


def test_profiles_page_uses_single_year_footer_for_2025(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FrozenDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, tzinfo=tz or UTC)

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded, "datetime", FrozenDateTime)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    class FakeSession:
        async def commit(self):
            return None

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_page(request, FakeSession()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_library.html"
    assert captured["context"]["title"] == "Library — Browser Policy Manager"
    assert captured["context"]["profiles_route_mode"] == "library"
    assert captured["context"]["editing_profile_id"] is None
    assert captured["context"]["app_name"] == "Browser Policy Manager"
    assert captured["context"]["app_version"] == reloaded.settings.APP_VERSION
    assert captured["context"]["footer_year_range"] == "2025"
    assert captured["context"]["tr"]("profiles.missing", "Fallback") == "Fallback"
    assert "wizard_settings_catalog" in captured["context"]
    assert "wizard_preferences_catalog" in captured["context"]
    assert "wizard_manual_policy_controls" in captured["context"]
    assert "wizard_starter_catalog" in captured["context"]
    assert "wizard_schema_shell_catalog" in captured["context"]


def test_profiles_library_route_does_not_mutate_schema_versions_before_render(monkeypatch):
    import app.web.profiles as web_profiles

    profiles_source = (
        REPO_ROOT / "app" / "web" / "profiles.py"
    ).read_text(encoding="utf-8")
    captured: dict[str, object] = {}
    events: list[str] = []

    class FakeSession:
        async def commit(self):
            events.append("commit")

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        events.append("render")
        return HTMLResponse("ok")

    monkeypatch.setattr(web_profiles.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [],
            "query_string": b"",
        }
    )
    session = FakeSession()

    response = asyncio.run(web_profiles.profiles_page(request, session))

    assert response.status_code == 200
    assert captured["name"] == "profiles_library.html"
    assert events == ["render"]
    assert "normalize_legacy_profile_schema_versions" not in profiles_source


def test_profile_editor_routes_use_editor_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="Template Split Profile",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/7/edit",
            "headers": [],
            "query_string": b"",
        }
    )

    response = asyncio.run(reloaded.profiles_edit_page(request, 7, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_editor.html"
    assert captured["context"]["profiles_route_mode"] == "edit"
    assert captured["context"]["editing_profile_id"] == 7
    assert captured["context"]["editing_profile_schema_version"] == "release-151"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 7,
        "name": "Template Split Profile",
        "schema_version": "release-151",
        "flags": {"DisableTelemetry": True},
    }


def test_profile_settings_route_uses_settings_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="Settings Split Profile",
            schema_version="esr-140.11",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/8/settings",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_settings_page(request, 8, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_settings.html"
    assert captured["context"]["title"] == (
        "Settings Split Profile — All settings — Browser Policy Manager"
    )
    assert captured["context"]["profiles_route_mode"] == "settings"
    assert captured["context"]["editing_profile_id"] == 8
    assert captured["context"]["editing_profile_schema_version"] == "esr-140.11"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 8,
        "name": "Settings Split Profile",
        "schema_version": "esr-140.11",
        "flags": {"DisableTelemetry": True},
    }
    assert captured["context"]["return_url"] == "/profiles/8/edit"
    assert captured["context"]["focus_target"] == "policy:DisableTelemetry"
    assert captured["context"]["settings_href"] == (
        "/profiles/8/settings?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    )
    assert captured["context"]["json_href"] == "/profiles/8/json?focus=policy:DisableTelemetry"


def test_profile_json_route_uses_json_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="JSON Split Profile",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/8/json",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_json_page(request, 8, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_json.html"
    assert captured["context"]["title"] == (
        "JSON Split Profile — JSON editor — Browser Policy Manager"
    )
    assert captured["context"]["profiles_route_mode"] == "json"
    assert captured["context"]["editing_profile_id"] == 8
    assert captured["context"]["editing_profile_schema_version"] == "release-151"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 8,
        "name": "JSON Split Profile",
        "schema_version": "release-151",
        "flags": {"DisableTelemetry": True},
    }
    assert captured["context"]["return_url"] == "/profiles/8/edit"
    assert captured["context"]["focus_target"] == "policy:DisableTelemetry"
    assert captured["context"]["settings_href"] == (
        "/profiles/8/settings?return=/profiles/8/json&focus=policy:DisableTelemetry"
    )


def test_profile_editor_route_context_bootstraps_frontend_state():
    source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function readProfilesRouteContext()" in source
    assert "bodyEl?.dataset.profilesRouteMode" in source
    assert "bodyEl?.dataset.editingProfileId" in source
    assert "async function bootstrapProfileRouteState()" in source
    assert '(routeMode === "edit" || routeMode === "settings" || routeMode === "json") && editingProfileId' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in source
    assert "await resetDraft(true);" in source
    assert "await reloadList();" in source


def test_profile_json_route_context_bootstraps_focus():
    source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert 'routeMode === "json"' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in source
    assert "setJsonHandoffContext(null);" in source
    assert "applyJsonFocusTarget(focusTarget);" in source
    assert 'const savedWorkspaceScope = windowRef.localStorage.getItem(workspaceScopeStorageKey)' not in source


def test_profile_json_route_renders_return_and_focus_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Focus Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
    )

    assert response.status_code == 200
    assert f'data-json-return-url="/profiles/{profile_id}/edit"' in response.text
    assert 'data-json-focus-target="policy:DisableTelemetry"' in response.text
    assert 'id="json-return-link"' not in response.text


def test_archived_profile_handoff_routes_preserve_include_deleted_return_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Handoff Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    assert client.delete(f"/api/profiles/{profile_id}").status_code == 204

    settings_response = client.get(
        f"/profiles/{profile_id}/settings?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue&focus=policy:DisableTelemetry"
    )
    json_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=raw"
    )

    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert 'data-include-deleted="true"' in settings_response.text
    assert f'data-json-return-url="/profiles/{profile_id}/edit?include_deleted=true"' in settings_response.text
    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=policy:DisableTelemetry"'
        in settings_response.text
    )
    assert 'data-include-deleted="true"' in json_response.text
    assert f'data-json-return-url="/profiles/{profile_id}/settings?include_deleted=true"' in json_response.text
    assert f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"' in json_response.text
    assert 'id="json-return-link"' not in json_response.text


def test_archived_profile_semantic_focus_routes_preserve_include_deleted_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Semantic Focus Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    assert client.delete(f"/api/profiles/{profile_id}").status_code == 204

    settings_policy_response = client.get(
        f"/profiles/{profile_id}/settings?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue&focus=policy:DisableTelemetry"
    )
    json_raw_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=raw"
    )
    json_deprecated_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=deprecated:LegacyPolicy"
    )
    json_unknown_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=unknown:FuturePolicy"
    )

    assert settings_policy_response.status_code == 200
    assert json_raw_response.status_code == 200
    assert json_deprecated_response.status_code == 200
    assert json_unknown_response.status_code == 200

    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=policy:DisableTelemetry"'
        in settings_policy_response.text
    )
    assert 'id="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-controls="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-expanded="true"' in settings_policy_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_raw_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_deprecated_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_unknown_response.text
    )
    assert 'data-json-focus-target="raw"' in json_raw_response.text
    assert 'data-json-focus-target="deprecated:LegacyPolicy"' in json_deprecated_response.text
    assert 'data-json-focus-target="unknown:FuturePolicy"' in json_unknown_response.text


def test_active_profile_semantic_focus_routes_preopen_expected_settings_shell():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Active Semantic Focus Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    settings_policy_response = client.get(
        f"/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
    )
    json_raw_response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/settings&focus=raw"
    )

    assert settings_policy_response.status_code == 200
    assert json_raw_response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/json?focus=policy:DisableTelemetry"'
        in settings_policy_response.text
    )
    assert 'id="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-controls="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-expanded="true"' in settings_policy_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/json&amp;focus=settings-schema-shell-step-8"'
        in json_raw_response.text
    )


def test_profile_routes_delegate_navigation_helpers():
    import app.web.profiles as web_profiles

    profiles_source = (
        REPO_ROOT / "app" / "web" / "profiles.py"
    ).read_text(encoding="utf-8")

    assert web_profiles._resolve_positive_int("not-a-number") is None
    assert "from app.web.profile_navigation import (" in profiles_source
    assert "settings_shell_focus_resolver=resolve_settings_shell_focus_step" in profiles_source
    assert "build_profile_json_href(" in profiles_source
    assert "build_profile_settings_href(" in profiles_source
    assert "build_profile_route_path(" in profiles_source
    assert "resolve_safe_profiles_return_url(" in profiles_source
    assert "resolve_focus_target(" in profiles_source
    assert "def _build_profile_json_href(" not in profiles_source
    assert "def _build_profile_settings_href(" not in profiles_source
    assert "def _build_profile_route_path(" not in profiles_source
    assert "def _resolve_safe_profiles_return_url(" not in profiles_source
    assert "def _resolve_focus_target(" not in profiles_source
    assert "def _resolve_settings_shell_focus_step(" not in profiles_source


def test_profile_json_route_regression_contract():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Regression Profile"),
    )
    profile_id = create_response.json()["id"]

    json_response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/edit&focus=editor"
    )
    visual_response = client.get(f"/profiles/{profile_id}/edit")

    assert json_response.status_code == 200
    assert "<title>Advanced Regression Profile — JSON editor — Browser Policy Manager</title>" in json_response.text
    assert 'data-profiles-route-mode="json"' in json_response.text
    assert 'data-profiles-template-kind="json"' in json_response.text
    assert f'data-editing-profile-id="{profile_id}"' in json_response.text
    assert f'data-json-return-url="/profiles/{profile_id}/edit"' in json_response.text
    assert 'data-json-focus-target="editor"' in json_response.text
    assert_contains_all(
        json_response.text,
        (
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="editor-panel"',
            'id="editor"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="json-context-panel"' not in json_response.text
    assert 'id="json-download-strip"' not in json_response.text
    assert 'id="json-review-strip"' not in json_response.text

    assert visual_response.status_code == 200
    assert 'data-profiles-template-kind="editor"' in visual_response.text
    assert 'id="editor-mode-settings"' in visual_response.text
    assert 'id="details-panel"' not in visual_response.text
    assert 'id="editor-panel"' not in visual_response.text
    assert 'id="editor"' not in visual_response.text
    assert 'id="workspace-scope-panel"' not in visual_response.text
    assert 'id="workspace-scope-guided"' not in visual_response.text
    assert 'id="workspace-scope-settings"' not in visual_response.text


def test_visual_detail_actions_route_to_settings_or_json_destination():
    source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function buildProfileRoutePath(profileId, modeKey, includeDeleted = false)" in source
    assert 'basePath = `/profiles/${profileId}/settings`;' in source
    assert 'basePath = `/profiles/${profileId}/json`;' in source
    assert "function buildEditorReturnPath(profileId, routeMode, includeDeleted = false)" in source
    assert 'if (routeMode === "settings") {' in source
    assert 'if (routeMode === "json") {' in source
    assert "function normalizeSettingsFocusTarget(focusTarget)" in source
    assert 'return "settings-panel";' in source
    assert 'return "settings-schema-shell-step-8";' in source
    assert 'normalizedTarget === "raw"' in source
    assert 'normalizedTarget.startsWith("deprecated:")' in source
    assert "function normalizeJsonFocusTarget(focusTarget)" in source
    assert 'if (normalizedTarget === "settings-schema-shell-step-8") return "raw";' in source
    assert "function buildSettingsRouteHref(profileId, focusTarget = \"\")" in source
    assert 'href.searchParams.set("return", buildEditorReturnPath(profileId, routeMode, includeDeleted));' in source
    assert "const normalizedFocusTarget = normalizeSettingsFocusTarget(focusTarget);" in source
    assert 'href.searchParams.set("focus", normalizedFocusTarget);' in source
    assert "function getSettingsRouteHref(focusTarget = \"\")" in source
    assert "function buildAdvancedRouteHref(profileId, focusTarget = \"\")" in source
    assert "const normalizedFocusTarget = normalizeJsonFocusTarget(focusTarget);" in source
    assert "function getAdvancedRouteHref(focusTarget = \"\")" in source
    assert "function parseJsonFocusTarget(focusTarget)" in source
    assert "function applyJsonEditorFocusTarget(focusTarget)" in source
    assert 'const jsonTarget = routeMode === "json" ? parseJsonFocusTarget(target) : null;' in source
    assert "function deriveJsonFocusTarget(targetEl, fallback = \"\")" in source
    assert "function openJsonRouteFromVisual(event = null, focusTarget = \"\")" in source
    assert 'if (routeMode === "json") return false;' in source
    assert 'const openJsonRoute = normalizedFocusTarget === "editor"' in source
    assert '|| normalizedFocusTarget === "unknown"' in source
    assert '|| normalizedFocusTarget.startsWith("unknown:");' in source
    assert 'getAdvancedRouteHref(normalizedFocusTarget || "editor")' in source
    assert "getSettingsRouteHref(normalizedFocusTarget)" in source
    assert 'const jsonWindow = windowRef.open(href, "_blank", "noopener");' in source
    assert "jsonWindow.opener = null;" in source
    assert "function resolveJsonFocusTarget(focusTarget)" in source
    assert 'if (target === "settings-panel") return documentRef.getElementById("settings-panel");' in source
    assert 'if (target === "settings-schema-shell-step-8") return documentRef.getElementById("settings-schema-shell-step-8");' in source
    assert "return findSettingsTarget(target)" in source
    assert 'documentRef.querySelector(`[data-wizard-shell-policy-id="${policyId}"]`)' in source
    assert "|| documentRef.getElementById(target)" in source
    assert "bpm-workspace-scope" not in source


def test_export_technical_alert_strip_has_direct_dom_refresh_contract():
    root = REPO_ROOT
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    review_source = (root / "app" / "static" / "profiles_review.js").read_text(
        encoding="utf-8"
    )

    assert 'id="wizard-export-technical-alerts"' in export_template
    assert 'id="wizard-export-raw-summary-jump"' in export_template
    assert 'id="wizard-export-deprecated-summary-jump"' in export_template
    assert 'id="wizard-export-unknown-summary-jump"' in export_template
    assert 'id="wizard-export-raw-summary-count"' in export_template
    assert 'id="wizard-export-deprecated-summary-count"' in export_template
    assert 'id="wizard-export-unknown-summary-count"' in export_template
    assert "function renderFinalExportTechnicalAlerts(summary)" in review_source
    assert 'documentRef.getElementById("wizard-export-technical-alerts")' in review_source
    assert 'documentRef.getElementById("wizard-export-raw-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-deprecated-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-unknown-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-raw-summary-count")' in review_source
    assert 'documentRef.getElementById("wizard-export-deprecated-summary-count")' in review_source
    assert 'documentRef.getElementById("wizard-export-unknown-summary-count")' in review_source
    assert "technicalAlertsContainerEl.hidden = visibleCount <= 0;" in review_source


def test_unknown_export_review_jump_routes_to_json_contract():
    source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert 'if (jumpKind === "unknown") {' in source
    assert 'const semanticFocusTarget = jumpKey ? `${jumpKind}:${jumpKey}` : jumpKind;' in source
    assert "applyAdvancedContextForFinalReviewSelection(selection);" in source
    assert "if (openJsonRouteFromVisual(event, semanticFocusTarget)) {" in source
    assert 'const openJsonRoute = normalizedFocusTarget === "editor"' in source
    assert '|| normalizedFocusTarget === "unknown"' in source
    assert '|| normalizedFocusTarget.startsWith("unknown:");' in source
    assert '? getAdvancedRouteHref(normalizedFocusTarget || "editor")' in source
    assert ': getSettingsRouteHref(normalizedFocusTarget);' in source
    assert 'const jumpKey = finalReviewJumpButton.dataset.finalReviewKey || "";' in source
