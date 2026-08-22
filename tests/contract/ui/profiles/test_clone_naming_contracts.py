# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_library_duplicate_is_a_direct_preparation_link_contract():
    source = static_source("profiles_library_bootstrap.js")

    assert_source_contains_all(
        source,
        (
            "function buildDuplicatePreparationHref(profile)",
            "return `/profiles/new?clone_from=${encodeURIComponent(String(profile.id))}`;",
            'href="${buildDuplicatePreparationHref(profile)}"',
            'target="_blank"',
            'rel="noopener"',
            'data-duplicate-preparation-profile-id="${profile.id}"',
            '${t("profiles.library_action_duplicate")}',
        ),
    )
    assert_source_excludes_all(
        source,
        (
            "clone_name",
            "library-clone-name-panel",
            "data-clone-name",
            "data-clone-profile-id",
            "window.location",
            "window.open",
        ),
    )


def test_preparation_route_uses_source_identity_without_clone_name_state():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name="Preparation Route Source", flags={"DisableTelemetry": True}
        ),
    )
    profile_id = create_response.json()["id"]
    before = client.get(f"/api/profiles/{profile_id}").json()

    response = client.get(
        f"/profiles/new?clone_from={profile_id}&clone_name=Ignored%20Legacy%20Name"
    )
    after = client.get(f"/api/profiles/{profile_id}").json()

    assert response.status_code == 200
    assert 'data-profiles-template-kind="preparation"' in response.text
    assert f'data-preparation-source-id="{profile_id}"' in response.text
    assert 'data-preparation-source-revision="1"' in response.text
    assert "data-clone-name=" not in response.text
    assert "data-clone-source-id=" not in response.text
    assert "DisableTelemetry" not in response.text
    assert after == before


def test_archived_library_duplicate_has_an_explicit_unavailable_preparation_state():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Preparation Source"),
    )
    profile_id = create_response.json()["id"]
    assert client.delete(f"/api/profiles/{profile_id}").status_code == 204

    response = client.get(f"/profiles/new?clone_from={profile_id}")

    assert response.status_code == 200
    assert 'data-preparation-mode="duplicate"' in response.text
    assert 'data-preparation-terminal-action-mode="unavailable"' in response.text
    assert 'data-preparation-source-state="archived"' in response.text
    assert 'id="profile-preparation-source-error"' in response.text


def test_clone_name_panel_copy_and_css_are_retired_from_active_owners():
    css = css_source()

    assert_source_excludes_all(
        css,
        (
            "library-clone-name-panel",
            "library-clone-name-controls",
            "library-clone-name-actions",
            "library-clone-name-input",
            "library-clone-name-status",
            "library-clone-name-confirm",
            "library-clone-name-cancel",
        ),
    )
    for locale in ("en", "ru", "de", "es-ES", "fr", "zh-CN"):
        locale_json = json.loads(
            (REPO_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        for key in (
            "profiles.clone_name_label",
            "profiles.clone_name_confirm",
            "profiles.clone_name_cancel",
            "profiles.clone_name_required",
            "profiles.clone_name_duplicate",
        ):
            assert key not in locale_json


def test_runtime_does_not_bootstrap_an_unsaved_clone_draft_from_route_data():
    document_template = source_text("app/templates/profiles/_page_document.html")
    runtime_source = static_source("profiles_runtime.js")

    assert "data-clone-name" not in document_template
    assert "data-clone-source-id" not in document_template
    assert "cloneSourceId" not in runtime_source
    assert "cloneName" not in runtime_source
    assert 'routeMode === "new" && clone' not in runtime_source
