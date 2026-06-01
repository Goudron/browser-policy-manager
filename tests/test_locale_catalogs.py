import json
import re
from pathlib import Path

from app.main import app
from tests.support import make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"

PLACEHOLDER_RE = re.compile(r"\{[A-Za-z0-9_]+\}")


def _load_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def test_active_locale_catalogs_match_source_keys_and_placeholders():
    en_catalog = _load_catalog("en")

    for locale in ("de", "zh-CN", "fr", "es-ES"):
        catalog = _load_catalog(locale)

        assert list(catalog) == list(en_catalog)

        placeholder_mismatches = {
            key: (
                sorted(PLACEHOLDER_RE.findall(en_value)),
                sorted(PLACEHOLDER_RE.findall(catalog[key])),
            )
            for key, en_value in en_catalog.items()
            if sorted(PLACEHOLDER_RE.findall(en_value))
            != sorted(PLACEHOLDER_RE.findall(catalog[key]))
        }
        assert placeholder_mismatches == {}


def test_active_locale_catalogs_keep_footer_identity_invariant():
    expected_owner = {
        "ru": "Валерий Ледовской",
        "de": "Valery Ledovskoy",
        "zh-CN": "Valery Ledovskoy",
        "fr": "Valery Ledovskoy",
        "es-ES": "Valery Ledovskoy",
    }

    for locale, owner in expected_owner.items():
        catalog = _load_catalog(locale)

        assert catalog["profiles.footer_owner"] == owner
        assert catalog["profiles.footer_license_label"] == "Mozilla Public License 2.0"
        assert catalog["profiles.footer_note"] == "Browser Policy Manager"


def test_active_locale_catalogs_do_not_contain_machine_placeholder_text():
    forbidden_fragments = (
        "lokalisierter Text",
        "lokalisierte Texte",
        "Richtlinien.json",
        "Übergasein",
        "vonf",
        "Alleow",
        "Treffering",
        "texte localise",
        "texte localisee",
        "politiques.json",
        "modifieror",
        "ouvrired",
        "alprêt",
        "fermerr",
        "texto localizado",
        "texto localizadoo",
        "políticas.json",
        "editaror",
        "allisto",
        "abrired",
        "cerrarr",
        "项目 项目",
        "策略.json",
        "配置文件",
    )

    failures = []
    for locale in ("de", "zh-CN", "fr", "es-ES"):
        catalog = _load_catalog(locale)
        for key, value in catalog.items():
            for fragment in forbidden_fragments:
                if fragment in value:
                    failures.append(f"{locale}:{key}: {fragment}")

    assert failures == []


