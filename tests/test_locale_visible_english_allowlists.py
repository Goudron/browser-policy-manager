import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
ALLOWLIST_DOC_PATH = (
    REPO_ROOT / "docs" / "locale_visible_english_allowlists_2026-05-30.md"
)
PLACEHOLDER_RULES_PATH = (
    REPO_ROOT / "docs" / "locale_placeholder_identifier_rules_2026-05-29.md"
)


LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")

CORPORATE_CIS_L2_VISIBLE_KEYS = (
    "profiles.wizard_step_two_index_title",
    "profiles.wizard_step_two_index_body",
    "profiles.wizard_step_two_index_basics",
    "profiles.wizard_step_two_index_proxy",
    "profiles.wizard_step_two_index_trust",
    "profiles.wizard_step_two_index_review",
    "profiles.wizard_step_four_index_title",
    "profiles.wizard_step_four_index_body",
    "profiles.wizard_step_four_index_defaults",
    "profiles.wizard_step_four_index_engines",
    "profiles.wizard_step_four_index_suggestions",
    "profiles.wizard_settings_search_label",
    "profiles.wizard_settings_search_hint",
    "profiles.wizard_settings_search_empty",
    "profiles.wizard_general_policy_title",
    "profiles.wizard_general_policy_body",
    "profiles.wizard_general_policy_focus_hint",
    "profiles.wizard_general_policy_preset_updates_copy",
    "profiles.wizard_general_policy_preset_browser_prompt_copy",
    "profiles.wizard_general_policy_preset_downloads_copy",
    "profiles.policy_default_browser",
    "profiles.policy_default_browser_copy",
    "profiles.policy_disable_app_update",
    "profiles.policy_disable_app_update_copy",
    "profiles.policy_disable_system_addon_update",
    "profiles.policy_disable_system_addon_update_copy",
    "profiles.policy_prompt_downloads",
    "profiles.policy_prompt_downloads_copy",
    "profiles.wizard_proxy_title",
    "profiles.wizard_proxy_body",
    "profiles.wizard_proxy_preset_hint",
    "profiles.wizard_proxy_preset_defaults_title",
    "profiles.wizard_proxy_preset_none_title",
    "profiles.wizard_proxy_preset_system_title",
    "profiles.wizard_proxy_preset_manual_title",
    "profiles.wizard_proxy_section_state_system",
    "profiles.wizard_proxy_locked_label",
    "profiles.wizard_proxy_locked_copy",
    "profiles.wizard_cis_l2_copy",
    "profiles.wizard_cis_final_summary_applied",
    "profiles.wizard_cis_final_summary_satisfied",
    "profiles.wizard_cis_final_summary_kept",
    "profiles.wizard_cis_final_summary_manual",
    "profiles.settings_review_title",
    "profiles.settings_review_body",
    "profiles.settings_review_actions_label",
    "profiles.settings_review_summary_attention",
    "profiles.settings_review_summary_clear",
    "profiles.settings_review_open",
    "profiles.settings_review_unknown_title",
    "profiles.settings_review_unknown_body",
    "profiles.settings_review_deprecated_title",
    "profiles.settings_review_deprecated_body",
    "profiles.settings_review_raw_title",
    "profiles.settings_review_raw_body",
    "profiles.settings_review_invalid_title",
    "profiles.settings_review_invalid_body",
    "profiles.settings_category_browser_access_title",
    "profiles.settings_category_browser_access_body",
    "profiles.settings_category_home_startup_title",
    "profiles.settings_category_home_startup_body",
    "profiles.settings_category_search_navigation_title",
    "profiles.settings_category_search_navigation_body",
    "profiles.settings_category_privacy_security_title",
    "profiles.settings_category_privacy_security_body",
    "profiles.settings_category_users_addons_sites_title",
    "profiles.settings_category_users_addons_sites_body",
    "profiles.settings_category_ai_smart_features_title",
    "profiles.settings_category_ai_smart_features_body",
    "profiles.settings_category_raw_unmapped_title",
    "profiles.settings_category_raw_unmapped_body",
    "profiles.settings_search_label",
    "profiles.settings_search_placeholder",
    "profiles.settings_search_hint",
    "profiles.settings_search_empty",
    "profiles.settings_map_title",
    "profiles.settings_map_body",
)

