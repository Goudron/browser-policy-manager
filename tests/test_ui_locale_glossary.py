from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = REPO_ROOT / "docs" / "ui_locale_glossary_global_2026-05-29.md"
MOZILLA_WORKFLOW_PATH = (
    REPO_ROOT / "docs" / "mozilla_terminology_verification_workflow_2026-05-29.md"
)
DE_MOZILLA_AUDIT_PATH = (
    REPO_ROOT / "docs" / "de_mozilla_terminology_audit_2026-05-29.md"
)
ZH_CN_MOZILLA_AUDIT_PATH = (
    REPO_ROOT / "docs" / "zh_cn_mozilla_terminology_audit_2026-05-29.md"
)
FR_MOZILLA_AUDIT_PATH = (
    REPO_ROOT / "docs" / "fr_mozilla_terminology_audit_2026-05-29.md"
)
ES_ES_MOZILLA_AUDIT_PATH = (
    REPO_ROOT / "docs" / "es_es_mozilla_terminology_audit_2026-05-30.md"
)
PLACEHOLDER_RULES_PATH = (
    REPO_ROOT / "docs" / "locale_placeholder_identifier_rules_2026-05-29.md"
)
LOCALE_UPDATE_RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "locale_update_runbook_2026-06-01.md"
)
LOCALE_OWNERSHIP_PATH = REPO_ROOT / "docs" / "locale_ownership_2026-06-01.md"
FIREFOX_SCHEMA_UPDATE_RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "firefox-schema-update-runbook.md"
)
HISTORICAL_GLOSSARY_PATH = (
    REPO_ROOT / "docs" / "ui_locale_glossary_en_ru_2026-05-15.md"
)


