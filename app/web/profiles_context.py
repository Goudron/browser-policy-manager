from __future__ import annotations

import hashlib
import json
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any, cast

from fastapi import Request

from app.core.locales import (
    LOCALE_MATRIX,
    resolve_active_catalog_locale_code,
    resolve_target_locale_code,
)
from app.core.schema_channels import (
    SCHEMA_CHANNELS,
    SCHEMA_FILENAMES,
    build_schema_channels_catalog,
)
from app.documentation.manifest import (
    DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS,
    DOCUMENTATION_DEEP_HELP_TARGET_IDS,
    DOCUMENTATION_LOCALES,
    resolve_all_settings_row_help_links,
    resolve_documentation_artifact_disposition,
    resolve_documentation_contextual_help_links,
    resolve_documentation_deep_help_links,
    resolve_documentation_home_links,
)
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from app.web.firefox_wizard_steps import get_wizard_steps

SettingsShellFocusResolver = Callable[
    [str | None, str | None, dict[str, object] | None], int | None
]
_PROFILE_FRONTEND_BUNDLE_MANIFEST = "profiles_bundles/profiles-bundles-manifest.json"
_PROFILE_FRONTEND_ROUTE_MODES = frozenset({"library", "compare", "new", "edit", "settings", "json"})


# Route payloads are deliberately narrower than the worker-local catalog cache.
# The latter is a convenient immutable construction boundary; the browser only
# receives the artifacts that its template and entrypoint can consume.
_ROUTE_CATALOG_KEYS: dict[str, tuple[str, ...]] = {
    "library": ("schema_channels_catalog",),
    "compare": ("wizard_preferences_catalog", "schema_channels_catalog"),
    "new": (
        "wizard_settings_catalog",
        "wizard_preferences_catalog",
        "wizard_manual_policy_controls",
        "wizard_starter_catalog",
        "wizard_steps",
        "wizard_schema_shell_catalog",
        "schema_channels_catalog",
    ),
    "edit": (
        "wizard_settings_catalog",
        "wizard_preferences_catalog",
        "wizard_manual_policy_controls",
        "wizard_starter_catalog",
        "wizard_steps",
        "wizard_schema_shell_catalog",
        "schema_channels_catalog",
    ),
    "settings": (
        "wizard_settings_catalog",
        "wizard_preferences_catalog",
        "wizard_preferences_sections_by_id",
        "wizard_schema_shell_catalog",
        "all_settings_category_catalog",
        "schema_channels_catalog",
        "documentation_all_settings_row_help_links",
        "documentation_all_settings_row_help_status",
    ),
    "json": ("wizard_schema_shell_catalog", "schema_channels_catalog"),
}

_ROUTE_CONTEXTUAL_HELP_SURFACES: dict[str, tuple[str, ...]] = {
    "compare": ("compare",),
    "new": ("guided",),
    "edit": ("guided",),
    "settings": ("settings",),
    "json": ("json",),
}

_ROUTE_DEEP_HELP_TARGETS: dict[str, tuple[str, ...]] = {
    "library": ("import-firefox-policies",),
    "new": (
        "validation",
        "policy-ai-controls",
        "policy-visual-search-enabled",
        "export-firefox-policies",
        "cis-baseline-selection",
    ),
    "edit": (
        "validation",
        "policy-ai-controls",
        "policy-visual-search-enabled",
        "export-firefox-policies",
        "cis-baseline-selection",
    ),
    "settings": ("validation",),
    "json": ("validation", "export-firefox-policies"),
}


@cache
def _file_sha256_for_stat(path_text: str, mtime_ns: int, size: int) -> str:
    """Return a content identity while avoiding repeat reads of unchanged files.

    The stat tuple merely makes hashing cheap on the hot path.  Catalog cache
    keys use the resulting digest, rather than a clock value, so a changed
    artifact receives a new immutable snapshot.
    """

    del mtime_ns, size
    return hashlib.sha256(Path(path_text).read_bytes()).hexdigest()


