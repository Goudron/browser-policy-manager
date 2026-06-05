# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_profile_route_navigation_warns_when_editor_is_dirty():
    runtime_source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")
    dirty_guard_source = (
        REPO_ROOT / "app" / "static" / "profiles_runtime_dirty_guard.js"
    ).read_text(encoding="utf-8")

    assert "function isGuardedProfileRouteHref(anchorEl)" in dirty_guard_source
    assert 'href.startsWith("#")' in dirty_guard_source
    assert 'url.pathname === "/profiles" || url.pathname.startsWith("/profiles/")' in dirty_guard_source
    assert "function isCrossTabProfileRouteIntent(event, anchorEl)" in dirty_guard_source
    assert 'anchorEl?.target && anchorEl.target !== "_self"' in dirty_guard_source
    assert "if (event.metaKey || event.ctrlKey || event.shiftKey) return true;" in dirty_guard_source
    assert 'if (typeof event.button === "number" && event.button !== 0) return true;' in dirty_guard_source
    assert "function confirmRouteNavigationIfDirty()" in dirty_guard_source
    assert "if (!currentSnapshotState().dirty) return true;" in dirty_guard_source
    assert "return windowRef.confirm(confirmDiscard());" in dirty_guard_source
    assert "function guardProfileRouteNavigation(event)" in dirty_guard_source
    assert "if (isCrossTabProfileRouteIntent(event, anchorEl)) return false;" in dirty_guard_source
    assert "event.preventDefault();" in dirty_guard_source
    assert "event.stopPropagation();" in dirty_guard_source
    assert "dirtyRouteGuard.guardProfileRouteNavigation(event)" in runtime_source
    assert 'windowRef.addEventListener("beforeunload"' in dirty_guard_source
    assert "dirtyRouteGuard.bindBeforeUnload();" in runtime_source


def test_guided_settings_handoffs_use_route_links_with_focus():
    root = REPO_ROOT
    ai_template = (root / "app" / "templates" / "profiles" / "_page_wizard_step_ai.html").read_text(
        encoding="utf-8"
    )
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")

    assert 'data-workspace-scope-target="settings"' not in ai_template
    assert 'data-workspace-scope-target="settings"' not in export_template
    assert 'id="wizard-ai-providers-handoff"' not in ai_template
    assert 'id="wizard-ai-providers-open-settings"' not in ai_template
    assert 'href="{{ settings_href }}&focus=settings-schema-shell-step-8"' in export_template
    assert 'target="_blank"' in export_template
    assert 'rel="noopener"' in export_template


def test_editor_mode_links_preserve_route_aware_returns_and_settings_focus():
    source = (
        REPO_ROOT / "app" / "static" / "profiles_workspace.js"
    ).read_text(encoding="utf-8")

    assert "function normalizeSettingsModeFocusTarget(focusTarget)" in source
    assert "function normalizeJsonModeFocusTarget(focusTarget)" in source
    assert "function isJsonModeFocusTarget(focusTarget)" in source
    assert 'const returnPath = routeMode === "settings"' in source
    assert '`/profiles/${currentId}/settings${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert '`/profiles/${currentId}/json${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert '`/profiles/${currentId}/edit${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert 'const settingsFocusTarget = normalizeSettingsModeFocusTarget(routeFocusTarget);' in source
    assert 'return `/profiles/${currentId}/settings?${params.join("&")}`;' in source
    assert 'const jsonFocusTarget = normalizeJsonModeFocusTarget(routeFocusTarget);' in source
    assert "function encodeReturnPath(returnPath)" in source
    assert source.count("params.push(`return=${encodeReturnPath(returnPath)}`);") == 2
    assert 'return `/profiles/${currentId}/json?${params.join("&")}`;' in source
    assert 'const detailMode = routeMode === "settings"' in source
    assert 'active: routeMode === "settings" || (routeMode === "json" && detailMode === "settings")' in source
    assert 'el.setAttribute("title", t("profiles.editor_chrome_save_first"));' in source
    assert 'el.removeAttribute("title");' in source


def test_unsaved_guided_route_explicitly_disables_settings_and_json_handoffs():
    client = make_test_client(app)
    response = client.get("/profiles/new")

    assert response.status_code == 200
    assert 'id="editor-mode-settings"' in response.text
    assert 'id="editor-mode-json"' in response.text
    assert response.text.count('aria-disabled="true"') >= 2
    assert response.text.count('title="Save the profile first to open All settings or JSON in a separate tab."') >= 2
    assert 'id="editor-mode-links-hint"' in response.text
    assert 'role="status"' in response.text
    assert 'Save the profile first to open All settings or JSON in a separate tab.' in response.text


def test_saved_guided_route_enables_settings_and_json_handoffs_after_first_save():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Saved Handoff Availability Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")

    assert response.status_code == 200
    assert f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit"' in response.text
    assert f'href="/profiles/{profile_id}/json?focus=editor"' in response.text
    assert 'title="Save the profile first to open All settings or JSON in a separate tab."' not in response.text
    assert 'id="editor-mode-links-hint"' in response.text
    assert 'support-hidden' in response.text


def test_profile_settings_route_preserves_step8_json_handoff():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Step 8 Handoff Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit&focus=settings-schema-shell-step-8"
    )

    assert response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/json?focus=raw"'
        in response.text
    )


def test_profile_json_route_maps_semantic_focus_back_to_settings():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Semantic Focus Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/settings&focus=deprecated:LegacyPolicy"
    )

    assert response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/json&amp;focus=settings-schema-shell-step-8"'
        in response.text
    )


def test_ai_step_locales_describe_esr_empty_state():
    client = make_test_client(app)
    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()

    assert en_catalog["profiles.wizard_ai_esr_title"] == (
        "This schema does not support AI settings"
    )
    assert en_catalog["profiles.wizard_ai_esr_state"] == (
        "This schema does not support AI settings."
    )
    assert ru_catalog["profiles.wizard_ai_esr_title"] == (
        "Эта схема не поддерживает настройки ИИ"
    )
    assert ru_catalog["profiles.wizard_ai_esr_state"] == (
        "Эта схема не поддерживает настройки ИИ."
    )