def test_global_ui_locale_glossary_records_six_locale_terms():
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-103`" in glossary
    assert "QA consolidation: `GLOC-305`" in glossary
    assert "Release-readiness glossary update: `GLOC-702`" in glossary
    assert "Document status: primary maintainer glossary" in glossary
    assert "Source locale: `en`" in glossary
    assert "Target locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in glossary
    assert "German, Simplified" in glossary
    assert "Chinese, French, and Spanish record the" in glossary
    assert (
        "| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |"
        in glossary
    )

    required_terms = (
        "Browser Policy Manager",
        "Менеджер профилей браузера",
        "Guided editor",
        "Пошаговый редактор",
        "All settings",
        "Все настройки",
        "JSON editor",
        "JSON-редактор",
        "Profile library",
        "Библиотека профилей",
        "Profile name",
        "Имя профиля",
        "Mozilla account",
        "аккаунт Mozilla",
        "Mozilla-Konto",
        "Mozilla 账号",
        "compte Mozilla",
        "Mozilla account",
        "Firefox Home",
        "Домашняя страница Firefox",
        "Firefox-Startseite",
        "Firefox 主页",
        "page d’accueil de Firefox",
        "página de inicio de Firefox",
        "Private Browsing",
        "Privater Modus",
        "隐私浏览",
        "navigation privée",
        "navegación privada",
        "Cookies",
        "Куки",
        "Cookie",
        "cookies",
        "Add-ons",
        "Дополнения",
        "附加组件",
        "modules complémentaires",
        "complementos",
        "Address bar",
        "Адресная строка",
        "Adressleiste",
        "地址栏",
        "barre d’adresse",
        "barra de direcciones",
        "Site permissions",
        "Разрешения сайтов",
        "Website-Berechtigungen",
        "网站权限",
        "permissions des sites",
        "permisos del sitio",
        "Managed preferences",
        "Управляемые параметры",
        "Verwaltete Einstellungen",
        "托管首选项",
        "préférences gérées",
        "preferencias gestionadas",
        "Outside Guided editor",
        "Вне Пошагового редактора",
        "Außerhalb des geführten Editors",
        "引导式编辑器之外",
        "Hors éditeur guidé",
        "Fuera del editor guiado",
        "CIS benchmark overlay",
        "Наложение бенчмарка CIS",
        "Validation failed",
        "Проверка не прошла",
        "{count}",
        "DisablePrivateBrowsing",
        "browser.startup.homepage",
        "policies.json",
        "ИИ и умные функции",
    )
    for term in required_terms:
        assert term in glossary

    assert "Do not replace `TBD` with unreviewed machine" in glossary
    assert "Firefox/Mozilla terms must be checked against Pontoon and SUMO" in glossary
    assert "docs/mozilla_terminology_verification_workflow_2026-05-29.md" in glossary
    assert "docs/locale_placeholder_identifier_rules_2026-05-29.md" in glossary


def test_global_ui_locale_glossary_consolidates_mozilla_qa_findings():
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    required_markers = (
        "`GLOC-305` consolidates the Mozilla terminology QA findings",
        "| `de` | `GLOC-301` | `docs/de_mozilla_terminology_audit_2026-05-29.md` |",
        "| `zh-CN` | `GLOC-302` | `docs/zh_cn_mozilla_terminology_audit_2026-05-29.md` |",
        "| `fr` | `GLOC-303` | `docs/fr_mozilla_terminology_audit_2026-05-29.md` |",
        "| `es-ES` | `GLOC-304` | `docs/es_es_mozilla_terminology_audit_2026-05-30.md` |",
        "Spanish keeps `Mozilla account`",
        "Russian `Private Browsing` remains `Приватные окна`",
        "`Visual search` and `AI & smart features` have weaker localized SUMO coverage",
        "`TBD` remains valid only as an explicit needs-review marker",
        "`GLOC-702` makes this file the single current glossary document",
    )
    for marker in required_markers:
        assert marker in glossary

    mozilla_section = glossary.split("## Firefox And Mozilla Terms", 1)[1].split(
        "## Policy And Schema Terms", 1
    )[0]
    term_rows = [
        row
        for row in mozilla_section.splitlines()
        if row.startswith("| mozilla.")
    ]

    assert term_rows
    assert all("TBD" not in row for row in term_rows)

    required_rows = (
        "| mozilla.account | Mozilla account | аккаунт Mozilla | Mozilla-Konto | Mozilla 账号 | compte Mozilla | Mozilla account |",
        "| mozilla.dns_over_https | DNS over HTTPS | DNS через HTTPS | DNS über HTTPS | 基于 HTTPS 的 DNS | DNS via HTTPS | DNS sobre HTTPS |",
        "| mozilla.built_in_vpn | Built-in VPN | Встроенный VPN | Integriertes VPN | 内置 VPN | VPN intégré | VPN integrada |",
    )
    for row in required_rows:
        assert row in glossary


def test_historical_en_ru_glossary_points_to_global_glossary():
    glossary = HISTORICAL_GLOSSARY_PATH.read_text(encoding="utf-8")

    assert "Scope: historical EN/RU product UI terminology only." in glossary
    assert "docs/ui_locale_glossary_global_2026-05-29.md" in glossary
    assert "historical EN/RU reference" in glossary
    assert "single current maintainer reference" in glossary
    assert "Do not add new terminology decisions here." in glossary


def test_mozilla_terminology_workflow_records_repeatable_process():
    workflow = MOZILLA_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-104`" in workflow
    assert "Applies to locales: `de`, `zh-CN`, `fr`, `es-ES`, and future locale maintenance for `ru`" in workflow
    assert "Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`" in workflow
    assert "Mozilla Pontoon Firefox project and target-locale team pages" in workflow
    assert "SUMO localized Firefox articles" in workflow
    assert "Target locale Firefox Enterprise project" in workflow
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in workflow

    required_terms = (
        "mozilla.account",
        "mozilla.firefox_home",
        "mozilla.private_browsing",
        "mozilla.website_translations",
        "mozilla.dns_over_https",
        "mozilla.site_permissions",
        "mozilla.built_in_vpn",
        "mozilla.ip_protection",
        "policy.managed_preferences",
    )
    for term in required_terms:
        assert term in workflow

    required_sources = (
        "https://pontoon.mozilla.org/projects/firefox/",
        "https://pontoon.mozilla.org/de/",
        "https://pontoon.mozilla.org/zh-CN/firefox/",
        "https://pontoon.mozilla.org/fr/",
        "https://pontoon.mozilla.org/es-ES/firefox/",
        "https://support.mozilla.org/en-US/kb/firefox-options-preferences-and-settings",
        "https://support.mozilla.org/en-US/kb/website-translation",
    )
    for source in required_sources:
        assert source in workflow


