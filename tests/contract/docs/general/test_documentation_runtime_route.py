from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.documentation import manifest as docs_manifest
from app.documentation import router as docs_router
from app.documentation.router import DOCUMENTATION_HTML_CSP
from app.main import create_app
from tests.support import make_test_client


def _docs_html(locale: str, title: str) -> str:
    return (
        f'<!doctype html><html lang="{locale}" data-theme="system">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title}</title>"
        '<link rel="stylesheet" href="assets/bpm-docs.css">'
        "</head>"
        '<body class="bpm-docs-shell">'
        '<a class="bpm-docs-skip-link" href="#bpm-docs-main">Skip to content</a>'
        '<header class="bpm-docs-header">'
        '<nav class="bpm-docs-header-nav" aria-label="Documentation navigation">'
        f'<a href="/help/{locale}/">Home</a>'
        "</nav>"
        "</header>"
        '<main id="bpm-docs-main" tabindex="-1">'
        f"<h1>{title}</h1>"
        f"<p>{title} {locale}</p>"
        "</main>"
        "</body></html>"
    )


def _write_packaged_site(root: Path) -> None:
    locales = ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    current_bpm_version = get_settings().APP_VERSION
    topic_specs = {
        "ug-concept-choose-editor-surface": ("user-guide", "user", {}),
        "ug-task-use-profile-library": ("user-guide", "user", {}),
        "ug-task-compare-profiles": ("user-guide", "user", {}),
        "ug-task-use-guided-editor": ("user-guide", "user", {}),
        "ug-task-use-all-settings": ("user-guide", "user", {}),
        "ug-task-use-json-editor": ("user-guide", "user", {}),
        "ug-task-validate-profile": ("user-guide", "user", {}),
        "ug-task-import-policies-json": ("user-guide", "user", {}),
        "ug-task-export-policies-json": ("user-guide", "user", {}),
        "fx-concept-complex-policy-families": (
            "firefox-policy-guide",
            "firefox",
            {"a-privacy-ai": "Privacy and AI controls"},
        ),
        "fx-reference-managed-preference-locking": (
            "firefox-policy-guide",
            "firefox",
            {"a-safe-review": "Safe review"},
        ),
        "cis-settings-guide": (
            "cis-settings-guide",
            "cis",
            {"a-cis-settings-guide": "CIS Settings Guide"},
        ),
    }
    for locale in locales:
        locale_root = root / locale
        (locale_root / "assets").mkdir(parents=True, exist_ok=True)
        (locale_root / "user").mkdir(parents=True, exist_ok=True)
        (locale_root / "firefox").mkdir(parents=True, exist_ok=True)
        (locale_root / "cis").mkdir(parents=True, exist_ok=True)
        (locale_root / "index.html").write_text(
            _docs_html(locale, f"Docs {locale}"),
            encoding="utf-8",
        )
        for topic_id, (_guide_id, url_root, _anchors) in topic_specs.items():
            (locale_root / f"{url_root}/{topic_id}.html").write_text(
                _docs_html(locale, topic_id),
                encoding="utf-8",
            )
        (locale_root / "source.dita").write_text("<topic/>", encoding="utf-8")
        (locale_root / "assets/bpm-docs.css").write_text(
            "body { color: CanvasText; }",
            encoding="utf-8",
        )

    (root / "search/en").mkdir(parents=True, exist_ok=True)
    (root / "search/en/index.json").write_text('{"documents":[]}', encoding="utf-8")
    target_map = {
        "schema_version": 1,
        "manifest_schema_version": 1,
        "bpm_version": current_bpm_version,
        "locales": locales,
        "targets": {
            "topic:user-guide": {
                "kind": "topic",
                "source_id": "user-guide",
                "source_inventory": "documentation/src/dita/en/maps/user-guide.ditamap",
                "topic_id": "user-guide",
            },
            **{
                f"topic:{topic_id}": {
                    "kind": "topic",
                    "source_id": topic_id,
                    "source_inventory": "documentation/src/dita",
                    "topic_id": topic_id,
                }
                for topic_id in topic_specs
            },
            "policy:AIControls": {
                "kind": "policy",
                "source_id": "AIControls",
                "source_inventory": (
                    "documentation/config/firefox-policy-context-targets-0.9.0.json"
                ),
                "topic_id": "fx-concept-complex-policy-families",
                "anchor_id": "a-privacy-ai",
            },
            "policy:VisualSearchEnabled": {
                "kind": "policy",
                "source_id": "VisualSearchEnabled",
                "source_inventory": (
                    "documentation/config/firefox-policy-context-targets-0.9.0.json"
                ),
                "topic_id": "fx-concept-complex-policy-families",
                "anchor_id": "a-privacy-ai",
            },
            "known-preference:browser.download.dir": {
                "kind": "known-preference",
                "source_id": "browser.download.dir",
                "source_inventory": (
                    "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
                ),
                "topic_id": "fx-reference-managed-preference-locking",
                "anchor_id": "a-safe-review",
            },
            "cis:1.1.1.1": {
                "kind": "cis",
                "source_id": "1.1.1.1",
                "source_inventory": "docs/architecture/cis-documentation-inventory-0.9.0.json",
                "topic_id": "cis-settings-guide",
                "anchor_id": "a-cis-settings-guide",
            },
        },
    }
    target_map_bytes = json.dumps(target_map).encode()
    (root / "ui-target-map.json").write_bytes(target_map_bytes)
    manifest = {
        "schema_version": 1,
        "artifact": {
            "bpm_version": current_bpm_version,
            "documentation_version": current_bpm_version,
            "build_id": "test-build",
            "source_revision": "0" * 40,
            "dita_ot_version": "4.4",
        },
        "default_locale": "en",
        "locales": locales,
        "guides": {
            "user-guide": {
                "url_root": "user",
                "home_topic_id": "user-guide",
                "title": {locale: "User Guide" for locale in locales},
            },
            "firefox-policy-guide": {
                "url_root": "firefox",
                "home_topic_id": "firefox-policy-guide",
                "title": {locale: "Firefox Policy Guide" for locale in locales},
            },
            "cis-settings-guide": {
                "url_root": "cis",
                "home_topic_id": "cis-settings-guide",
                "title": {locale: "CIS Settings Guide" for locale in locales},
            },
        },
        "topics": {
            "user-guide": {
                "guide_id": "user-guide",
                "dita_key": "topic.user-guide",
                "source_slug": "user-guide",
                "url_path": "home",
                "kind": "landing",
                "title": {locale: "User Guide" for locale in locales},
                "anchors": {},
                "output": {locale: f"{locale}/index.html" for locale in locales},
            },
            **{
                topic_id: {
                    "guide_id": guide_id,
                    "dita_key": f"topic.{topic_id}",
                    "source_slug": topic_id,
                    "url_path": topic_id,
                    "kind": "task" if "-task-" in topic_id else "concept",
                    "title": {locale: topic_id for locale in locales},
                    "anchors": anchors,
                    "output": {
                        locale: f"{locale}/{url_root}/{topic_id}.html" for locale in locales
                    },
                }
                for topic_id, (guide_id, url_root, anchors) in topic_specs.items()
            },
        },
        "search": {"en": {"path": "search/en/index.json"}},
        "aliases": {
            "user/choose-editor": {
                "topic_id": "ug-concept-choose-editor-surface",
                "canonical_url_path": "user/ug-concept-choose-editor-surface",
                "reason": "stable short alias",
                "since_bpm_version": current_bpm_version,
            }
        },
        "ui_target_map": {
            "path": "ui-target-map.json",
            "sha256": hashlib.sha256(target_map_bytes).hexdigest(),
            "schema_version": 1,
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _client_with_docs(root: Path, monkeypatch):
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", str(root))
    get_settings.cache_clear()
    return make_test_client(create_app())


def _read_manifest(root: Path) -> dict[str, object]:
    return json.loads((root / "manifest.json").read_text(encoding="utf-8"))


def _write_manifest(root: Path, manifest: dict[str, object]) -> None:
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _read_target_map(root: Path) -> dict[str, object]:
    return json.loads((root / "ui-target-map.json").read_text(encoding="utf-8"))


def _write_target_map(root: Path, target_map: dict[str, object]) -> None:
    target_map_bytes = json.dumps(target_map).encode()
    (root / "ui-target-map.json").write_bytes(target_map_bytes)
    manifest = _read_manifest(root)
    ui_target_map = manifest["ui_target_map"]
    if isinstance(ui_target_map, dict):
        ui_target_map["sha256"] = hashlib.sha256(target_map_bytes).hexdigest()
        _write_manifest(root, manifest)


def test_help_route_serves_packaged_locale_pages_assets_and_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        page = client.get("/help/ru/")
        css = client.get("/help/ru/assets/bpm-docs.css")
        manifest = client.get("/help/manifest.json")
        target_map = client.get("/help/ui-target-map.json")
        search = client.get("/help/search/en/index.json")

    assert page.status_code == 200
    assert 'lang="ru"' in page.text
    assert page.headers["content-type"].startswith("text/html; charset=utf-8")
    assert page.headers["content-security-policy"] == DOCUMENTATION_HTML_CSP
    served_manifest = manifest.json()
    served_target_map = target_map.json()
    current_version = get_settings().APP_VERSION
    artifact = served_manifest["artifact"]
    assert artifact["bpm_version"] == current_version
    assert artifact["documentation_version"] == current_version
    assert served_target_map["bpm_version"] == current_version

    for response, content_type in (
        (css, "text/css; charset=utf-8"),
        (manifest, "application/json; charset=utf-8"),
        (target_map, "application/json; charset=utf-8"),
        (search, "application/json; charset=utf-8"),
    ):
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(content_type)
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "0"
        assert response.headers["permissions-policy"] == "geolocation=(), microphone=(), camera=()"
        assert response.headers["cross-origin-resource-policy"] == "same-origin"
        assert response.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"


def test_help_route_redirects_locale_root_and_preserves_openapi_docs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        help_root = client.get("/help/")
        locale_root = client.get("/help/en")
        openapi_ui = client.get("/docs")
        openapi_schema = client.get("/openapi.json")

    assert help_root.status_code == 307
    assert help_root.headers["location"] == "/help/en/"
    assert locale_root.status_code == 307
    assert locale_root.headers["location"] == "/help/en/"
    assert openapi_ui.status_code == 200
    assert "Swagger UI" in openapi_ui.text
    assert openapi_schema.status_code == 200
    assert "/help/" not in openapi_schema.text


def test_help_root_selects_active_locale_from_query_cookie_and_accept_language(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        query_locale = client.get("/help/?locale=ru")
        language_locale = client.get("/help/", headers={"accept-language": "de-DE,de;q=0.8"})
        cookie_locale = client.get("/help/", headers={"cookie": "bpm_locale=fr"})
        noncanonical_query_locale = client.get("/help/?locale=zh")

    assert query_locale.status_code == 307
    assert query_locale.headers["location"] == "/help/ru/"
    assert language_locale.status_code == 307
    assert language_locale.headers["location"] == "/help/de/"
    assert cookie_locale.status_code == 307
    assert cookie_locale.headers["location"] == "/help/fr/"
    assert noncanonical_query_locale.status_code == 307
    assert noncanonical_query_locale.headers["location"] == "/help/zh-CN/"


def test_help_route_resolves_manifest_topics_aliases_and_unsupported_locale_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        guide_home = client.get("/help/es-ES/user/home/")
        topic_without_slash = client.get("/help/ru/user/ug-concept-choose-editor-surface")
        topic = client.get("/help/ru/user/ug-concept-choose-editor-surface/")
        alias = client.get("/help/ru/user/choose-editor/")
        unsupported_locale = client.get("/help/it/user/home/")
        topic_page = client.get("/help/ru/user/ug-concept-choose-editor-surface.html")

    assert guide_home.status_code == 307
    assert guide_home.headers["location"] == "/help/es-ES/index.html"
    assert topic_without_slash.status_code == 307
    assert (
        topic_without_slash.headers["location"] == "/help/ru/user/ug-concept-choose-editor-surface/"
    )
    assert topic.status_code == 307
    assert topic.headers["location"] == "/help/ru/user/ug-concept-choose-editor-surface.html"
    assert alias.status_code == 307
    assert alias.headers["location"] == "/help/ru/user/ug-concept-choose-editor-surface/"
    assert unsupported_locale.status_code == 307
    assert unsupported_locale.headers["location"] == "/help/en/user/home/"
    assert topic_page.status_code == 200
    assert "ug-concept-choose-editor-surface ru" in topic_page.text


def test_help_route_preserves_accessibility_responsive_csp_and_theme_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        docs_page = client.get("/help/ru/")
        topic_page = client.get("/help/ru/user/ug-task-use-profile-library.html")
        missing_page = client.get("/help/ru/user/missing.html")
        openapi_ui = client.get("/docs")

    assert docs_page.status_code == 200
    assert topic_page.status_code == 200
    assert missing_page.status_code == 404
    assert openapi_ui.status_code == 200

    for response in (docs_page, topic_page, missing_page):
        assert response.headers["content-security-policy"] == DOCUMENTATION_HTML_CSP
        assert response.headers["cross-origin-opener-policy"] == "same-origin"
        assert response.headers["permissions-policy"] == "geolocation=(), microphone=(), camera=()"
        soup = BeautifulSoup(response.text, "html.parser")
        assert soup.html["lang"] == "ru"
        assert (
            soup.find("meta", attrs={"name": "viewport"})["content"]
            == "width=device-width, initial-scale=1"
        )
        assert soup.find("main") is not None
        assert soup.find("h1") is not None
        assert soup.find("script") is None
        assert soup.find("style") is None
        assert not soup.find(attrs={"onclick": True})

    docs_soup = BeautifulSoup(docs_page.text, "html.parser")
    assert docs_soup.html["data-theme"] == "system"
    assert docs_soup.select_one(".bpm-docs-skip-link[href='#bpm-docs-main']") is not None
    assert docs_soup.select_one("nav[aria-label='Documentation navigation']") is not None
    assert docs_soup.select_one("main#bpm-docs-main[tabindex='-1']") is not None

    missing_soup = BeautifulSoup(missing_page.text, "html.parser")
    assert missing_soup.select_one("a[href='#bpm-docs-status-main']") is not None
    assert missing_soup.select_one("nav[aria-label='Documentation status']") is not None
    assert missing_soup.select_one("main#bpm-docs-status-main[tabindex='-1']") is not None
    assert missing_soup.select_one("section[role='status'][aria-live='polite']") is not None
    assert "Страница документации не найдена" in missing_page.text


def test_help_route_rejects_missing_locale_missing_asset_and_path_traversal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        fallback_locale = client.get("/help/it/")
        missing_asset = client.get("/help/en/missing.html")
        encoded_traversal = client.get("/help/en/%2e%2e/manifest.json")
        unsupported_type = client.get("/help/en/source.dita")

    assert fallback_locale.status_code == 307
    assert fallback_locale.headers["location"] == "/help/en/"
    assert missing_asset.status_code == 404
    assert "Documentation page was not found" in missing_asset.text
    assert missing_asset.headers["content-type"].startswith("text/html; charset=utf-8")

    for response in (encoded_traversal, unsupported_type):
        assert response.status_code == 404
        assert response.text == "Documentation asset not found\n"
        assert response.headers["content-security-policy"].startswith("default-src 'none'")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"


def test_help_route_fails_safely_when_documentation_artifact_is_absent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    missing_site = tmp_path / "missing"

    with _client_with_docs(missing_site, monkeypatch) as client:
        page = client.get("/help/en/")
        root = client.get("/help/", headers={"accept-language": "ru-RU,ru;q=0.9"})
        manifest = client.get("/help/manifest.json")

    assert page.status_code == 503
    assert "Documentation is not installed" in page.text
    assert "Open BPM Profile Library" in page.text
    assert page.headers["content-type"].startswith("text/html; charset=utf-8")

    assert root.status_code == 503
    assert "Документация не установлена" in root.text
    assert "Открыть библиотеку профилей BPM" in root.text

    assert manifest.status_code == 503
    assert manifest.text == "Documentation artifact is not installed\n"
    for response in (page, root, manifest):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"


def test_help_route_fails_safely_when_manifest_or_target_map_is_incompatible(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with _client_with_docs(tmp_path, monkeypatch) as client:
        root = client.get("/help/")
        manifest_response = client.get("/help/manifest.json")
        topic = client.get("/help/en/user/ug-concept-choose-editor-surface.html")

    assert root.status_code == 503
    assert "Documentation build cannot be used" in root.text
    assert topic.status_code == 503
    assert "Documentation build cannot be used" in topic.text
    assert manifest_response.status_code == 503
    assert manifest_response.text == "Documentation artifact is not installed\n"

    _write_packaged_site(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ui_target_map"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with _client_with_docs(tmp_path, monkeypatch) as client:
        root = client.get("/help/")

    assert root.status_code == 503
    assert "Documentation build cannot be used" in root.text


def test_help_route_reports_stale_and_incomplete_artifact_states(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact"]["bpm_version"] = "0.9.4"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with _client_with_docs(tmp_path, monkeypatch) as client:
        stale = client.get("/help/ru/")

    assert stale.status_code == 503
    assert "Сборка документации не соответствует версии BPM" in stale.text

    _write_packaged_site(tmp_path)
    (tmp_path / "fr/index.html").unlink()

    with _client_with_docs(tmp_path, monkeypatch) as client:
        incomplete = client.get("/help/fr/")

    assert incomplete.status_code == 503
    assert "La documentation est incomplète" in incomplete.text


def test_documentation_manifest_helpers_reject_unsafe_and_malformed_inputs(
    tmp_path: Path,
) -> None:
    duplicate_json = tmp_path / "duplicate.json"
    duplicate_json.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    list_json = tmp_path / "list.json"
    list_json.write_text("[]", encoding="utf-8")

    for raw_path in ("\x00bad", "/absolute", "", ".", "a/../b"):
        assert docs_manifest._safe_artifact_path(raw_path) is None

    assert docs_manifest._safe_artifact_path("a/%2E/b.txt") == Path("a/b.txt")
    assert docs_manifest._resolve_artifact_file(tmp_path, "%2Fetc/passwd") is None
    assert docs_manifest._manifest_bpm_version({}) is None
    assert docs_manifest._manifest_bpm_version({"artifact": {"bpm_version": ""}}) is None

    with pytest.raises(ValueError, match="duplicate JSON key"):
        docs_manifest._load_json_object(duplicate_json)
    with pytest.raises(ValueError, match="must be a JSON object"):
        docs_manifest._load_json_object(list_json)

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    site_root = tmp_path / "site"
    site_root.mkdir()
    (site_root / "escape").symlink_to(outside)
    assert docs_manifest._resolve_artifact_file(site_root, "escape") is None


def test_documentation_catalog_target_resolution_fails_closed_for_partial_records(
    tmp_path: Path,
) -> None:
    _write_packaged_site(tmp_path)
    catalog = docs_manifest.load_documentation_catalog(tmp_path)
    assert catalog is not None

    assert catalog.resolve_target_url("topic:user-guide", "it") == "/help/en/index.html"

    cases: list[tuple[dict[str, object], dict[str, object], str]] = []
    manifest = _read_manifest(tmp_path)
    target_map = _read_target_map(tmp_path)
    topics = manifest["topics"]
    targets = target_map["targets"]
    assert isinstance(topics, dict)
    assert isinstance(targets, dict)

    bad_target_map = dict(target_map)
    bad_target_map["targets"] = []
    cases.append((manifest, bad_target_map, "topic:user-guide"))

    bad_target_map = json.loads(json.dumps(target_map))
    bad_target_map["targets"]["topic:user-guide"] = []
    cases.append((manifest, bad_target_map, "topic:user-guide"))

    bad_target_map = json.loads(json.dumps(target_map))
    bad_target_map["targets"]["topic:user-guide"]["topic_id"] = 42
    cases.append((manifest, bad_target_map, "topic:user-guide"))

    bad_manifest = json.loads(json.dumps(manifest))
    bad_manifest["topics"].pop("user-guide")
    cases.append((bad_manifest, target_map, "topic:user-guide"))

    bad_manifest = json.loads(json.dumps(manifest))
    bad_manifest["topics"]["user-guide"]["anchors"] = {}
    bad_target_map = json.loads(json.dumps(target_map))
    bad_target_map["targets"]["topic:user-guide"]["anchor_id"] = "missing"
    cases.append((bad_manifest, bad_target_map, "topic:user-guide"))

    bad_manifest = json.loads(json.dumps(manifest))
    bad_manifest["topics"]["user-guide"]["output"] = []
    cases.append((bad_manifest, target_map, "topic:user-guide"))

    bad_manifest = json.loads(json.dumps(manifest))
    bad_manifest["topics"]["user-guide"]["output"]["en"] = 42
    cases.append((bad_manifest, target_map, "topic:user-guide"))

    bad_manifest = json.loads(json.dumps(manifest))
    bad_manifest["topics"]["user-guide"]["output"]["en"] = "en/missing.html"
    cases.append((bad_manifest, target_map, "topic:user-guide"))

    for manifest_payload, target_map_payload, target_id in cases:
        broken_catalog = docs_manifest.DocumentationCatalog(
            site_root=tmp_path,
            manifest=manifest_payload,
            target_map=target_map_payload,
            locales=("en",),
            default_locale="en",
        )
        assert broken_catalog.resolve_target_url(target_id, "en") is None

    broken_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest=manifest,
        target_map=target_map,
        locales=("en", "ru"),
        default_locale="en",
    )
    topics["user-guide"]["output"]["ru"] = "ru/missing.html"
    assert broken_catalog.locale_urls_for_target("topic:user-guide") is None


def test_documentation_manifest_validation_failures_return_no_catalog(
    tmp_path: Path,
) -> None:
    def assert_invalid_site(
        mutate_manifest=None,
        mutate_target_map=None,
        *,
        remove_target_map: bool = False,
    ) -> None:
        _write_packaged_site(tmp_path)
        manifest = _read_manifest(tmp_path)
        target_map = _read_target_map(tmp_path)
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        _write_manifest(tmp_path, manifest)
        if remove_target_map:
            (tmp_path / "ui-target-map.json").unlink()
        else:
            if mutate_target_map is not None:
                mutate_target_map(target_map)
            _write_target_map(tmp_path, target_map)
        assert docs_manifest.load_documentation_catalog(tmp_path) is None

    assert_invalid_site(lambda manifest: manifest.update({"locales": ["en"]}))
    assert_invalid_site(lambda manifest: manifest.update({"default_locale": "it"}))
    assert_invalid_site(lambda manifest: manifest.update({"artifact": {}}))
    assert_invalid_site(lambda manifest: manifest.update({"ui_target_map": []}))
    assert_invalid_site(lambda manifest: manifest["ui_target_map"].pop("path"))
    assert_invalid_site(remove_target_map=True)
    assert_invalid_site(
        mutate_target_map=lambda target_map: target_map.update({"schema_version": 2})
    )
    assert_invalid_site(
        mutate_manifest=lambda manifest: manifest["ui_target_map"].update({"schema_version": 2})
    )
    assert_invalid_site(
        mutate_target_map=lambda target_map: target_map.update({"manifest_schema_version": 2})
    )
    assert_invalid_site(mutate_target_map=lambda target_map: target_map.update({"locales": ["en"]}))
    assert_invalid_site(
        mutate_target_map=lambda target_map: target_map.update({"bpm_version": "0.8.0"})
    )
    assert_invalid_site(mutate_target_map=lambda target_map: target_map.update({"targets": []}))
    assert_invalid_site(lambda manifest: manifest.update({"topics": []}))
    assert_invalid_site(lambda manifest: manifest["topics"].update({"broken": []}))
    assert_invalid_site(lambda manifest: manifest["topics"]["user-guide"].pop("output"))
    assert_invalid_site(
        lambda manifest: manifest["topics"]["user-guide"]["output"].update({"en": 42})
    )


def test_documentation_target_semantics_reject_malformed_records(tmp_path: Path) -> None:
    _write_packaged_site(tmp_path)
    manifest = _read_manifest(tmp_path)
    target_map = _read_target_map(tmp_path)

    malformed_cases = [
        ({"topics": []}, {"targets": {}}),
        ({"topics": {}}, {"targets": {"topic:user-guide": []}}),
        ({"topics": {}}, {"targets": {"topic:user-guide": {"kind": 1, "source_id": "user-guide"}}}),
        (
            {"topics": {}},
            {
                "targets": {
                    "topic:user-guide": {
                        "kind": "topic",
                        "source_id": "other",
                        "topic_id": "user-guide",
                    }
                }
            },
        ),
        (
            {"topics": {}},
            {
                "targets": {
                    "topic:user-guide": {
                        "kind": "topic",
                        "source_id": "user-guide",
                        "topic_id": "missing",
                    }
                }
            },
        ),
        (
            {"topics": {"user-guide": []}},
            {
                "targets": {
                    "topic:user-guide": {
                        "kind": "topic",
                        "source_id": "user-guide",
                        "topic_id": "user-guide",
                    }
                }
            },
        ),
        (
            {"topics": {"user-guide": {"anchors": {}}}},
            {
                "targets": {
                    "topic:user-guide": {
                        "kind": "topic",
                        "source_id": "user-guide",
                        "topic_id": "user-guide",
                        "anchor_id": "missing",
                    }
                }
            },
        ),
    ]

    for bad_manifest, bad_target_map in malformed_cases:
        with pytest.raises(ValueError):
            docs_manifest._validate_targets(bad_manifest, bad_target_map)

    manifest["topics"]["user-guide"]["anchors"]["a-home"] = "Home"
    target_map["targets"]["topic:user-guide"]["anchor_id"] = "a-home"
    docs_manifest._validate_targets(manifest, target_map)


def test_help_route_covers_locale_defaults_status_and_asset_edge_cases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    assert docs_router._settings_site_root().is_absolute()
    assert "Cross-Origin-Opener-Policy" not in docs_router._headers(html=False, status_code=200)
    assert docs_router._status_locale(None) == get_settings().DEFAULT_LOCALE

    fallback_status = docs_router._status_page_response(503, "unknown", locale="it")
    assert fallback_status.status_code == 503
    assert "Documentation build cannot be used" in fallback_status.body.decode("utf-8")

    empty_default = docs_router._default_locale(None, set())
    assert empty_default == get_settings().DEFAULT_LOCALE
    manifest_default = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest={},
        target_map={},
        locales=("en", "ru"),
        default_locale="ru",
    )
    assert docs_router._default_locale(manifest_default, {"ru"}) == "ru"
    assert docs_router._canonical_locale("zh", {"en", "zh-CN"}, "en") == "zh-CN"
    assert docs_router._canonical_locale("it", {"en"}, "en") == "en"

    for raw_path in ("\x00bad", "/absolute", "a/../b"):
        assert docs_router._safe_relative_path(raw_path) is None
    assert docs_router._safe_relative_path("") == Path("index.html")
    assert docs_router._safe_relative_path("en/") == Path("en/index.html")

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    site_root = tmp_path / "site"
    site_root.mkdir()
    (site_root / "escape").symlink_to(outside)
    assert docs_router._resolve_packaged_file(site_root, Path("escape")) is None
    assert docs_router._resolve_packaged_file(site_root, Path("missing.html")) is None

    _write_packaged_site(tmp_path)
    with _client_with_docs(tmp_path, monkeypatch) as client:
        weighted = client.get(
            "/help/",
            headers={"accept-language": "de;q=bad,fr;q=0,es-ES;q=0.7"},
        )
        png_missing = client.get("/help/en/assets/missing.png")
        empty_asset = client.get("/help/en/")
        search_missing = client.get("/help/search/missing.json")

    assert weighted.status_code == 307
    assert weighted.headers["location"] == "/help/es-ES/"
    assert png_missing.status_code == 404
    assert png_missing.text == "Documentation asset not found\n"
    assert empty_asset.status_code == 200
    assert search_missing.status_code == 404


def test_help_route_handles_manifest_without_locale_list_and_empty_catalog(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)
    manifest = _read_manifest(tmp_path)
    manifest["locales"] = "en"
    _write_manifest(tmp_path, manifest)

    with _client_with_docs(tmp_path, monkeypatch) as client:
        incompatible = client.get("/help/")

    assert incompatible.status_code == 503
    assert "Documentation build cannot be used" in incompatible.text

    _write_packaged_site(tmp_path)
    monkeypatch.setattr(
        docs_manifest,
        "load_documentation_catalog",
        lambda site_root=None: docs_manifest.DocumentationCatalog(
            site_root=site_root,
            manifest={},
            target_map={},
            locales=(),
            default_locale="en",
        ),
    )
    assert docs_router._artifact_problem(tmp_path) == "incomplete"


def test_help_route_canonical_redirect_helpers_cover_alias_anchor_and_bad_topics(
    tmp_path: Path,
) -> None:
    _write_packaged_site(tmp_path)
    catalog = docs_manifest.load_documentation_catalog(tmp_path)
    assert catalog is not None

    catalog.manifest["aliases"]["user/anchored"] = {
        "topic_id": "ug-concept-choose-editor-surface",
        "canonical_url_path": "user/ug-concept-choose-editor-surface",
        "anchor_id": "a-anchored",
    }
    redirect = docs_router._canonical_topic_redirect(
        locale="en",
        catalog=catalog,
        public_path="user/anchored",
    )
    assert redirect is not None
    assert (
        redirect.headers["location"] == "/help/en/user/ug-concept-choose-editor-surface/#a-anchored"
    )

    assert (
        docs_router._canonical_topic_redirect(locale="en", catalog=catalog, public_path="") is None
    )

    malformed_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest={"guides": [], "topics": {}},
        target_map={},
        locales=("en",),
        default_locale="en",
    )
    assert docs_router._topic_public_paths(malformed_catalog) == {}
    assert (
        docs_router._canonical_topic_redirect(
            locale="en",
            catalog=malformed_catalog,
            public_path="user/home",
        )
        is None
    )


def test_documentation_resolvers_fail_closed_for_missing_or_partial_catalogs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("BPM_DOCUMENTATION_SITE_DIR", "missing-relative-docs")
    get_settings.cache_clear()
    try:
        assert docs_manifest.load_documentation_catalog() is None
        assert docs_manifest.resolve_documentation_home_links() is None
        assert docs_manifest.resolve_documentation_contextual_help_links() == {}
        assert docs_manifest.resolve_documentation_deep_help_links() == {}
        assert docs_manifest.resolve_all_settings_row_help_links() == {}
        assert (
            docs_router._settings_site_root() == get_settings().ROOT_DIR / "missing-relative-docs"
        )
    finally:
        get_settings.cache_clear()

    _write_packaged_site(tmp_path)
    target_map = _read_target_map(tmp_path)
    targets = target_map["targets"]
    assert isinstance(targets, dict)
    targets.pop("topic:ug-task-use-profile-library")
    targets.pop("policy:AIControls")
    _write_target_map(tmp_path, target_map)

    contextual = docs_manifest.resolve_documentation_contextual_help_links(tmp_path)
    deep = docs_manifest.resolve_documentation_deep_help_links(tmp_path)
    row_help = docs_manifest.resolve_all_settings_row_help_links(tmp_path)

    assert "library" not in contextual
    assert "guided" in contextual
    assert "policy-ai-controls" not in deep
    assert "validation" in deep
    assert "known-preference:browser.download.dir" in row_help
    assert "policy:AIControls" not in row_help


def test_all_settings_row_help_resolver_fails_closed_for_malformed_catalogs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    malformed_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest={"topics": {}},
        target_map={"targets": []},
        locales=("en",),
        default_locale="en",
    )
    monkeypatch.setattr(
        docs_manifest,
        "load_documentation_catalog",
        lambda site_root=None: malformed_catalog,
    )
    assert docs_manifest.resolve_all_settings_row_help_links(tmp_path) == {}

    partial_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest={"topics": {}},
        target_map={
            "targets": {
                "policy:missing": {"kind": "policy", "topic_id": "missing"},
                "topic:user-guide": {"kind": "topic", "topic_id": "user-guide"},
            }
        },
        locales=("en",),
        default_locale="en",
    )
    monkeypatch.setattr(
        docs_manifest,
        "load_documentation_catalog",
        lambda site_root=None: partial_catalog,
    )
    assert docs_manifest.resolve_all_settings_row_help_links(tmp_path) == {}


def test_documentation_artifact_dispositions_match_help_status_states(tmp_path: Path) -> None:
    assert docs_manifest.resolve_documentation_artifact_disposition(tmp_path) == (
        "artifact_unavailable"
    )

    _write_packaged_site(tmp_path)
    assert docs_manifest.resolve_documentation_artifact_disposition(tmp_path) == "available"

    manifest = _read_manifest(tmp_path)
    artifact = manifest["artifact"]
    assert isinstance(artifact, dict)
    artifact["bpm_version"] = "0.0.0"
    _write_manifest(tmp_path, manifest)
    assert docs_manifest.resolve_documentation_artifact_disposition(tmp_path) == "artifact_stale"

    _write_packaged_site(tmp_path)
    manifest = _read_manifest(tmp_path)
    artifact = manifest["artifact"]
    assert isinstance(artifact, dict)
    artifact["documentation_version"] = "0.9.4"
    _write_manifest(tmp_path, manifest)
    assert (
        docs_manifest.resolve_documentation_artifact_disposition(tmp_path)
        == "artifact_incompatible"
    )

    _write_packaged_site(tmp_path)
    (tmp_path / "fr/index.html").unlink()
    assert docs_manifest.resolve_documentation_artifact_disposition(tmp_path) == (
        "artifact_incomplete"
    )

    _write_packaged_site(tmp_path)
    (tmp_path / "manifest.json").write_text("{", encoding="utf-8")
    assert docs_manifest.resolve_documentation_artifact_disposition(tmp_path) == (
        "artifact_incompatible"
    )


def test_help_status_pages_use_query_and_cookie_locales_for_missing_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    missing_site = tmp_path / "missing"

    with _client_with_docs(missing_site, monkeypatch) as client:
        query_locale = client.get("/help/?locale=fr")
        cookie_locale = client.get("/help/", headers={"cookie": "bpm_locale=es-ES"})
        no_slash = client.get("/help", follow_redirects=False)

    assert query_locale.status_code == 503
    assert "La documentation n’est pas installée" in query_locale.text
    assert cookie_locale.status_code == 503
    assert "La documentación no está instalada" in cookie_locale.text
    assert no_slash.status_code == 307
    assert no_slash.headers["location"] == "/help/"


def test_help_artifact_problem_and_public_path_helpers_cover_remaining_edges(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_packaged_site(tmp_path)
    (tmp_path / "manifest.json").write_text("{", encoding="utf-8")
    assert docs_router._artifact_problem(tmp_path) == "incompatible"

    _write_packaged_site(tmp_path)
    (tmp_path / "ru/index.html").unlink()
    monkeypatch.setattr(
        docs_manifest,
        "load_documentation_catalog",
        lambda site_root=None: docs_manifest.DocumentationCatalog(
            site_root=site_root,
            manifest={},
            target_map={},
            locales=("en", "ru"),
            default_locale="en",
        ),
    )
    manifest = _read_manifest(tmp_path)
    manifest["locales"] = "not-a-list"
    _write_manifest(tmp_path, manifest)
    assert docs_router._artifact_problem(tmp_path) == "incomplete"

    catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest={
            "guides": {
                "valid": {"url_root": "user"},
                "bad-root": {"url_root": 42},
            },
            "topics": {
                "skip-non-dict": [],
                "skip-missing-guide": {"guide_id": "missing", "url_path": "topic"},
                "skip-bad-guide": {"guide_id": "bad-root", "url_path": "topic"},
                "skip-bad-path": {"guide_id": "valid", "url_path": 42},
                "ok": {"guide_id": "valid", "url_path": "ok"},
            },
        },
        target_map={},
        locales=("en",),
        default_locale="en",
    )
    assert docs_router._topic_public_paths(catalog) == {
        "user/ok": {"guide_id": "valid", "url_path": "ok"}
    }

    manifest = _read_manifest(tmp_path)
    malformed_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest=manifest,
        target_map={},
        locales=("en",),
        default_locale="en",
    )
    manifest["topics"]["user-guide"]["output"] = []
    assert (
        docs_router._canonical_topic_redirect(
            locale="en",
            catalog=malformed_catalog,
            public_path="user/home",
        )
        is None
    )


def test_help_router_internal_fallbacks_cover_default_site_and_alias_edges(
    tmp_path: Path,
) -> None:
    _write_packaged_site(tmp_path)
    catalog = docs_manifest.load_documentation_catalog(tmp_path)
    assert catalog is not None

    assert docs_router._site_is_available(tmp_path) is True
    assert docs_router._default_locale(catalog, {"ru"}) == "ru"

    catalog.manifest["aliases"]["user/bad-alias"] = {
        "topic_id": "ug-concept-choose-editor-surface",
        "canonical_url_path": 42,
    }
    assert (
        docs_router._canonical_topic_redirect(
            locale="en",
            catalog=catalog,
            public_path="user/bad-alias",
        )
        is None
    )

    manifest = _read_manifest(tmp_path)
    malformed_catalog = docs_manifest.DocumentationCatalog(
        site_root=tmp_path,
        manifest=manifest,
        target_map={},
        locales=("en",),
        default_locale="en",
    )
    manifest["topics"]["user-guide"]["output"].pop("en")
    assert (
        docs_router._canonical_topic_redirect(
            locale="en",
            catalog=malformed_catalog,
            public_path="user/home",
        )
        is None
    )
