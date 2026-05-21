import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RU_LOCALE_PATH = REPO_ROOT / "app" / "i18n" / "ru.json"

ALLOWED_VISIBLE_LATIN_TOKENS = {
    # Brands, product names, and product/channel labels.
    "Benchmark",
    "Bing",
    "Browser",
    "DuckDuckGo",
    "Entra",
    "Everywhere",
    "Firefox",
    "Labs",
    "Level",
    "License",
    "Manager",
    "Microsoft",
    "Mozilla",
    "Origin",
    "Pocket",
    "Policy",
    "Public",
    "Release",
    "Suggest",
    "Windows",
    # Human-readable pieces of accepted multi-word technical/product names.
    "Client",
    "Encrypted",
    "Hello",
    "Preferences",
    # Literal or placeholder-like technical fragments intentionally shown in UI.
    "example",
    "false",
    "firefox",
    "local",
    "mailto",
    "q",
    "r",
    "source",
    "true",
    "true/false",
}


def _visible_latin_tokens(locale: dict[str, str]) -> set[str]:
    locale_text = "\n".join(
        value for value in locale.values() if isinstance(value, str)
    )
    scrubbed_text = locale_text
    for pattern in (
        r"\{[^}]+\}",  # runtime interpolation variables
        r"https?://\S+",  # URLs
        r"\b\S+@\S+\b",  # email-like placeholders and extension IDs
        r"\b[a-zA-Z][\w-]*(?:\.[\w-]+)+\b",  # dotted keys such as browser.startup.page
        r"\b[a-zA-Z][\w-]*:[\w-]+\b",  # about:config-like identifiers
    ):
        scrubbed_text = re.sub(pattern, " ", scrubbed_text)

    return set(
        re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*", scrubbed_text)
    )


def test_ru_locale_has_no_known_accidental_english_fragments():
    locale = json.loads(RU_LOCALE_PATH.read_text(encoding="utf-8"))
    locale_text = "\n".join(
        value for value in locale.values() if isinstance(value, str)
    )

    forbidden_fragments = (
        "allowlist",
        "approved-",
        "outcome-",
        "override-",
        "финального review",
        "Правила cookie",
        "SameSite для cookie",
        "Разрешения сайтов и cookie",
        "Контролов:",
        "Контролов обновлений",
        "Контролов дополнений",
        "Контролы обновлений",
        "DNS over HTTPS",
        "IP protection",
        "Firefox Home",
        "GenerativeAI",
        "AIControls",
        "Enabled",
        "Chatbot",
        "LinkPreviews",
        "TabGroups",
        "настройки Home",
        "поверхностями Home",
        "политики Home",
        "DoH-настроек",
    )
    for fragment in forbidden_fragments:
        assert fragment not in locale_text


def test_ru_locale_uses_mozilla_russian_terms_for_firefox_surfaces():
    locale = json.loads(RU_LOCALE_PATH.read_text(encoding="utf-8"))

    expected_terms = {
        "profiles.shell_policy_dnsover_https": "DNS через HTTPS",
        "profiles.wizard_shell_subsection_dns_over_https": "DNS через HTTPS",
        "profiles.wizard_home_step_summary_title": "Итог настройки домашней страницы",
        "profiles.wizard_home_surfaces_workflow_item_cards": "Карточки Домашней страницы Firefox",
        "profiles.wizard_privacy_vpn_title": "Встроенный VPN и защита IP-адреса",
        "profiles.wizard_export_guided_network_dns": "Настроек DNS через HTTPS: {count}",
    }
    for key, expected in expected_terms.items():
        assert locale[key] == expected


def test_ru_locale_visible_latin_tokens_stay_on_allowlist():
    locale = json.loads(RU_LOCALE_PATH.read_text(encoding="utf-8"))
    visible_tokens = _visible_latin_tokens(locale)

    allowed_by_shape = {
        token
        for token in visible_tokens
        if token.isupper()
        or any(character.isupper() for character in token[1:])
        or any(character.isdigit() for character in token)
    }
    unexpected_tokens = sorted(
        visible_tokens - allowed_by_shape - ALLOWED_VISIBLE_LATIN_TOKENS
    )

    assert unexpected_tokens == []