def test_de_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = DE_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-301`" in audit
    assert "Catalog: `app/i18n/de.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = (
        "mozilla.account",
        "Mozilla-Konto",
        "mozilla.firefox_home",
        "Firefox-Startseite",
        "mozilla.private_browsing",
        "Privater Modus",
        "mozilla.dns_over_https",
        "DNS über HTTPS",
        "mozilla.site_permissions",
        "Website-Berechtigungen",
        "mozilla.addons",
        "Add-ons",
        "mozilla.extensions",
        "Erweiterungen",
        "mozilla.website_translations",
        "Website-Übersetzungen",
        "mozilla.built_in_vpn",
        "Integriertes VPN",
        "policy.managed_preferences",
        "Verwaltete Einstellungen",
    )
    for term in required_terms:
        assert term in audit

    required_sources = (
        "https://pontoon.mozilla.org/de/",
        "https://support.mozilla.org/de/kb/firefox-konto-auf-supportmozillaorg",
        "https://support.mozilla.org/de/kb/startseite-festlegen",
        "https://support.mozilla.org/de/kb/privater-modus",
        "https://support.mozilla.org/de/kb/dns-over-https",
        "https://support.mozilla.org/de/kb/vollstandige-webseiten-in-firefox-ubersetzen",
    )
    for source in required_sources:
        assert source in audit


def test_zh_cn_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = ZH_CN_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-302`" in audit
    assert "Catalog: `app/i18n/zh-CN.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = (
        "mozilla.account",
        "Mozilla 账号",
        "mozilla.firefox_home",
        "Firefox 主页",
        "mozilla.private_browsing",
        "隐私浏览",
        "mozilla.dns_over_https",
        "基于 HTTPS 的 DNS",
        "mozilla.site_permissions",
        "网站权限",
        "mozilla.addons",
        "附加组件",
        "mozilla.extensions",
        "扩展",
        "mozilla.website_translations",
        "网站翻译",
        "mozilla.built_in_vpn",
        "内置 VPN",
        "policy.managed_preferences",
        "托管首选项",
    )
    for term in required_terms:
        assert term in audit

    required_sources = (
        "https://pontoon.mozilla.org/zh-CN/firefox/",
        "https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security",
        "https://support.mozilla.org/zh-CN/kb/firefox-dns-over-https",
        "https://support.mozilla.org/zh-CN/kb/website-translation",
        "https://support.mozilla.org/zh-CN/kb/use-ip-concealment-in-firefox",
    )
    for source in required_sources:
        assert source in audit