def _file_content_identity(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"missing:{path}"
    return _file_sha256_for_stat(str(path), stat.st_mtime_ns, stat.st_size)


@cache
def _load_locale_catalog_from_path(
    root_dir: str,
    i18n_dir: str,
    locale: str,
    artifact_identity: str,
) -> tuple[tuple[str, str], ...]:
    del artifact_identity
    locale_path = Path(root_dir) / i18n_dir / f"{locale}.json"
    if not locale_path.is_file():
        return ()
    payload = json.loads(locale_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ()
    return tuple(
        (key, value)
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str)
    )


def load_locale_catalog(locale: str, settings_obj: Any) -> dict[str, str]:
    locale_path = Path(settings_obj.ROOT_DIR) / str(settings_obj.I18N_DIR) / f"{locale}.json"
    # Materialize a fresh dict so a request/template cannot mutate the
    # worker-local immutable locale cache.
    return dict(
        _load_locale_catalog_from_path(
            str(settings_obj.ROOT_DIR),
            str(settings_obj.I18N_DIR),
            locale,
            _file_content_identity(locale_path),
        )
    )


def clear_locale_catalog_cache() -> None:
    _load_locale_catalog_from_path.cache_clear()


def _schema_catalog_identity() -> tuple[str, ...]:
    """Identify every external artifact used by schema-backed wizard catalogs."""

    policies_dir = Path(__file__).resolve().parents[1] / "schemas" / "policies"
    cis_dir = Path(__file__).resolve().parents[1] / "compliance" / "firefox" / "cis"
    schema_identities = tuple(
        _file_content_identity(policies_dir / filename) for filename in SCHEMA_FILENAMES.values()
    )
    cis_identities = tuple(
        _file_content_identity(cis_dir / filename)
        for filename in (
            "firefox_esr_gpo_1_0_0.yaml",
            "mappings.yaml",
            "schema.yaml",
            "sources.yaml",
            "merge_rules.yaml",
        )
    )
    return schema_identities + cis_identities


def _documentation_catalog_identity() -> str:
    """Return the identity of the manifest and its UI target-map payload.

    These two artifacts own the link catalog.  HTML/PDF output changes that do
    not alter targets intentionally retain the same link snapshot.
    """

    from app.core.config import get_settings

    runtime_settings = get_settings()
    root = Path(runtime_settings.DOCUMENTATION_SITE_DIR)
    if not root.is_absolute():
        root = runtime_settings.ROOT_DIR / root
    manifest_path = root / "manifest.json"
    manifest_identity = _file_content_identity(manifest_path)
    if not manifest_path.is_file():
        return manifest_identity
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        target_map_path = manifest.get("ui_target_map", {}).get("path")
    except OSError:
        return manifest_identity
    except ValueError:
        return manifest_identity
    except AttributeError:
        return manifest_identity
    if not isinstance(target_map_path, str):
        return manifest_identity
    try:
        target_map = (root / target_map_path).resolve()
        target_map.relative_to(root.resolve())
    except ValueError:
        return manifest_identity
    return f"{manifest_identity}:{_file_content_identity(target_map)}"


@cache
def _build_profiles_page_catalog_json(
    schema_artifact_identity: tuple[str, ...],
    documentation_artifact_identity: str,
) -> str:
    """Build the shared immutable catalog portion of a profiles page.

    JSON is the immutable cache representation.  Callers receive a newly
    decoded payload, preserving Jinja-compatible dict/list shapes without
    exposing worker-local state to mutation.
    """

    del schema_artifact_identity, documentation_artifact_identity
    wizard_settings_catalog = get_wizard_settings_catalog()
    wizard_preferences_catalog = get_wizard_preferences_catalog(wizard_settings_catalog)
    wizard_schema_shell_catalog = get_wizard_schema_shell_catalog(wizard_preferences_catalog)
    documentation_home_links = resolve_documentation_home_links()
    documentation_context_help_links = resolve_documentation_contextual_help_links()
    documentation_deep_help_links = resolve_documentation_deep_help_links()
    if documentation_home_links is None:
        documentation_home_links = _documentation_status_links()
        documentation_context_help_links = _documentation_status_contextual_help_links()
        documentation_deep_help_links = _documentation_status_deep_help_links()

    return json.dumps(
        {
            "wizard_settings_catalog": wizard_settings_catalog,
            "wizard_preferences_catalog": wizard_preferences_catalog,
            "wizard_manual_policy_controls": get_manual_policy_controls_catalog(),
            "wizard_starter_catalog": get_wizard_starter_catalog(include_compliance=False),
            "wizard_steps": get_wizard_steps(),
            "wizard_schema_shell_catalog": wizard_schema_shell_catalog,
            "all_settings_category_catalog": get_all_settings_category_catalog(),
            "documentation_home_links": documentation_home_links,
            "documentation_context_help_links": documentation_context_help_links,
            "documentation_deep_help_links": documentation_deep_help_links,
            "documentation_all_settings_row_help_links": resolve_all_settings_row_help_links(),
            "documentation_all_settings_row_help_status": (
                resolve_documentation_artifact_disposition()
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _profiles_page_catalog() -> dict[str, object]:
    payload = _build_profiles_page_catalog_json(
        _schema_catalog_identity(),
        _documentation_catalog_identity(),
    )
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):  # pragma: no cover - JSON is built above.
        raise RuntimeError("Profiles page catalog cache is malformed")
    wizard_preferences_catalog = decoded["wizard_preferences_catalog"]
    if not isinstance(wizard_preferences_catalog, dict):  # pragma: no cover
        raise RuntimeError("Profiles preferences catalog cache is malformed")
    sections = wizard_preferences_catalog.get("sections", [])
    decoded["wizard_preferences_sections_by_id"] = {
        section["id"]: section
        for section in sections
        if isinstance(section, dict) and isinstance(section.get("id"), str)
    }
    return decoded


def clear_profiles_page_catalog_cache() -> None:
    """Clear worker-local immutable profiles page catalogs for artifact tests."""

    _build_profiles_page_catalog_json.cache_clear()
    _file_sha256_for_stat.cache_clear()


@cache
def _resolve_profiles_asset_version_from_paths(
    static_dir: str,
    templates_dir: str,
    app_version: str,
) -> str:
    latest_mtime = 0
    for root in (Path(static_dir), Path(templates_dir)):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            latest_mtime = max(latest_mtime, int(path.stat().st_mtime))
    return str(latest_mtime or app_version)


def resolve_profiles_asset_version(settings_obj: Any) -> str:
    return _resolve_profiles_asset_version_from_paths(
        str(settings_obj.STATIC_DIR),
        str(settings_obj.TEMPLATES_DIR),
        str(settings_obj.APP_VERSION),
    )


@cache
def _load_profile_frontend_assets_for_stat(
    path_text: str,
    mtime_ns: int,
    size: int,
) -> dict[str, object]:
    """Load the build-owned route manifest for one immutable file identity."""

    del mtime_ns, size
    try:
        payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Profile frontend bundle manifest is unavailable: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Profile frontend bundle manifest is invalid")
    routes = payload.get("routes")
    if (
        payload.get("schema_version") != 1
        or not isinstance(routes, dict)
        or set(routes) != _PROFILE_FRONTEND_ROUTE_MODES
        or not isinstance(payload.get("head_script"), str)
    ):
        raise RuntimeError("Profile frontend bundle manifest is invalid")
    return payload


def load_profile_frontend_assets(static_dir: Path) -> dict[str, object]:
    """Return the checked-in route assets, with safe local build invalidation."""

    manifest_path = static_dir / _PROFILE_FRONTEND_BUNDLE_MANIFEST
    try:
        stat = manifest_path.stat()
    except OSError as error:
        raise RuntimeError(
            "Profile frontend bundles are missing; run make build-profile-frontend-bundles."
        ) from error
    return _load_profile_frontend_assets_for_stat(
        str(manifest_path), stat.st_mtime_ns, stat.st_size
    )


def clear_profile_frontend_assets_cache() -> None:
    """Reset the route manifest cache when a test replaces generated assets."""

    _load_profile_frontend_assets_for_stat.cache_clear()


def resolve_request_locale(request: Request, settings_obj: Any) -> str:
    supported = tuple(settings_obj.SUPPORTED_LOCALES)
    header = request.headers.get("accept-language", "")

    weighted_direct_locales: list[tuple[float, str]] = []
    weighted_fallback_locales: list[tuple[float, str]] = []
    for raw_part in header.split(","):
        part = raw_part.strip()
        if not part:
            continue
        lang, _, params = part.partition(";")
        lang = lang.strip()
        if not lang:
            continue
        weight = 1.0
        for param in params.split(";"):
            param = param.strip()
            if not param.startswith("q="):
                continue
            try:
                weight = float(param[2:])
            except ValueError:
                weight = 0.0
        if weight <= 0:
            continue
        target_locale = resolve_target_locale_code(lang)
        if target_locale in supported:
            weighted_direct_locales.append((weight, target_locale))
        else:
            weighted_fallback_locales.append(
                (weight, resolve_active_catalog_locale_code(lang, supported))
            )

    weighted_locales = weighted_direct_locales or weighted_fallback_locales
    if not weighted_locales:
        return settings_obj.DEFAULT_LOCALE

    weighted_locales.sort(key=lambda item: item[0], reverse=True)
    return weighted_locales[0][1]


def _documentation_status_links() -> dict[str, str]:
    return {
        locale: f"/help/?locale={urllib.parse.quote(locale, safe='-')}"
        for locale in DOCUMENTATION_LOCALES
    }


def _documentation_status_contextual_help_links() -> dict[str, dict[str, str]]:
    status_links = _documentation_status_links()
    return {
        surface_id: dict(status_links) for surface_id in DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS
    }


def _documentation_status_deep_help_links() -> dict[str, dict[str, str]]:
    status_links = _documentation_status_links()
    return {target_id: dict(status_links) for target_id in DOCUMENTATION_DEEP_HELP_TARGET_IDS}


def build_profiles_page_context(
    request: Request,
    *,
    settings_obj: Any,
    settings_shell_focus_resolver: SettingsShellFocusResolver,
    now: datetime | None = None,
    title: str,
    route_mode: str,
    editing_profile_id: int | None = None,
    editing_profile_schema_version: str | None = None,
    editing_profile_initial: dict[str, object] | None = None,
    include_deleted: bool = False,
    return_url: str | None = None,
    focus_target: str | None = None,
    settings_href: str | None = None,
    json_href: str | None = None,
    clone_source_id: int | None = None,
    clone_name: str | None = None,
) -> dict[str, object]:
    current_year = (now or datetime.now(UTC)).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"
    catalog = _profiles_page_catalog()
    route_catalog_keys = _ROUTE_CATALOG_KEYS[route_mode]
    wizard_schema_shell_catalog = cast(dict[str, object], catalog["wizard_schema_shell_catalog"])
    initial_lang = resolve_request_locale(request, settings_obj)
    initial_locale = load_locale_catalog(initial_lang, settings_obj)
    documentation_home_links = cast(dict[str, str], catalog["documentation_home_links"])
    documentation_context_help_links = cast(
        dict[str, dict[str, str]], catalog["documentation_context_help_links"]
    )
    documentation_deep_help_links = cast(
        dict[str, dict[str, str]], catalog["documentation_deep_help_links"]
    )

    def tr(key: str, fallback: str = "") -> str:
        value = initial_locale.get(key)
        if isinstance(value, str) and value:
            return value
        return fallback

    schema_channels_catalog = build_schema_channels_catalog(
        label_overrides={
            channel.value: tr(channel.i18n_key, channel.label) for channel in SCHEMA_CHANNELS
        }
    )
    schema_options = cast(list[dict[str, object]], schema_channels_catalog["options"])
    initial_schema_version = (
        editing_profile_initial.get("schema_version")
        if isinstance(editing_profile_initial, dict)
        else editing_profile_schema_version
    )
    active_schema_version = (
        initial_schema_version
        if isinstance(initial_schema_version, str) and initial_schema_version in SCHEMA_FILENAMES
        else schema_channels_catalog["default_channel"]
    )
    # The runtime lifecycle catalog has already applied the contract's public
    # header order; do not recreate ordering from a second tuple here.
    header_schema_options = list(schema_options)

    context: dict[str, object] = {
        "title": title,
        "app_name": settings_obj.APP_NAME,
        "app_version": settings_obj.APP_VERSION,
        "asset_version": resolve_profiles_asset_version(settings_obj),
        "profiles_frontend_assets": load_profile_frontend_assets(settings_obj.STATIC_DIR),
        "footer_year_range": footer_year_range,
        "profiles_route_mode": route_mode,
        "editing_profile_id": editing_profile_id,
        "editing_profile_schema_version": editing_profile_schema_version,
        "editing_profile_initial": editing_profile_initial,
        "active_schema_version": active_schema_version,
        "include_deleted": include_deleted,
        "return_url": return_url,
        "focus_target": focus_target,
        "settings_href": settings_href,
        "json_href": json_href,
        "clone_source_id": clone_source_id,
        "clone_name": clone_name,
        "header_schema_options": header_schema_options,
        "locale_picker_options": LOCALE_MATRIX,
        "initial_lang": initial_lang,
        "initial_locale": initial_locale,
        "documentation_home_links": documentation_home_links,
        "documentation_home_href": documentation_home_links.get(initial_lang),
        "documentation_context_help_links": {
            surface: documentation_context_help_links[surface]
            for surface in _ROUTE_CONTEXTUAL_HELP_SURFACES.get(route_mode, ())
            if surface in documentation_context_help_links
        },
        "documentation_deep_help_links": {
            target: documentation_deep_help_links[target]
            for target in _ROUTE_DEEP_HELP_TARGETS.get(route_mode, ())
            if target in documentation_deep_help_links
        },
        "tr": tr,
    }
    for key in route_catalog_keys:
        if key == "schema_channels_catalog":
            context[key] = schema_channels_catalog
        else:
            context[key] = catalog[key]
    context["profiles_catalog_keys"] = route_catalog_keys
    if route_mode == "settings":
        context["settings_shell_step_to_open"] = settings_shell_focus_resolver(
            focus_target,
            editing_profile_schema_version,
            wizard_schema_shell_catalog,
        )
    return context
