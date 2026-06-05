# ruff: noqa: F403,F405
from tests.web_profiles_page_helpers import *


def test_profiles_page_uses_local_js_yaml_asset():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/vendor/js-yaml.js?v=' in response.text
    assert "https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js" not in response.text
    assert "https://cdn.jsdelivr.net/npm/js-yaml@4.2.0/dist/js-yaml.min.js" not in response.text


def test_json_profile_route_uses_local_monaco_assets():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Monaco Asset Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get("/profiles/new")
    response = client.get(f"/profiles/{profile_id}/json")

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in guided_response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in guided_response.text
    assert '<script src="/static/vendor/monaco/vs/loader.js"></script>' not in response.text
    assert "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs" not in response.text


def test_profiles_page_uses_local_tailwind_stylesheet():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/vendor/profiles_tailwind.css?v=' in response.text
    assert "https://cdn.tailwindcss.com" not in response.text
    assert "tailwind.config =" not in response.text


def test_profiles_page_uses_local_bootstrap_assets_without_inline_scripts():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_page_bootstrap.js?v=' in response.text
    assert '<script id="profiles-initial-locale" type="application/json">' in response.text
    assert "<script>" not in response.text
    assert "window.__BPM_INITIAL_LANG__ =" not in response.text
    assert "window.__BPM_INITIAL_LOCALE__ =" not in response.text


def test_existing_profile_routes_embed_initial_profile_payload():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name="Initial Profile Embed Contract",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        ),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")

    assert response.status_code == 200
    assert '<script id="profiles-initial-profile" type="application/json">' in response.text
    assert '"name": "Initial Profile Embed Contract"' in response.text
    assert '"schema_version": "release-151"' in response.text
    assert '"DisableTelemetry": true' in response.text

    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find(id="current-name").get_text(strip=True) == "Initial Profile Embed Contract"
    assert soup.find(id="save").get_text(strip=True) == "Save"
    assert soup.find(id="profile-name").get("value") == "Initial Profile Embed Contract"
    assert soup.find(id="editor-profile-id").get_text(strip=True).startswith("#")


def test_profiles_library_page_uses_library_only_assets():
    client = make_test_client(app)

    response = client.get("/profiles")

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_utils.js?v=' in response.text
    assert '<script src="/static/profiles_shared.js?v=' in response.text
    assert '<script src="/static/profiles_platform.js?v=' in response.text
    assert '<script src="/static/profiles_data.js?v=' in response.text
    assert '<script src="/static/profiles_library_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_library.js?v=' in response.text
    assert 'id="schema-channels-catalog"' in response.text
    assert '<script src="/static/vendor/js-yaml.js?v=' not in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in response.text
    assert '<script src="/static/profiles_catalogs.js?v=' not in response.text
    assert '<script src="/static/profiles_page_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_runtime.js?v=' not in response.text
    assert '<script src="/static/profiles_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_guided.js?v=' not in response.text
    assert '<script src="/static/profiles_settings.js?v=' not in response.text
    assert '<script src="/static/profiles.js?v=' not in response.text
    assert 'id="wizard-starter-catalog"' not in response.text
    assert 'id="wizard-settings-catalog"' not in response.text
    assert 'id="wizard-preferences-catalog"' not in response.text
    assert 'id="wizard-manual-policy-controls"' not in response.text
    assert 'id="wizard-schema-shell-catalog"' not in response.text


def test_profiles_editor_modes_use_mode_specific_entrypoints():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Mode Entrypoint Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get("/profiles/new")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    assert guided_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert '<script src="/static/profiles_guided.js?v=' in guided_response.text
    assert '<script src="/static/profiles_settings.js?v=' not in guided_response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in guided_response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in guided_response.text
    assert '<script src="/static/profiles_library.js?v=' not in guided_response.text
    assert '<script src="/static/profiles.js?v=' not in guided_response.text
    assert '<script src="/static/profiles_settings.js?v=' in settings_response.text
    assert '<script src="/static/profiles_guided.js?v=' not in settings_response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in settings_response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in settings_response.text
    assert '<script src="/static/profiles_json.js?v=' in json_response.text
    assert '<script src="/static/profiles_guided.js?v=' not in json_response.text
    assert '<script src="/static/profiles_settings.js?v=' not in json_response.text
    assert '<script src="/static/profiles_library.js?v=' not in json_response.text
    assert '<script src="/static/profiles.js?v=' not in json_response.text