def test_fr_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = FR_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-303`" in audit
    assert "Catalog: `app/i18n/fr.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = (
        "mozilla.account",
        "compte Mozilla",
        "mozilla.firefox_home",
        "page d’accueil de Firefox",
        "mozilla.private_browsing",
        "navigation privée",
        "mozilla.dns_over_https",
        "DNS via HTTPS",
        "mozilla.site_permissions",
        "permissions des sites",
        "mozilla.addons",
        "modules complémentaires",
        "mozilla.extensions",
        "extensions",
        "mozilla.website_translations",
        "traductions des sites web",
        "mozilla.built_in_vpn",
        "VPN intégré",
        "policy.managed_preferences",
        "préférences gérées",
    )
    for term in required_terms:
        assert term in audit

    required_sources = (
        "https://pontoon.mozilla.org/fr/",
        "https://support.mozilla.org/fr/products/mozilla-account/accounts",
        "https://support.mozilla.org/fr/kb/comment-definir-page-accueil",
        "https://support.mozilla.org/fr/kb/navigation-privee-naviguer-avec-firefox-sans-enregistrer-historique",
        "https://support.mozilla.org/fr/kb/dns-over-https",
        "https://support.mozilla.org/fr/kb/traduction-sites-web",
        "https://support.mozilla.org/fr/kb/vpn-integre",
    )
    for source in required_sources:
        assert source in audit


def test_es_es_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = ES_ES_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-304`" in audit
    assert "Catalog: `app/i18n/es-ES.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = (
        "mozilla.account",
        "Mozilla account",
        "mozilla.firefox_home",
        "página de inicio de Firefox",
        "mozilla.private_browsing",
        "navegación privada",
        "mozilla.dns_over_https",
        "DNS sobre HTTPS",
        "mozilla.site_permissions",
        "permisos del sitio",
        "mozilla.addons",
        "complementos",
        "mozilla.extensions",
        "extensiones",
        "mozilla.website_translations",
        "traducciones de sitios web",
        "mozilla.built_in_vpn",
        "VPN integrada",
        "policy.managed_preferences",
        "preferencias gestionadas",
    )
    for term in required_terms:
        assert term in audit

    required_sources = (
        "https://pontoon.mozilla.org/es-ES/firefox/",
        "https://support.mozilla.org/es/products/firefox/accounts",
        "https://support.mozilla.org/es/kb/como-configurar-la-pagina-de-inicio",
        "https://support.mozilla.org/es/kb/navegacion-privada-Firefox-no-guardar-historial-navegacion",
        "https://support.mozilla.org/en-US/kb/firefox-dns-over-https?lang=es",
        "https://support.mozilla.org/es/kb/traduccion-pagina-web",
        "https://support.mozilla.org/es/kb/usar-la-vpn-de-firefox-en-firefox",
    )
    for source in required_sources:
        assert source in audit


