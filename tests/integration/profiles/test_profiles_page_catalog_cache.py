from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import Request

from app.web import profiles_context


def _patch_catalog_builders(monkeypatch) -> dict[str, int]:
    calls = {
        "settings": 0,
        "preferences": 0,
        "shell": 0,
        "categories": 0,
        "manual": 0,
        "starter": 0,
        "steps": 0,
        "docs": 0,
    }

    def settings():
        calls["settings"] += 1
        return {"sections": [{"id": "general", "preferences": {"id": "general"}}]}

    def preferences(_settings):
        calls["preferences"] += 1
        return {"sections": [{"id": "general"}], "known_preferences": []}

    def shell(_preferences):
        calls["shell"] += 1
        return {"steps": []}

    monkeypatch.setattr(profiles_context, "get_wizard_settings_catalog", settings)
    monkeypatch.setattr(profiles_context, "get_wizard_preferences_catalog", preferences)
    monkeypatch.setattr(profiles_context, "get_wizard_schema_shell_catalog", shell)
    monkeypatch.setattr(
        profiles_context,
        "get_all_settings_category_catalog",
        lambda: calls.__setitem__("categories", calls["categories"] + 1) or {"categories": []},
    )
    monkeypatch.setattr(
        profiles_context,
        "get_manual_policy_controls_catalog",
        lambda: calls.__setitem__("manual", calls["manual"] + 1) or {"groups": []},
    )
    monkeypatch.setattr(
        profiles_context,
        "get_wizard_starter_catalog",
        lambda **_kwargs: calls.__setitem__("starter", calls["starter"] + 1) or {"presets": {}},
    )
    monkeypatch.setattr(
        profiles_context,
        "get_wizard_steps",
        lambda: calls.__setitem__("steps", calls["steps"] + 1) or [],
    )

    def documentation_links():
        calls["docs"] += 1
        return {"en": "/help/en/index.html"}

    monkeypatch.setattr(profiles_context, "resolve_documentation_home_links", documentation_links)
    monkeypatch.setattr(profiles_context, "resolve_documentation_contextual_help_links", lambda: {})
    monkeypatch.setattr(profiles_context, "resolve_documentation_deep_help_links", lambda: {})
    monkeypatch.setattr(profiles_context, "resolve_all_settings_row_help_links", lambda: {})
    monkeypatch.setattr(
        profiles_context, "resolve_documentation_artifact_disposition", lambda: "available"
    )
    return calls


def test_shared_catalog_rebuilds_only_for_schema_or_documentation_identity(monkeypatch):
    profiles_context.clear_profiles_page_catalog_cache()
    calls = _patch_catalog_builders(monkeypatch)
    schema_identity = ["schema-a"]
    documentation_identity = ["docs-a"]
    monkeypatch.setattr(
        profiles_context, "_schema_catalog_identity", lambda: tuple(schema_identity)
    )
    monkeypatch.setattr(
        profiles_context, "_documentation_catalog_identity", lambda: documentation_identity[0]
    )

    first = profiles_context._profiles_page_catalog()
    second = profiles_context._profiles_page_catalog()

    assert first == second
    assert calls == {name: 1 for name in calls}

    schema_identity[0] = "schema-b"
    profiles_context._profiles_page_catalog()
    documentation_identity[0] = "docs-b"
    profiles_context._profiles_page_catalog()

    assert calls == {name: 3 for name in calls}


def test_page_context_receives_fresh_catalogs_and_keeps_request_fields_outside_cache(
    monkeypatch, tmp_path: Path
):
    profiles_context.clear_profiles_page_catalog_cache()
    profiles_context.clear_profile_frontend_assets_cache()
    calls = _patch_catalog_builders(monkeypatch)
    monkeypatch.setattr(profiles_context, "_schema_catalog_identity", lambda: ("schema",))
    monkeypatch.setattr(profiles_context, "_documentation_catalog_identity", lambda: "docs")
    i18n_dir = tmp_path / "i18n"
    i18n_dir.mkdir()
    (i18n_dir / "en.json").write_text(json.dumps({"profiles.channel": "Channel"}), encoding="utf-8")
    manifest_path = tmp_path / "static" / "profiles_bundles" / "profiles-bundles-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "head_script": "/static/profiles_head_bootstrap.js",
                "routes": {
                    route: {"scripts": [], "styles": []}
                    for route in ("library", "compare", "new", "edit", "settings", "json")
                },
            }
        ),
        encoding="utf-8",
    )
    settings = SimpleNamespace(
        ROOT_DIR=tmp_path,
        I18N_DIR="i18n",
        STATIC_DIR=tmp_path / "static",
        TEMPLATES_DIR=tmp_path / "templates",
        APP_VERSION="0.9.4",
        APP_NAME="BPM",
        SUPPORTED_LOCALES=["en"],
        DEFAULT_LOCALE="en",
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/new",
            "headers": [(b"accept-language", b"en")],
        }
    )

    first = profiles_context.build_profiles_page_context(
        request,
        settings_obj=settings,
        settings_shell_focus_resolver=lambda *_args: None,
        title="First",
        route_mode="new",
    )
    first["wizard_settings_catalog"]["sections"].append({"id": "mutated"})  # type: ignore[index]
    second = profiles_context.build_profiles_page_context(
        request,
        settings_obj=settings,
        settings_shell_focus_resolver=lambda *_args: None,
        title="Second",
        route_mode="new",
    )

    assert second["title"] == "Second"
    assert second["wizard_settings_catalog"]["sections"] == [
        {"id": "general", "preferences": {"id": "general"}}
    ]  # type: ignore[index]
    assert calls == {name: 1 for name in calls}


def test_locale_catalog_cache_uses_content_identity_and_returns_fresh_dicts(tmp_path: Path):
    profiles_context.clear_locale_catalog_cache()
    profiles_context.clear_profiles_page_catalog_cache()
    i18n_dir = tmp_path / "i18n"
    i18n_dir.mkdir()
    locale_path = i18n_dir / "en.json"
    locale_path.write_text('{"label":"first"}', encoding="utf-8")
    settings = SimpleNamespace(ROOT_DIR=tmp_path, I18N_DIR="i18n")

    first = profiles_context.load_locale_catalog("en", settings)
    first["label"] = "mutated"
    second = profiles_context.load_locale_catalog("en", settings)
    locale_path.write_text('{"label":"second"}', encoding="utf-8")
    third = profiles_context.load_locale_catalog("en", settings)

    assert second == {"label": "first"}
    assert third == {"label": "second"}