def test_profiles_page_uses_request_locale_for_initial_render():
    client = make_test_client(app)

    response = client.get(
        "/profiles",
        headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
    )

    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    assert "Библиотека" in response.text
    assert "Менеджер профилей браузера" in response.text
    assert "Поиск по имени профиля" in response.text
    assert "Сравнение двух профилей" in response.text
    assert "Пошаговый мастер" not in response.text
    assert "Search engine" not in response.text
    assert "Engine name" not in response.text
    assert "Search URL template" not in response.text
    assert "Required for a valid engine" not in response.text
    assert "Privacy and user data" not in response.text
    assert "Sync and Firefox Accounts" not in response.text
    assert "Homepage and startup" not in response.text
    assert "Controls in this area" not in response.text
    assert "Top-level policies" not in response.text
    assert "Control Room" not in response.text


def test_resolve_request_locale_skips_unsupported_languages_and_bad_weights():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"pt-BR;q=1, ;q=0.9, ru;q=oops, en;q=0.5")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_uses_matrix_backed_regional_fallbacks(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            SUPPORTED_LOCALES=("en", "ru", "de", "zh-CN", "fr", "es-ES"),
            DEFAULT_LOCALE="en",
        ),
    )

    cases = (
        (b"de-AT,de;q=0.9,en;q=0.1", "de"),
        (b"fr-CA,fr;q=0.9,en;q=0.1", "fr"),
        (b"es-MX,es;q=0.9,en;q=0.1", "es-ES"),
        (b"zh-Hans-CN,zh;q=0.9,en;q=0.1", "zh-CN"),
    )
    for header, expected_locale in cases:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/profiles",
                "headers": [(b"accept-language", header)],
                "query_string": b"",
            }
        )
        assert reloaded._resolve_request_locale(request) == expected_locale


