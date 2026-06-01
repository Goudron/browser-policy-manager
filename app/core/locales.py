"""Locale matrix for Browser Policy Manager UI localization.

English remains the source product language. ``ACTIVE_CATALOG_LOCALES`` lists
catalogs that are currently shippable at runtime; ``TARGET_UI_LOCALES`` records
the first-class locale set being prepared by the global locale expansion work.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocaleDefinition:
    code: str
    bcp47: str
    english_name: str
    native_name: str
    fallback: str
    browser_language_matches: tuple[str, ...]
    has_catalog: bool


SOURCE_LOCALE = "en"
DEFAULT_LOCALE = SOURCE_LOCALE

LOCALE_MATRIX: tuple[LocaleDefinition, ...] = (
    LocaleDefinition(
        code="en",
        bcp47="en",
        english_name="English",
        native_name="English",
        fallback="en",
        browser_language_matches=("en", "en-*"),
        has_catalog=True,
    ),
    LocaleDefinition(
        code="ru",
        bcp47="ru",
        english_name="Russian",
        native_name="Русский",
        fallback="en",
        browser_language_matches=("ru", "ru-*"),
        has_catalog=True,
    ),
    LocaleDefinition(
        code="de",
        bcp47="de",
        english_name="German",
        native_name="Deutsch",
        fallback="en",
        browser_language_matches=("de", "de-*"),
        has_catalog=True,
    ),
    LocaleDefinition(
        code="zh-CN",
        bcp47="zh-CN",
        english_name="Simplified Chinese",
        native_name="简体中文",
        fallback="en",
        browser_language_matches=("zh-CN", "zh-Hans", "zh-Hans-*", "zh"),
        has_catalog=True,
    ),
    LocaleDefinition(
        code="fr",
        bcp47="fr",
        english_name="French",
        native_name="Français",
        fallback="en",
        browser_language_matches=("fr", "fr-*"),
        has_catalog=True,
    ),
    LocaleDefinition(
        code="es-ES",
        bcp47="es-ES",
        english_name="Spanish",
        native_name="Español",
        fallback="en",
        browser_language_matches=("es-ES", "es", "es-*"),
        has_catalog=True,
    ),
)

TARGET_UI_LOCALES = tuple(locale.code for locale in LOCALE_MATRIX)
ACTIVE_CATALOG_LOCALES = tuple(
    locale.code for locale in LOCALE_MATRIX if locale.has_catalog
)
LOCALE_FALLBACKS = {locale.code: locale.fallback for locale in LOCALE_MATRIX}
LOCALE_BROWSER_LANGUAGE_MATCHES = {
    locale.code: locale.browser_language_matches for locale in LOCALE_MATRIX
}

_LOCALE_BY_CODE = {locale.code: locale for locale in LOCALE_MATRIX}


def _normalize_language_tag(language_tag: str) -> str:
    return language_tag.strip().replace("_", "-").lower()


def _language_matches_rule(language_tag: str, rule: str) -> bool:
    normalized_tag = _normalize_language_tag(language_tag)
    normalized_rule = _normalize_language_tag(rule)
    if not normalized_tag or not normalized_rule:
        return False
    if normalized_rule.endswith("-*"):
        prefix = normalized_rule[:-2]
        return normalized_tag.startswith(f"{prefix}-")
    return normalized_tag == normalized_rule


def resolve_target_locale_code(language_tag: str) -> str:
    """Resolve a browser language tag to a canonical target UI locale code."""

    for locale in LOCALE_MATRIX:
        if any(
            _language_matches_rule(language_tag, rule)
            for rule in locale.browser_language_matches
        ):
            return locale.code
    return DEFAULT_LOCALE


def resolve_active_catalog_locale_code(
    language_tag: str,
    active_catalog_locales: tuple[str, ...] = ACTIVE_CATALOG_LOCALES,
) -> str:
    """Resolve a browser language tag to a currently loadable locale catalog."""

    active_locales = set(active_catalog_locales)
    target_locale = resolve_target_locale_code(language_tag)
    if target_locale in active_locales:
        return target_locale

    seen_locales = {target_locale}
    fallback_locale = _LOCALE_BY_CODE.get(
        target_locale, _LOCALE_BY_CODE[DEFAULT_LOCALE]
    ).fallback
    while fallback_locale and fallback_locale not in seen_locales:
        if fallback_locale in active_locales:
            return fallback_locale
        seen_locales.add(fallback_locale)
        fallback_locale = _LOCALE_BY_CODE.get(
            fallback_locale, _LOCALE_BY_CODE[DEFAULT_LOCALE]
        ).fallback

    if DEFAULT_LOCALE in active_locales:
        return DEFAULT_LOCALE
    if active_catalog_locales:
        return active_catalog_locales[0]
    return DEFAULT_LOCALE