def test_de_locale_catalog_contains_german_source_terms():
    de_catalog = _load_catalog("de")

    expected_terms = {
        "profiles.title": "Browser-Profilmanager",
        "profiles.locale_option_de": "Deutsch",
        "profiles.editor_chrome_title": "Geführter Editor",
        "profiles.editor_chrome_settings_link": "Alle Einstellungen",
        "profiles.editor_chrome_validation": "Validierung",
        "profiles.shell_policy_translate_enabled": "Website-Übersetzungen",
        "profiles.wizard_privacy_section_state_private_browsing": "Privater Modus",
        "profiles.wizard_privacy_vpn_title": "Integriertes VPN",
        "profiles.wizard_export_guided_privacy_vpn_hidden": "Integriertes VPN",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in de_catalog[key]

    assert de_catalog["profiles.wizard_search_engine_url_placeholder"] == (
        "https://www.example.org/search?q={searchTerms}"
    )
    assert de_catalog["profiles.wizard_proxy_passthrough_placeholder"] == "<local>"


def test_de_locale_catalog_applies_mozilla_terminology_audit_terms():
    de_catalog = _load_catalog("de")

    expected_terms = {
        "profiles.shell_policy_disable_firefox_accounts": "Mozilla-Konto",
        "profiles.wizard_settings_sync_account": "Mozilla-Konto",
        "profiles.wizard_preferences_group_sync_account": "Mozilla-Konto",
        "profiles.policy_disable_accounts": "Mozilla-Konten",
        "profiles.shell_policy_private_browsing_mode_availability": "Privaten Modus",
        "profiles.schema_field_private_browsing": "Privater Modus",
        "profiles.wizard_doh_state_empty": "DNS über HTTPS",
        "profiles.wizard_doh_state_invalid": "DNS über HTTPS",
        "profiles.wizard_review_search_suggestions_on": "Suchvorschläge aktiviert",
        "profiles.wizard_review_search_suggestions_off": "Suchvorschläge deaktiviert",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in de_catalog[key]

    audited_values = "\n".join(
        de_catalog[key]
        for key in (
            "profiles.shell_policy_private_browsing_mode_availability",
            "profiles.schema_field_private_browsing",
            "profiles.wizard_shared_device_workflow_private_ready",
            "profiles.wizard_hardening_impact_private_browsing",
            "profiles.wizard_doh_state_empty",
            "profiles.wizard_doh_state_invalid",
            "profiles.policy_disable_accounts",
            "profiles.policy_disable_accounts_copy",
        )
    )
    assert "Private browsing" not in audited_values
    assert "DNS-over-HTTPS" not in audited_values
    assert "Firefox Account" not in audited_values


def test_de_locale_catalog_loads_from_runtime_endpoint():
    client = make_test_client(app)

    response = client.get("/i18n/de.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["profiles.locale_option_de"] == "Deutsch"


def test_zh_cn_locale_catalog_contains_simplified_chinese_source_terms():
    zh_catalog = _load_catalog("zh-CN")

    expected_terms = {
        "profiles.title": "浏览器配置档案管理器",
        "profiles.locale_option_zh_cn": "简体中文",
        "profiles.editor_chrome_title": "引导式编辑器",
        "profiles.editor_chrome_settings_link": "所有设置",
        "profiles.editor_chrome_validation": "验证",
        "profiles.shell_policy_translate_enabled": "网站翻译",
        "profiles.wizard_privacy_section_state_private_browsing": "隐私浏览",
        "profiles.wizard_privacy_vpn_title": "内置 VPN",
        "profiles.wizard_export_guided_privacy_vpn_hidden": "内置 VPN",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in zh_catalog[key]

    assert zh_catalog["profiles.wizard_search_engine_url_placeholder"] == (
        "https://www.example.org/search?q={searchTerms}"
    )
    assert zh_catalog["profiles.wizard_proxy_passthrough_placeholder"] == "<local>"


def test_zh_cn_locale_catalog_applies_mozilla_terminology_audit_terms():
    zh_catalog = _load_catalog("zh-CN")

    expected_terms = {
        "profiles.shell_policy_disable_firefox_accounts": "Mozilla 账号",
        "profiles.wizard_sync_title": "Mozilla 账号",
        "profiles.wizard_sync_section_state_accounts_disabled": "Mozilla 账号",
        "profiles.wizard_shell_subsection_dns_over_https": "基于 HTTPS 的 DNS",
        "profiles.shell_policy_dnsover_https": "基于 HTTPS 的 DNS",
        "profiles.wizard_doh_state_empty": "基于 HTTPS 的 DNS",
        "profiles.wizard_doh_state_invalid": "基于 HTTPS 的 DNS",
        "profiles.wizard_review_search_suggestions_on": "搜索建议已启用",
        "profiles.wizard_review_search_suggestions_off": "搜索建议已禁用",
        "profiles.wizard_privacy_vpn_section_state_available": "内置 VPN",
        "profiles.wizard_export_guided_privacy_vpn_available": "内置 VPN",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in zh_catalog[key]

    audited_values = "\n".join(
        zh_catalog[key]
        for key in (
            "profiles.shell_policy_disable_firefox_accounts",
            "profiles.wizard_sync_title",
            "profiles.wizard_sync_section_state_accounts_disabled",
            "profiles.wizard_shell_subsection_dns_over_https",
            "profiles.shell_policy_dnsover_https",
            "profiles.wizard_doh_state_empty",
            "profiles.wizard_doh_state_invalid",
            "profiles.wizard_privacy_vpn_section_state_available",
            "profiles.wizard_export_guided_privacy_vpn_available",
        )
    )
    assert "Mozilla 账户" not in audited_values
    assert "DNS over HTTPS" not in audited_values
    assert "DNS-over-HTTPS" not in audited_values
    assert "Built-in VPN" not in audited_values


def test_zh_cn_locale_catalog_loads_from_runtime_endpoint():
    client = make_test_client(app)

    response = client.get("/i18n/zh-CN.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["profiles.locale_option_zh_cn"] == "简体中文"


def test_fr_locale_catalog_contains_french_source_terms():
    fr_catalog = _load_catalog("fr")

    expected_terms = {
        "profiles.title": "Gestionnaire de politiques du navigateur",
        "profiles.locale_option_fr": "Français",
        "profiles.editor_chrome_title": "Éditeur guidé",
        "profiles.editor_chrome_settings_link": "Tous les paramètres",
        "profiles.editor_chrome_validation": "Validation",
        "profiles.shell_policy_translate_enabled": "Traductions des sites web",
        "profiles.wizard_privacy_section_state_private_browsing": "Navigation privée",
        "profiles.wizard_privacy_vpn_title": "VPN intégré",
        "profiles.wizard_export_guided_privacy_vpn_hidden": "VPN intégré",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in fr_catalog[key]

    assert fr_catalog["profiles.wizard_search_engine_url_placeholder"] == (
        "https://www.example.org/search?q={searchTerms}"
    )
    assert fr_catalog["profiles.wizard_proxy_passthrough_placeholder"] == "<local>"


def test_fr_locale_catalog_applies_mozilla_terminology_audit_terms():
    fr_catalog = _load_catalog("fr")

    expected_terms = {
        "profiles.shell_policy_disable_firefox_accounts": "compte Mozilla",
        "profiles.wizard_sync_title": "Compte Mozilla",
        "profiles.wizard_sync_section_state_accounts_disabled": "compte Mozilla",
        "profiles.wizard_shell_subsection_dns_over_https": "DNS via HTTPS",
        "profiles.shell_policy_dnsover_https": "DNS via HTTPS",
        "profiles.wizard_doh_state_empty": "DNS via HTTPS",
        "profiles.wizard_doh_state_invalid": "DNS via HTTPS",
        "profiles.shell_policy_private_browsing_mode_availability": "mode de navigation privée",
        "profiles.schema_field_private_browsing": "Navigation privée",
        "profiles.wizard_review_search_suggestions_on": "Suggestions de recherche activées",
        "profiles.wizard_review_search_suggestions_off": "Suggestions de recherche désactivées",
        "profiles.wizard_privacy_vpn_section_state_available": "VPN intégré",
        "profiles.wizard_export_guided_privacy_vpn_available": "VPN intégré",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in fr_catalog[key]

    audited_values = "\n".join(
        fr_catalog[key]
        for key in (
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
        )
    )
    assert "compte Mozillas" not in audited_values
    assert "DNS over HTTPS" not in audited_values
    assert "DNS-over-HTTPS" not in audited_values
    assert "Private browsing" not in audited_values


def test_fr_locale_catalog_loads_from_runtime_endpoint():
    client = make_test_client(app)

    response = client.get("/i18n/fr.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["profiles.locale_option_fr"] == "Français"


def test_es_es_locale_catalog_contains_spanish_source_terms():
    es_catalog = _load_catalog("es-ES")

    expected_terms = {
        "profiles.title": "Gestor de políticas del navegador",
        "profiles.locale_option_es_es": "Español",
        "profiles.editor_chrome_title": "Editor guiado",
        "profiles.editor_chrome_settings_link": "Todos los ajustes",
        "profiles.editor_chrome_validation": "Validación",
        "profiles.shell_policy_translate_enabled": "Traducciones de sitios web",
        "profiles.wizard_privacy_section_state_private_browsing": "Navegación privada",
        "profiles.wizard_privacy_vpn_title": "VPN integrada",
        "profiles.wizard_export_guided_privacy_vpn_hidden": "VPN integrada",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in es_catalog[key]

    assert es_catalog["profiles.wizard_search_engine_url_placeholder"] == (
        "https://www.example.org/search?q={searchTerms}"
    )
    assert es_catalog["profiles.wizard_proxy_passthrough_placeholder"] == "<local>"


def test_es_es_locale_catalog_applies_mozilla_terminology_audit_terms():
    es_catalog = _load_catalog("es-ES")

    expected_terms = {
        "profiles.shell_policy_disable_firefox_accounts": "Mozilla account",
        "profiles.wizard_sync_title": "Mozilla account",
        "profiles.wizard_sync_section_state_accounts_disabled": "Mozilla account",
        "profiles.wizard_shell_subsection_dns_over_https": "DNS sobre HTTPS",
        "profiles.shell_policy_dnsover_https": "DNS sobre HTTPS",
        "profiles.wizard_doh_state_empty": "DNS sobre HTTPS",
        "profiles.wizard_doh_state_invalid": "DNS sobre HTTPS",
        "profiles.shell_policy_private_browsing_mode_availability": "modo de navegación privada",
        "profiles.schema_field_private_browsing": "Navegación privada",
        "profiles.wizard_review_search_suggestions_on": "Sugerencias de búsqueda activadas",
        "profiles.wizard_review_search_suggestions_off": "Sugerencias de búsqueda desactivadas",
        "profiles.wizard_privacy_vpn_section_state_available": "VPN integrada",
        "profiles.wizard_export_guided_privacy_vpn_available": "VPN integrada",
    }
    for key, expected_fragment in expected_terms.items():
        assert expected_fragment in es_catalog[key]

    audited_values = "\n".join(
        es_catalog[key]
        for key in (
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
        )
    )
    assert "cuenta Mozillas" not in audited_values
    assert "DNS over HTTPS" not in audited_values
    assert "DNS-over-HTTPS" not in audited_values
    assert "Private browsing" not in audited_values


def test_es_es_locale_catalog_loads_from_runtime_endpoint():
    client = make_test_client(app)

    response = client.get("/i18n/es-ES.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["profiles.locale_option_es_es"] == "Español"
