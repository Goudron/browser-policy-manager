# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_clone_naming_ux_decision_covers_required_validation_and_navigation():
    decision = source_text("docs/architecture/profile-clone-naming-ux-decision.md")

    assert_source_contains_all(
        decision,
        (
            "# Profile Clone Naming UX Decision",
            "focused clone-name dialog or inline control",
            "{source name} copy",
            'target="_blank"',
            'rel="noopener"',
            "/profiles/new?clone_from={id}&clone_name={encodedName}",
            "Cancel closes the dialog",
            "Empty or whitespace-only clone names disable confirmation",
            "Duplicate-name conflicts are checked optimistically",
            "The save API remains authoritative",
            "A clone draft opens in the Guided editor as a draft",
            "The draft name is initialized from `clone_name`",
            "Owner metadata is intentionally excluded",
        ),
    )


def test_library_duplicate_opens_clone_name_control_before_new_tab_contract():
    source = static_source("profiles_library_bootstrap.js")

    assert_source_contains_all(
        source,
        (
            "function buildDefaultCloneName(profile)",
            "function buildCloneDraftHref(profile, cloneName)",
            'params.set("clone_from", String(profile.id));',
            'params.set("clone_name", cloneName);',
            'params.set("include_deleted", "true");',
            "function updateCloneNameControl(panelEl, profile)",
            "profileNameExists(cloneName, profile.id)",
            "clonePanel?.querySelector(\"[data-clone-name-input]\")?.addEventListener(\"input\", () => {",
            "clonePanel?.querySelector(\"[data-clone-name-confirm]\")?.addEventListener(\"click\", (event) => {",
            'data-clone-profile-id="${profile.id}"',
            'aria-controls="${clonePanelId}"',
            'data-clone-name-input',
            'data-clone-name-confirm',
            'target="_blank"',
            'rel="noopener"',
            '${t("profiles.library_action_duplicate")}',
        ),
    )
    assert "window.location" not in source
    assert "window.open" not in source