def test_placeholder_identifier_rules_record_locale_review_contract():
    rules = PLACEHOLDER_RULES_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-105`" in rules
    assert "Applies to locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in rules
    assert "Make locale review deterministic" in rules
    assert "Preserve the complete token exactly, including braces and case" in rules
    assert "Every target locale key must contain the same placeholder set" in rules
    assert "The complete placeholder inventory is in `placeholder_map`" in rules
    assert "The complete technical-token inventory is in `technical_token_map`" in rules
    assert "docs/locale_visible_english_allowlists_2026-05-30.md" in rules
    assert "English prose is not accepted just because technical terms are allowed" in rules

    required_tokens = (
        "{count}",
        "{searchTerms}",
        "DisablePrivateBrowsing",
        "IPProtectionAvailable",
        "browser.startup.homepage",
        "policies.json",
        "about:config",
        "uBlock0@raymondhill.net",
        "q={searchTerms}&source=firefox",
        "<local>",
        "placeholder-missing",
        "identifier-translated",
        "untranslated-prose",
    )
    for token in required_tokens:
        assert token in rules


def test_locale_update_runbook_records_repeatable_release_process():
    runbook = LOCALE_UPDATE_RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-703`" in runbook
    assert "Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in runbook
    assert "Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`" in runbook
    assert "Mozilla terminology workflow: `docs/mozilla_terminology_verification_workflow_2026-05-29.md`" in runbook
    assert "Placeholder and identifier rules: `docs/locale_placeholder_identifier_rules_2026-05-29.md`" in runbook
    assert "Visible English allowlists: `docs/locale_visible_english_allowlists_2026-05-30.md`" in runbook
    assert "Locale ownership: `docs/locale_ownership_2026-06-01.md`" in runbook

    required_catalogs = (
        "app/i18n/en.json",
        "app/i18n/ru.json",
        "app/i18n/de.json",
        "app/i18n/zh-CN.json",
        "app/i18n/fr.json",
        "app/i18n/es-ES.json",
    )
    for catalog in required_catalogs:
        assert catalog in runbook

    required_commands = (
        ".venv/bin/pytest -q tests/test_locale_catalogs.py tests/test_locale_visible_english_allowlists.py tests/test_ui_runtime_i18n_contract.py",
        ".venv/bin/pytest -q tests/test_ui_locale_glossary.py",
        ".venv/bin/pytest -q tests/test_all_settings_search_filter_i18n.py tests/test_runtime_count_i18n.py",
        ".venv/bin/pytest -q tests/test_chromium_locale_smoke_matrix_contract.py tests/test_locale_viewport_overflow_contract.py",
        ".venv/bin/pytest -q tests/test_locale_switching_regression_contract.py tests/test_localized_import_edit_export_workflow_contract.py",
        ".venv/bin/mypy app",
        ".venv/bin/ruff check .",
        ".venv/bin/pytest -q --cov=app --cov-report=term-missing",
    )
    for command in required_commands:
        assert command in runbook

    required_review_points = (
        "Mozilla terms match the global glossary or have fresh Pontoon/SUMO evidence.",
        "Non-English catalogs do not contain accidental English prose.",
        "The expected coverage result for the app surface is `TOTAL 100%`.",
        "any known `TBD` or `needs-review` terminology left intentionally unresolved.",
        "single-maintainer, manual-review model",
        "External or community translation contributions are not a separate maintained workflow yet",
    )
    for point in required_review_points:
        assert point in runbook


def test_firefox_schema_update_runbook_includes_locale_update_gate():
    runbook = FIREFOX_SCHEMA_UPDATE_RUNBOOK_PATH.read_text(encoding="utf-8")

    required_catalogs = (
        "app/i18n/en.json",
        "app/i18n/ru.json",
        "app/i18n/de.json",
        "app/i18n/zh-CN.json",
        "app/i18n/fr.json",
        "app/i18n/es-ES.json",
    )
    for catalog in required_catalogs:
        assert catalog in runbook

    required_markers = (
        "Update every active locale catalog when Release / ESR labels",
        "docs/locale_update_runbook_2026-06-01.md",
        "Pontoon/SUMO evidence",
        "tests/test_locale_catalogs.py",
        "tests/test_ui_runtime_i18n_contract.py",
        "tests/test_locale_visible_english_allowlists.py",
        "tests/test_ui_locale_glossary.py",
        "current Release / ESR labels",
        "without English fallback islands",
        "Adding schema-related locale keys only to `en.json`",
    )
    for marker in required_markers:
        assert marker in runbook


def test_locale_ownership_records_single_maintainer_model():
    ownership = LOCALE_OWNERSHIP_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-705`" in ownership
    assert "Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in ownership
    assert "BPM is currently maintained by a single project maintainer, Valery Ledovskoy" in ownership
    assert "There is no separate translator team, localization vendor, or open community translation process" in ownership
    assert "External or community translation contributions are not a separate maintained workflow yet" in ownership
    assert "Locale drift is handled during ordinary feature work." in ownership
    assert "Revisit this ownership document if BPM adds regular external contributors" in ownership

    required_rows = (
        "| English source copy | Project maintainer |",
        "| Russian localization | Project maintainer |",
        "| German localization | Project maintainer |",
        "| Simplified Chinese localization | Project maintainer |",
        "| French localization | Project maintainer |",
        "| Spanish (Spain) localization | Project maintainer |",
        "| Locale QA and release readiness | Project maintainer |",
    )
    for row in required_rows:
        assert row in ownership