def test_resolve_request_locale_falls_back_to_active_catalog_for_target_only_locales(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_prefers_next_active_catalog_before_default_fallback(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,ru-RU;q=0.8,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "ru"


def test_load_locale_catalog_returns_empty_mapping_for_missing_locale(
    tmp_path,
    monkeypatch,
    reset_app_caches,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    reset_app_caches("locale_catalogs")
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            ROOT_DIR=tmp_path,
            I18N_DIR="i18n",
            SUPPORTED_LOCALES=("en", "ru"),
            TEMPLATES_DIR=web_profiles.settings.TEMPLATES_DIR,
        ),
    )

    assert reloaded._load_locale_catalog("de") == {}


def test_en_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/en.json")
    assert locale_response.status_code == 200
    assert locale_response.headers["content-type"].startswith("application/json")
    _assert_en_locale_catalog(locale_response.json())


def test_ru_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/ru.json")
    assert locale_response.status_code == 200
    _assert_ru_locale_catalog(locale_response.json())


def test_profiles_js_has_no_inline_english_fallback_copy():
    static_dir = REPO_ROOT / "app" / "static"
    fallback_pattern = re.compile(r'\bt\(\s*"profiles\.[^"]+"\s*,\s*"[^"]+"\s*\)')
    raw_status_pattern = re.compile(r"\b(?:setStatus|setDraftState|setValidationPreview)\(\s*[\"`]")
    confirm_fallback_pattern = re.compile(r'windowRef\.confirm\(\s*t\(\s*"profiles\.[^"]+"\s*,')

    fallback_hits: list[str] = []
    raw_status_hits: list[str] = []
    confirm_hits: list[str] = []

    for path in sorted(static_dir.glob("profiles*.js")):
        text = path.read_text(encoding="utf-8")
        if fallback_pattern.search(text):
            fallback_hits.append(path.name)
        if raw_status_pattern.search(text):
            raw_status_hits.append(path.name)
        if confirm_fallback_pattern.search(text):
            confirm_hits.append(path.name)

    assert not fallback_hits, f"inline translation fallbacks remain in: {fallback_hits}"
    assert not raw_status_hits, f"raw status strings remain in: {raw_status_hits}"
    assert not confirm_hits, f"confirm fallbacks remain in: {confirm_hits}"


def test_static_assets_are_served():
    client = make_test_client(app)
    settings = get_settings()

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"].startswith("image/x-icon")
    assert favicon_response.content == (settings.STATIC_DIR / "favicon.ico").read_bytes()


def test_static_vendor_js_yaml_asset_exists():
    asset_path = REPO_ROOT / "app" / "static" / "vendor" / "js-yaml.js"
    asset_text = asset_path.read_text(encoding="utf-8")

    assert asset_path.is_file()
    assert ".jsyaml={}" in asset_text or ".jsyaml=" in asset_text


def test_static_vendor_monaco_assets_exist():
    vendor_root = REPO_ROOT / "app" / "static" / "vendor"
    bundle_path = vendor_root / "profiles_monaco.js"
    bundle_css_path = vendor_root / "profiles_monaco.css"
    editor_worker_path = vendor_root / "monaco-editor.worker.js"
    json_worker_path = vendor_root / "monaco-json.worker.js"
    license_path = vendor_root / "monaco.LICENSE"

    assert bundle_path.is_file()
    assert bundle_css_path.is_file()
    assert editor_worker_path.is_file()
    assert json_worker_path.is_file()
    assert license_path.is_file()
    assert "eval(" not in bundle_path.read_text(encoding="utf-8")
    assert "new Function" not in bundle_path.read_text(encoding="utf-8")
    assert "Microsoft Corporation" in license_path.read_text(encoding="utf-8")


def test_json_editor_runtime_uses_profile_loaded_status_and_custom_monaco_theme_contract():
    root = REPO_ROOT
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    json_editor_source = (
        root / "app" / "static" / "profiles_runtime_json_editor.js"
    ).read_text(encoding="utf-8")
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert 'function getMonacoThemeName(resolvedTheme)' in json_editor_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-light"' in json_editor_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-dark"' in json_editor_source
    assert 'windowRef.monaco.editor.setTheme(jsonEditorRuntime.getMonacoThemeName(resolvedTheme));' in runtime_source
    assert 'lineNumbersMinChars: 4' in runtime_source
    assert 'lineDecorationsWidth: 18' in runtime_source
    assert 'vertical: "visible"' in runtime_source
    assert 'horizontal: "auto"' in runtime_source
    assert (
        'fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"'
        in runtime_source
    )
    assert 'await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });' in runtime_source
    assert (
        'setStatus(t("profiles.status_profile_loaded").replace("{name}", hydratedProfile.name), "success");'
        in runtime_source
    )
    assert "const { announceStatus = hasLibrarySurface } = options;" in workspace_source
    assert "syncLibrary = hasLibrarySurface" in workspace_source
    assert "announceLoaded = true" in workspace_source
    assert '.editor-frame .monaco-editor .margin-view-overlays .line-numbers {' in css_source
    assert '.editor-frame .monaco-scrollable-element > .scrollbar.vertical {' in css_source
    assert '.editor-frame .monaco-scrollable-element > .scrollbar > .slider {' in css_source


def test_static_vendor_tailwind_replacement_asset_exists():
    asset_path = (
        REPO_ROOT / "app" / "static" / "vendor" / "profiles_tailwind.css"
    )
    asset_text = asset_path.read_text(encoding="utf-8")

    assert asset_path.is_file()
    assert ".min-h-screen" in asset_text
    assert ".shadow-soft" in asset_text
    assert ".hover\\:bg-slate-50:hover" in asset_text


def test_static_profiles_bootstrap_assets_exist():
    static_root = REPO_ROOT / "app" / "static"
    head_bootstrap = static_root / "profiles_head_bootstrap.js"
    page_bootstrap = static_root / "profiles_page_bootstrap.js"
    library_bootstrap = static_root / "profiles_library_bootstrap.js"
    library_entry = static_root / "profiles_library.js"
    guided_entry = static_root / "profiles_guided.js"
    settings_entry = static_root / "profiles_settings.js"
    json_entry = static_root / "profiles_json.js"
    json_editor_runtime = static_root / "profiles_runtime_json_editor.js"
    dirty_guard_runtime = static_root / "profiles_runtime_dirty_guard.js"
    workspace_state = static_root / "profiles_workspace_state.js"
    review_state = static_root / "profiles_review_state.js"
    css_layer_root = static_root / "profiles_css"

    assert head_bootstrap.is_file()
    assert page_bootstrap.is_file()
    assert library_bootstrap.is_file()
    assert library_entry.is_file()
    assert guided_entry.is_file()
    assert settings_entry.is_file()
    assert json_entry.is_file()
    assert json_editor_runtime.is_file()
    assert dirty_guard_runtime.is_file()
    assert workspace_state.is_file()
    assert review_state.is_file()
    assert (css_layer_root / "00-foundation.css").is_file()
    assert (css_layer_root / "10-library.css").is_file()
    assert (css_layer_root / "20-editor-wizard.css").is_file()
    assert (css_layer_root / "30-responsive.css").is_file()
    assert (css_layer_root / "40-compact-shell.css").is_file()
    assert 'window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);' in page_bootstrap.read_text(encoding="utf-8")


def test_profiles_css_bundle_matches_source_layers():
    root = REPO_ROOT
    bundle_source = (root / "app" / "static" / "profiles.css").read_text(encoding="utf-8")
    readme_source = (root / "app" / "static" / "profiles_css" / "README.md").read_text(
        encoding="utf-8"
    )

    assert bundle_source == build_profiles_css.build_css()
    assert "Generated by tools/build_profiles_css.py" in bundle_source
    assert "00-foundation.css" in readme_source
    assert "40-compact-shell.css" in readme_source


def test_profiles_page_assets_are_declared_through_route_manifest():
    templates_root = REPO_ROOT / "app" / "templates" / "profiles"
    document_template = (templates_root / "_page_document.html").read_text(encoding="utf-8")
    manifest_template = (templates_root / "_page_route_assets.html").read_text(encoding="utf-8")

    assert '{% include "profiles/_page_route_assets.html" %}' in document_template
    assert document_template.count('{% include "profiles/_page_route_assets.html" %}') == 2
    assert '{% set route_requires_monaco = route_kind == "json" %}' in manifest_template
    assert "route_entrypoints" in manifest_template
    assert '"editor": "/static/profiles_guided.js"' in manifest_template
    assert '"settings": "/static/profiles_settings.js"' in manifest_template
    assert '"json": "/static/profiles_json.js"' in manifest_template
    assert "/static/profiles_library.js" in manifest_template
    assert '"/static/profiles_review_state.js"' in manifest_template
    assert '"/static/profiles_workspace_state.js"' in manifest_template
    assert '"/static/profiles.css"' in manifest_template
    assert '"/static/profiles_css/' not in manifest_template
    assert '<script src="/static/profiles_guided.js?v={{ asset_version }}"></script>' not in document_template
    assert '<script src="/static/profiles_settings.js?v={{ asset_version }}"></script>' not in document_template
    assert '<script src="/static/profiles_json.js?v={{ asset_version }}"></script>' not in document_template


def test_web_profiles_module_wires_templates_and_route():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    profile_route_paths = {
        route.path
        for route in reloaded.router.routes
        if route.path.startswith("/profiles")
    }

    assert reloaded.templates.env.loader.searchpath == [str(reloaded.settings.TEMPLATES_DIR)]
    assert profile_route_paths == {
        "/profiles",
        "/profiles/new",
        "/profiles/{profile_id}/edit",
        "/profiles/{profile_id}/settings",
        "/profiles/{profile_id}/json",
    }