def test_library_clone_name_control_copy_keys_are_in_runtime_catalogs():
    for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN"):
        locale_json = json.loads((REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8"))

        for key in (
            "profiles.clone_name_label",
            "profiles.clone_name_confirm",
            "profiles.clone_name_cancel",
            "profiles.clone_name_ready",
            "profiles.clone_name_required",
            "profiles.clone_name_duplicate",
        ):
            assert locale_json[key]


def test_library_clone_name_actions_stay_inside_panel_with_long_labels_contract():
    source = static_source("profiles_library_bootstrap.js")
    css = css_source()

    assert_source_contains_all(
        source,
        (
            'class="library-clone-name-panel"',
            'class="library-clone-name-controls"',
            'class="library-clone-name-actions"',
            'class="button-base primary-button library-clone-name-confirm"',
            'class="button-base ghost-button library-clone-name-cancel"',
        ),
    )
    assert_source_contains_all(
        css,
        (
            ".library-clone-name-panel {",
            "max-inline-size: 100%;",
            "overflow-x: clip;",
            ".library-clone-name-controls {",
            "grid-template-columns: minmax(0, 1fr);",
            ".library-clone-name-actions {",
            "display: flex;",
            "flex-wrap: wrap;",
            ".library-clone-name-confirm,",
            ".library-clone-name-cancel {",
            "min-width: 0;",
            "max-width: 100%;",
            "white-space: normal;",
            "overflow-wrap: anywhere;",
            "@media (max-width: 820px)",
            ".library-clone-name-actions",
            "flex-direction: column;",
        ),
    )


def test_library_clone_name_controls_align_with_library_action_sizing_contract():
    css = css_source()

    assert_source_contains_all(
        css,
        (
            ".library-clone-name-panel {",
            "box-sizing: border-box;",
            ".library-clone-name-controls {",
            "align-items: stretch;",
            "gap: 8px;",
            ".library-clone-name-input {",
            "box-sizing: border-box;",
            "min-height: 42px;",
            ".library-clone-name-actions {",
            "align-items: stretch;",
            ".library-clone-name-confirm,",
            ".library-clone-name-cancel {",
            "box-sizing: border-box;",
            "min-height: 42px;",
            "justify-content: center;",
            "text-align: center;",
            ".library-clone-name-status {",
            "max-width: 100%;",
            "overflow-wrap: anywhere;",
        ),
    )


def test_library_clone_name_layout_covers_russian_and_french_long_labels_contract():
    css = css_source()
    locales = {
        locale: json.loads((REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8"))
        for locale in ("ru", "fr")
    }

    assert locales["ru"]["profiles.clone_name_confirm"] == "Открыть черновик"
    assert locales["ru"]["profiles.clone_name_ready"] == "Выберите имя перед открытием черновика клона."
    assert locales["fr"]["profiles.clone_name_confirm"] == "Ouvrir le brouillon"
    assert locales["fr"]["profiles.clone_name_ready"] == "Choisissez un nom avant d’ouvrir le brouillon cloné."

    assert_source_contains_all(
        css,
        (
            ".library-clone-name-panel {",
            "max-inline-size: 100%;",
            "overflow-x: clip;",
            ".library-clone-name-actions {",
            "flex-wrap: wrap;",
            ".library-clone-name-confirm,",
            ".library-clone-name-cancel {",
            "white-space: normal;",
            "overflow-wrap: anywhere;",
            "line-height: 1.25;",
            ".library-clone-name-status {",
            "overflow-wrap: anywhere;",
            "@media (max-width: 820px)",
            ".library-clone-name-actions",
            "flex-direction: column;",
        ),
    )


def test_new_profile_clone_route_exposes_requested_clone_name_to_draft():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Clone Route Source"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/new?clone_from={profile_id}&clone_name=Custom%20Clone")

    assert response.status_code == 200
    assert f'data-clone-source-id="{profile_id}"' in response.text
    assert 'data-clone-name="Custom Clone"' in response.text


def test_clone_draft_uses_requested_clone_name_with_pattern_fallback_contract():
    runtime_source = static_source("profiles_runtime.js")
    workspace_source = static_source("profiles_workspace.js")

    assert_source_contains_all(
        runtime_source,
        (
            'const cloneName = (bodyEl?.dataset.cloneName || "").trim();',
            "cloneName,",
            "await cloneFromProfile(cloneSourceId, {",
            "includeDeleted: readProfilesRouteContext().includeDeleted,",
        ),
    )
    assert_source_contains_all(
        workspace_source,
        (
            "function resolveCloneDraftName(sourceProfile, requestedCloneName = \"\")",
            "const cloneName = String(requestedCloneName || \"\").trim();",
            'return cloneName || t("profiles.clone_name_pattern").replace("{name}", sourceName);',
            "setCloneDraftState(profile, { cloneName: options.cloneName });",
            "nameInput.value = clonedName;",
        ),
    )


def test_clone_draft_preserves_source_data_without_owner_contract():
    source = static_source("profiles_workspace.js")

    assert_source_contains_all(
        source,
        (
            "setWizardComplianceSnapshot(sourceProfile?.compliance || null);",
            "descriptionInput.value = sourceProfile?.description || \"\";",
            "documentRef.getElementById(\"profile-type\").value = sourceProfile?.schema_version || defaultSchemaVersion;",
            "setCurrentRaw(flags);",
            "setCloneDraftState(profile, { cloneName: options.cloneName });",
            "const createPayload = buildCreatePayload(form, parsedFlags, compliancePayload);",
            "const copyPayload = buildCreatePayload(form, parsedFlags, compliancePayload, { name: copyName });",
        ),
    )
    assert "ownerInput" not in source
    assert "omitOwner" not in source
    assert "profile.owner" not in source


def test_clone_create_payload_has_no_owner_contract():
    source = static_source("profiles_workspace_state.js")

    assert_source_contains_all(
        source,
        (
            "const { name = form.name } = options;",
            "return {",
            "compliance: compliancePayload,",
        ),
    )
    assert "omitOwner" not in source
    assert "payload.owner" not in source
    assert "form.owner" not in source


def test_clone_name_conflicts_are_actionable_and_do_not_open_revision_conflict_panel():
    data_source = static_source("profiles_data.js")
    workspace_source = static_source("profiles_workspace.js")

    assert_source_contains_all(
        data_source,
        (
            "async function createProfile(body, fetchImpl = fetch)",
            "if (!res.ok) throw await profileRequestError(res);",
        ),
    )
    assert_source_contains_all(
        workspace_source,
        (
            "function isRevisionConflictError(error)",
            "return Number(error?.status) === 409;",
            "function isNameConflictError(error)",
            "error?.detail === \"Profile with this name already exists\"",
            "function showNameConflictState(error)",
            "? t(\"profiles.clone_name_duplicate\")",
            "clearSaveConflictState();",
            "nameInput.focus();",
            "if (isNameConflictError(e)) {",
            "showNameConflictState(e);",
        ),
    )


def test_clone_handoff_copy_has_no_owner_or_compare_guidance():
    for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN"):
        locale_json = json.loads((REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8"))

        assert "profiles.clone_handoff_item_compare" not in locale_json
        assert "profiles.clone_handoff_compare" not in locale_json
        identity_copy = locale_json["profiles.clone_handoff_item_identity"].lower()
        assert "owner" not in identity_copy
        assert "владель" not in identity_copy
        assert "所有者" not in identity_copy
