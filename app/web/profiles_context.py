from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

from fastapi import Request

from app.core.locales import (
    LOCALE_MATRIX,
    resolve_active_catalog_locale_code,
    resolve_target_locale_code,
)
from app.core.schema_channels import build_schema_channels_catalog
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from app.web.firefox_wizard_steps import get_wizard_steps

SettingsShellFocusResolver = Callable[[str | None, str | None, dict[str, object] | None], int | None]


@cache
def _load_locale_catalog_from_path(root_dir: str, i18n_dir: str, locale: str) -> dict[str, str]:
    locale_path = Path(root_dir) / i18n_dir / f"{locale}.json"
    if not locale_path.is_file():
        return {}
    return json.loads(locale_path.read_text(encoding="utf-8"))


def load_locale_catalog(locale: str, settings_obj: Any) -> dict[str, str]:
    return _load_locale_catalog_from_path(
        str(settings_obj.ROOT_DIR),
        str(settings_obj.I18N_DIR),
        locale,
    )


def clear_locale_catalog_cache() -> None:
    _load_locale_catalog_from_path.cache_clear()


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
    wizard_settings_catalog = get_wizard_settings_catalog()
    wizard_preferences_catalog = get_wizard_preferences_catalog(wizard_settings_catalog)
    wizard_schema_shell_catalog = get_wizard_schema_shell_catalog(wizard_preferences_catalog)
    all_settings_category_catalog = get_all_settings_category_catalog()
    initial_lang = resolve_request_locale(request, settings_obj)
    initial_locale = load_locale_catalog(initial_lang, settings_obj)

    def tr(key: str, fallback: str = "") -> str:
        value = initial_locale.get(key)
        if isinstance(value, str) and value:
            return value
        return fallback

    return {
        "title": title,
        "app_name": settings_obj.APP_NAME,
        "app_version": settings_obj.APP_VERSION,
        "asset_version": resolve_profiles_asset_version(settings_obj),
        "footer_year_range": footer_year_range,
        "profiles_route_mode": route_mode,
        "editing_profile_id": editing_profile_id,
        "editing_profile_schema_version": editing_profile_schema_version,
        "editing_profile_initial": editing_profile_initial,
        "include_deleted": include_deleted,
        "return_url": return_url,
        "focus_target": focus_target,
        "settings_href": settings_href,
        "json_href": json_href,
        "clone_source_id": clone_source_id,
        "clone_name": clone_name,
        "wizard_settings_catalog": wizard_settings_catalog,
        "wizard_preferences_catalog": wizard_preferences_catalog,
        "wizard_preferences_sections_by_id": {
            section["id"]: section
            for section in wizard_preferences_catalog.get("sections", [])
            if isinstance(section, dict) and section.get("id")
        },
        "wizard_manual_policy_controls": get_manual_policy_controls_catalog(),
        "wizard_starter_catalog": get_wizard_starter_catalog(),
        "wizard_steps": get_wizard_steps(),
        "wizard_schema_shell_catalog": wizard_schema_shell_catalog,
        "all_settings_category_catalog": all_settings_category_catalog,
        "settings_shell_step_to_open": settings_shell_focus_resolver(
            focus_target,
            editing_profile_schema_version,
            wizard_schema_shell_catalog,
        ),
        "schema_channels_catalog": build_schema_channels_catalog(),
        "locale_picker_options": LOCALE_MATRIX,
        "initial_lang": initial_lang,
        "initial_locale": initial_locale,
        "tr": tr,
    }