ALLOWED_SHARED_ENGLISH_PHRASES = {
    "Firefox",
    "Mozilla",
    "BPM",
    "CIS",
    "Level 1",
    "Level 2",
    "AI",
    "AMO",
    "API",
    "CSV",
    "DNS",
    "DoH",
    "ESR",
    "HTML",
    "Intune",
    "JSON",
    "Release",
    "URI",
    "VPN",
    "YAML",
    "HTTPS",
    "HTTP proxy",
    "SSL",
    "FTP",
    "SOCKS",
    "SOCKS v5",
    "PAC URL",
    "WPAD",
    "DuckDuckGo",
    "Browser Policy Manager",
    "Encrypted Client Hello",
    "POST payload",
    "SSL proxy",
    "Validation OK",
    "add-on ID",
    "Microsoft Entra",
    "Mozilla Public License",
    "AdGuard AdBlocker",
    "uBlock Origin",
    "Valery Ledovskoy",
    "Licensed under",
    "Copyright",
}

LATIN_TECHNICAL_TERMS = {
    "AdBlocker",
    "AdGuard",
    "AI",
    "AMO",
    "API",
    "Add",
    "BPM",
    "Bing",
    "Browser",
    "CA",
    "Chrome",
    "Chromium",
    "CIS",
    "Cookie",
    "Copyright",
    "CSV",
    "DNS",
    "DoH",
    "DuckDuckGo",
    "Edge",
    "Entra",
    "ESR",
    "Captive",
    "FIDO",
    "Firefox",
    "FTP",
    "GitHub",
    "Google",
    "GPO",
    "HTML",
    "HTTP",
    "HTTPS",
    "Intune",
    "JSON",
    "Max",
    "Min",
    "Kerberos",
    "LDAP",
    "License",
    "Level",
    "Ledovskoy",
    "Licensed",
    "Linux",
    "LTS",
    "macOS",
    "Manager",
    "Microsoft",
    "MIME",
    "Mozilla",
    "Portal",
    "NTLM",
    "OCSP",
    "OIDC",
    "Origin",
    "PAC",
    "POST",
    "PDF",
    "PKI",
    "Pocket",
    "Policy",
    "Public",
    "Qwant",
    "Release",
    "SSLVersion",
    "SAML",
    "S",
    "SameSite",
    "SOCKS",
    "SPNEGO",
    "SSO",
    "Startpage",
    "U2F",
    "URI",
    "URL",
    "UTF",
    "UTF-8",
    "VPN",
    "WebAuthn",
    "Windows",
    "WPAD",
    "XML",
    "YAML",
    "YouTube",
    "Wiki",
    "about",
    "addons",
    "addon",
    "bad",
    "config",
    "Ctrl",
    "example",
    "ico",
    "id",
    "js",
    "org",
    "owner",
    "page",
    "profiles",
    "proxy",
    "startup",
    "www",
    "xpi",
    "uBlock",
    "policies",
    "json",
    "local",
    "q",
    "source",
    "under",
    "Valery",
}

COMMON_UNTRANSLATED_PROSE_FRAGMENTS = (
    "Open profile",
    "Save changes",
    "Use this when",
    "Task-first setup",
)

LOCALE_ALLOWED_EXAMPLES = {
    "ru": (
        "Firefox policies.json",
        "DNS через HTTPS",
        "VPN",
        "ESR 140.11",
        "Release 151",
    ),
    "de": (
        "Firefox policies.json",
        "Mozilla-Konto",
        "DNS über HTTPS",
        "Add-ons",
        "Cookies",
    ),
    "zh-CN": (
        "Firefox policies.json",
        "Mozilla 账号",
        "基于 HTTPS 的 DNS",
        "Cookie",
        "内置 VPN",
    ),
    "fr": (
        "Firefox policies.json",
        "compte Mozilla",
        "DNS via HTTPS",
        "VPN intégré",
        "JSON",
    ),
    "es-ES": (
        "Firefox policies.json",
        "Mozilla account",
        "Mozilla accounts",
        "DNS sobre HTTPS",
        "VPN integrada",
    ),
}

LOCALE_FORBIDDEN_FRAGMENTS = {
    "ru": (
        "DNS over HTTPS",
        "IP protection",
        "Firefox Home",
        "Enabled",
        "Chatbot",
        "LinkPreviews",
        "TabGroups",
    ),
    "de": (
        "Private browsing",
        "DNS-over-HTTPS",
        "Firefox Account",
        "Mozilla account",
        "Built-in VPN",
    ),
    "zh-CN": (
        "Mozilla 账户",
        "DNS over HTTPS",
        "DNS-over-HTTPS",
        "Built-in VPN",
        "Mozilla sign-in",
    ),
    "fr": (
        "compte Mozillas",
        "DNS over HTTPS",
        "DNS-over-HTTPS",
        "Private browsing",
        "AI & fonctionnalités intelligentes",
        "AI and fonctionnalités intelligentes",
    ),
    "es-ES": (
        "cuenta Mozillas",
        "DNS over HTTPS",
        "DNS-over-HTTPS",
        "Private browsing",
        "AI & funciones inteligentes",
        "AI and funciones inteligentes",
    ),
}

AUDITED_KEYS = {
    "ru": (
        "profiles.shell_policy_dnsover_https",
        "profiles.wizard_shell_subsection_dns_over_https",
        "profiles.wizard_home_step_summary_title",
        "profiles.wizard_home_surfaces_workflow_item_cards",
        "profiles.wizard_privacy_vpn_title",
        "profiles.wizard_export_guided_network_dns",
    ),
    "de": (
        "profiles.shell_policy_disable_firefox_accounts",
        "profiles.wizard_settings_sync_account",
        "profiles.wizard_preferences_group_sync_account",
        "profiles.policy_disable_accounts",
        "profiles.shell_policy_private_browsing_mode_availability",
        "profiles.schema_field_private_browsing",
        "profiles.wizard_doh_state_empty",
        "profiles.wizard_doh_state_invalid",
        "profiles.wizard_review_search_suggestions_on",
        "profiles.wizard_review_search_suggestions_off",
    ),
    "zh-CN": (
        "profiles.shell_policy_disable_firefox_accounts",
        "profiles.wizard_sync_title",
        "profiles.wizard_sync_section_state_accounts_disabled",
        "profiles.wizard_shell_subsection_dns_over_https",
        "profiles.shell_policy_dnsover_https",
        "profiles.wizard_doh_state_empty",
        "profiles.wizard_doh_state_invalid",
        "profiles.wizard_review_search_suggestions_on",
        "profiles.wizard_review_search_suggestions_off",
        "profiles.wizard_privacy_vpn_section_state_available",
        "profiles.wizard_export_guided_privacy_vpn_available",
    ),
    "fr": (
        "profiles.settings_category_users_addons_sites_body",
        "profiles.wizard_step_four_copy",
        "profiles.shell_policy_disable_firefox_accounts",
        "profiles.wizard_sync_title",
        "profiles.wizard_sync_section_state_accounts_disabled",
        "profiles.wizard_shell_subsection_dns_over_https",
        "profiles.shell_policy_dnsover_https",
        "profiles.wizard_doh_state_empty",
        "profiles.wizard_doh_state_invalid",
        "profiles.shell_policy_private_browsing_mode_availability",
        "profiles.schema_field_private_browsing",
        "profiles.wizard_step_five",
        "profiles.wizard_progress_five",
    ),
    "es-ES": (
        "profiles.settings_category_users_addons_sites_body",
        "profiles.wizard_step_four_copy",
        "profiles.shell_policy_disable_firefox_accounts",
        "profiles.wizard_sync_title",
        "profiles.wizard_sync_section_state_accounts_disabled",
        "profiles.wizard_shell_subsection_dns_over_https",
        "profiles.shell_policy_dnsover_https",
        "profiles.wizard_doh_state_empty",
        "profiles.wizard_doh_state_invalid",
        "profiles.shell_policy_private_browsing_mode_availability",
        "profiles.schema_field_private_browsing",
        "profiles.wizard_step_five",
        "profiles.wizard_progress_five",
    ),
}


def _load_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _english_source_phrases(value: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*", value)
    phrases = set()
    for size in (4, 3, 2):
        for index in range(len(words) - size + 1):
            phrase = " ".join(words[index : index + size])
            if any(allowed in phrase or phrase in allowed for allowed in ALLOWED_SHARED_ENGLISH_PHRASES):
                continue
            phrases.add(phrase)
    return phrases


def _all_english_source_phrases(value: str) -> set[str]:
    allowed_terms = {term.lower() for term in LATIN_TECHNICAL_TERMS}
    source_words = [
        word
        for word in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*", value)
        if word.lower() not in allowed_terms
    ]
    phrases = set()
    for size in (5, 4, 3, 2):
        for index in range(len(source_words) - size + 1):
            phrase = " ".join(source_words[index : index + size])
            if any(
                allowed.lower() in phrase.lower()
                or phrase.lower() in allowed.lower()
                for allowed in ALLOWED_SHARED_ENGLISH_PHRASES
            ):
                continue
            phrases.add(phrase)
    return phrases


def _without_placeholders(value: str) -> str:
    return re.sub(r"\{[^}]+\}", "", value)


def _unapproved_visible_english_fragments(text: str, locale: str) -> list[str]:
    fragments = list(COMMON_UNTRANSLATED_PROSE_FRAGMENTS)
    fragments.extend(LOCALE_FORBIDDEN_FRAGMENTS[locale])
    return [fragment for fragment in fragments if fragment in text]


def test_visible_english_allowlist_document_records_locale_contract():
    allowlist = ALLOWLIST_DOC_PATH.read_text(encoding="utf-8")
    rules = PLACEHOLDER_RULES_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-306`" in allowlist
    assert "without being treated as untranslated prose" in allowlist
    assert "full-catalog source-phrase reuse" in allowlist
    assert "Flag ordinary English commands or prose" in allowlist
    assert "docs/locale_visible_english_allowlists_2026-05-30.md" in rules

    for locale in LOCALES:
        assert f"| `{locale}` |" in allowlist

    required_allowed_terms = (
        "Browser Policy Manager",
        "policies.json",
        "JSON",
        "YAML",
        "DNS",
        "HTTPS",
        "VPN",
        "Mozilla account",
        "Add-ons",
        "Cookie",
    )
    for term in required_allowed_terms:
        assert term in allowlist

    required_forbidden_terms = (
        "DNS over HTTPS",
        "DNS-over-HTTPS",
        "Private browsing",
        "cuenta Mozillas",
        "compte Mozillas",
        "Task-first setup",
    )
    for term in required_forbidden_terms:
        assert term in allowlist


def test_locale_visible_english_allowlists_accept_documented_technical_examples():
    for locale, examples in LOCALE_ALLOWED_EXAMPLES.items():
        for example in examples:
            assert _unapproved_visible_english_fragments(example, locale) == []


def test_locale_visible_english_allowlists_reject_ordinary_untranslated_prose():
    for locale in LOCALES:
        sample = "Open profile. Save changes. Use this when setup needs a Task-first setup."

        unexpected = _unapproved_visible_english_fragments(sample, locale)

        assert "Open profile" in unexpected
        assert "Save changes" in unexpected
        assert "Use this when" in unexpected
        assert "Task-first setup" in unexpected


def test_audited_locale_surfaces_do_not_contain_forbidden_english_fragments():
    for locale, keys in AUDITED_KEYS.items():
        catalog = _load_catalog(locale)
        audited_text = "\n".join(catalog[key] for key in keys)

        assert _unapproved_visible_english_fragments(audited_text, locale) == []


def test_corporate_cis_l2_visible_locale_strings_do_not_reuse_english_source_phrases():
    english_catalog = _load_catalog("en")
    source_phrases = {
        key: _english_source_phrases(english_catalog[key])
        for key in CORPORATE_CIS_L2_VISIBLE_KEYS
    }

    failures = []
    for locale in LOCALES:
        catalog = _load_catalog(locale)
        for key, phrases in source_phrases.items():
            reused = sorted(phrase for phrase in phrases if phrase in catalog[key])
            if reused:
                failures.append(f"{locale}:{key}: {', '.join(reused[:5])}")

    assert failures == []


def test_non_english_catalogs_do_not_reuse_english_source_phrases():
    english_catalog = _load_catalog("en")
    source_phrases = {
        key: _all_english_source_phrases(value)
        for key, value in english_catalog.items()
    }

    failures = []
    for locale in LOCALES:
        catalog = _load_catalog(locale)
        for key, phrases in source_phrases.items():
            text = _without_placeholders(catalog[key])
            reused = sorted(
                phrase for phrase in phrases if phrase.lower() in text.lower()
            )
            if reused:
                failures.append(f"{locale}:{key}: {', '.join(reused[:5])}")

    assert failures == []


def test_simplified_chinese_catalog_keeps_latin_to_allowed_terms_only():
    catalog = _load_catalog("zh-CN")
    failures = []
    allowed_terms = {term.lower() for term in LATIN_TECHNICAL_TERMS}

    for key, value in catalog.items():
        text = _without_placeholders(value)
        if "://" in text or "@" in text:
            continue
        unexpected = sorted(
            {
                word
                for word in re.findall(
                    r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*",
                    text,
                )
                if word.lower() not in allowed_terms
                and not re.fullmatch(r"[A-Z]{2,}", word)
            }
        )
        if unexpected:
            failures.append(f"{key}: {', '.join(unexpected[:5])}")

    assert failures == []
