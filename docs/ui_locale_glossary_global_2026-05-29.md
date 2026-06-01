# Browser Policy Manager Global UI Glossary

Date: `2026-05-29`

Backlog item: `GLOC-103`

QA consolidation: `GLOC-305`

Release-readiness glossary update: `GLOC-702`

Document status: primary maintainer glossary for current six-locale UI terminology

Source locale: `en`

Target locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`

Source inventory: `docs/source_string_inventory_en_2026-05-21.json`

Normalization notes: `docs/source_copy_normalization_en_2026-05-21.md`

Mozilla terminology workflow: `docs/mozilla_terminology_verification_workflow_2026-05-29.md`

Placeholder and identifier rules: `docs/locale_placeholder_identifier_rules_2026-05-29.md`

Mozilla terminology audits:

- `docs/de_mozilla_terminology_audit_2026-05-29.md`
- `docs/zh_cn_mozilla_terminology_audit_2026-05-29.md`
- `docs/fr_mozilla_terminology_audit_2026-05-29.md`
- `docs/es_es_mozilla_terminology_audit_2026-05-30.md`

## Scope

This glossary is the primary maintainer terminology reference for BPM UI localization. English is
the source product language. Russian, German, Simplified Chinese, French, and Spanish record the
current six-locale terminology decisions that should guide UI strings, release documentation,
locale review, and future source-copy changes.

This file replaces the historical EN/RU-only glossary at
`docs/ui_locale_glossary_en_ru_2026-05-15.md` for active maintenance. The historical file remains
only as an archive of pre-expansion Russian terminology.

## QA Consolidation

`GLOC-305` consolidates the Mozilla terminology QA findings from `GLOC-301` through `GLOC-304`.
The Firefox and Mozilla term rows below are now the maintained multilingual reference for future UI
copy changes. Locale-specific audits remain the evidence log for why each target term was accepted
or changed.

`GLOC-702` makes this file the single current glossary document for the six-locale release. When a
new UI string needs terminology guidance, update this glossary first or record why an existing row is
not applicable. Do not add active terminology decisions to the historical EN/RU glossary.

| Locale | Audit task | Evidence log | Glossary result |
|---|---|---|---|
| `de` | `GLOC-301` | `docs/de_mozilla_terminology_audit_2026-05-29.md` | Firefox/Mozilla rows filled with German Pontoon/SUMO decisions. |
| `zh-CN` | `GLOC-302` | `docs/zh_cn_mozilla_terminology_audit_2026-05-29.md` | Firefox/Mozilla rows filled with Simplified Chinese Pontoon/SUMO decisions. |
| `fr` | `GLOC-303` | `docs/fr_mozilla_terminology_audit_2026-05-29.md` | Firefox/Mozilla rows filled with French Pontoon/SUMO decisions. |
| `es-ES` | `GLOC-304` | `docs/es_es_mozilla_terminology_audit_2026-05-30.md` | Firefox/Mozilla rows filled with Spanish Pontoon/SUMO decisions. |

Accepted QA findings:

- Spanish keeps `Mozilla account` where current Spanish SUMO product/account copy keeps the English
  product term.
- Russian `Private Browsing` remains `Приватные окна` in the current runtime catalog until a future
  Russian maintenance pass revisits that wording.
- `Visual search` and `AI & smart features` have weaker localized SUMO coverage in some target
  locales, so the glossary records the accepted natural UI terms and the audit logs note the
  evidence limitation.
- `TBD` remains valid only as an explicit needs-review marker outside the audited Firefox/Mozilla
  rows and selected policy rows. It should not be treated as approved release terminology.

## Column Rules

- Preserve `{placeholders}` exactly, including braces and spelling.
- Preserve product names, file names, policy keys, preference keys, API paths, URLs, extension IDs,
  JSON/YAML literals, `ESR`, `Release`, `CIS`, and `policies.json` unless a locale-specific note says
  otherwise.
  Use `docs/locale_placeholder_identifier_rules_2026-05-29.md` for the full preservation rules and
  review checklist.
- `TBD` means untranslated and awaiting human review. Do not replace `TBD` with unreviewed machine
  translation.
- Firefox/Mozilla terms must be checked against Pontoon and SUMO during the relevant locale QA tasks.
  Use `docs/mozilla_terminology_verification_workflow_2026-05-29.md` for the repeatable process and
  evidence log format.

## Product Modes

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| product.name | Browser Policy Manager | Менеджер профилей браузера | TBD | TBD | TBD | TBD | Product name can remain English in code and technical references. |
| product.profile_library | Profile library | Библиотека профилей | TBD | TBD | TBD | TBD | Saved profile collection and list surface. |
| product.library_short | Library | Библиотека | TBD | TBD | TBD | TBD | Short navigation label. |
| product.guided_editor | Guided editor | Пошаговый редактор | TBD | TBD | TBD | TBD | Task-first editor for common administrator workflows. |
| product.all_settings | All settings | Все настройки | TBD | TBD | TBD | TBD | Full visual settings manager; not an "advanced settings" synonym. |
| product.json_editor | JSON editor | JSON-редактор | TBD | TBD | TBD | TBD | Raw `policies.json` editor. Keep `JSON` untranslated. |
| product.command_deck | Command deck | Командная панель | TBD | TBD | TBD | TBD | Shared action surface for save, validate, restore, and profile actions. |
| product.current_mode | Current mode | Текущий режим | TBD | TBD | TBD | TBD | Editor chrome and mode switch context. |

## Profile Lifecycle

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| lifecycle.profile | Profile | Профиль | TBD | TBD | TBD | TBD | Generic managed browser profile. |
| lifecycle.profile_name | Profile name | Имя профиля | TBD | TBD | TBD | TBD | Prefer over generic `Name` in profile-specific fields. |
| lifecycle.owner | Owner | Владелец | TBD | TBD | TBD | TBD | Profile metadata. |
| lifecycle.description | Description | Описание | TBD | TBD | TBD | TBD | Profile metadata. |
| lifecycle.draft | Draft | Черновик | TBD | TBD | TBD | TBD | Unsaved or not-yet-finalized profile state. |
| lifecycle.active | Active | Активен | TBD | TBD | TBD | TBD | Saved active profile state. |
| lifecycle.deleted | Deleted | Удалён | TBD | TBD | TBD | TBD | Current badge/state term for archived/deleted profiles. |
| lifecycle.archive | Archive | Архивировать | TBD | TBD | TBD | TBD | Soft-delete action; the profile can be restored later. |
| lifecycle.restore | Restore | Восстановить | TBD | TBD | TBD | TBD | Re-enable an archived/deleted profile. |
| lifecycle.delete_permanently | Delete permanently | Удалить навсегда | TBD | TBD | TBD | TBD | Hard-delete action. Use only where destructive behavior is explicit. |
| lifecycle.clone_adjust | Clone and adjust | Клонировать и доработать | TBD | TBD | TBD | TBD | Creates a draft based on another profile. |
| lifecycle.compare | Compare | Сравнить | TBD | TBD | TBD | TBD | Compare profiles or current setup with a saved profile. |
| lifecycle.save_conflict | Save conflict | Конфликт сохранения | TBD | TBD | TBD | TBD | Multi-tab or revision conflict. |

## Editing And Workflow

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| workflow.save | Save | Сохранить | TBD | TBD | TBD | TBD | Primary persistence action. |
| workflow.validate | Validate | Проверить | TBD | TBD | TBD | TBD | Button/action verb. |
| workflow.validation | Validation | Проверка | TBD | TBD | TBD | TBD | Noun for validation state/results. |
| workflow.validation_passed | Validation passed | Проверка прошла успешно | TBD | TBD | TBD | TBD | Success result. |
| workflow.validation_failed | Validation failed | Проверка не прошла | TBD | TBD | TBD | TBD | Failure result. |
| workflow.unsaved_changes | Unsaved changes | Несохранённые изменения | TBD | TBD | TBD | TBD | Dirty editor state. |
| workflow.all_changes_saved | All changes saved | Все изменения сохранены | TBD | TBD | TBD | TBD | Clean editor state. |
| workflow.reload_latest | Reload latest | Загрузить последнюю версию | TBD | TBD | TBD | TBD | Conflict recovery action. |
| workflow.overwrite_anyway | Overwrite anyway | Всё равно перезаписать | TBD | TBD | TBD | TBD | Conflict override action. |
| workflow.import_policies | Import policies.json | Импортировать policies.json | TBD | TBD | TBD | TBD | Keep `policies.json` unchanged. |
| workflow.download_policies | Download Firefox policies.json | Скачать Firefox policies.json | TBD | TBD | TBD | TBD | File download action. |
| workflow.export | Export | Выгрузка | TBD | TBD | TBD | TBD | Product flow noun, especially final guided step. |
| workflow.review_export | Review & export | Проверка и выгрузка | TBD | TBD | TBD | TBD | Guided editor final step. |
| workflow.format | Format | Форматировать | TBD | TBD | TBD | TBD | JSON editor action. |
| workflow.raw_json | Raw JSON | Сырой JSON | TBD | TBD | TBD | TBD | Expert/low-level JSON context only. |

## Firefox And Mozilla Terms

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| mozilla.firefox | Firefox | Firefox | Firefox | Firefox | Firefox | Firefox | Brand, do not translate. |
| mozilla.mozilla | Mozilla | Mozilla | Mozilla | Mozilla | Mozilla | Mozilla | Brand, do not translate. |
| mozilla.account | Mozilla account | аккаунт Mozilla | Mozilla-Konto | Mozilla 账号 | compte Mozilla | Mozilla account | zh-CN SUMO uses `Mozilla 账号`; German SUMO uses `Mozilla-Konto`; French SUMO uses `compte Mozilla`; Spanish SUMO currently keeps `Mozilla account` in product copy. |
| mozilla.firefox_home | Firefox Home | Домашняя страница Firefox | Firefox-Startseite | Firefox 主页 | page d’accueil de Firefox | página de inicio de Firefox | Browser home/new-tab surface; verify locale-specific Mozilla wording. |
| mozilla.home_page | Home page | Домашняя страница | Startseite | 主页 | page d’accueil | página de inicio | Generic browser home page. |
| mozilla.address_bar | Address bar | Адресная строка | Adressleiste | 地址栏 | barre d’adresse | barra de direcciones | Prefer native browser UI term. |
| mozilla.search_suggestions | Search suggestions | Поисковые подсказки | Suchvorschläge | 搜索建议 | suggestions de recherche | sugerencias de búsqueda | Search/navigation UI. |
| mozilla.private_browsing | Private Browsing | Приватные окна | Privater Modus | 隐私浏览 | navigation privée | navegación privada | Current ru catalog uses window-based wording; re-check during RU maintenance. |
| mozilla.cookies | Cookies | Куки | Cookies | Cookie | cookies | cookies | German, zh-CN, French, and Spanish Mozilla/SUMO keep this as a visible browser term. |
| mozilla.dns_over_https | DNS over HTTPS | DNS через HTTPS | DNS über HTTPS | 基于 HTTPS 的 DNS | DNS via HTTPS | DNS sobre HTTPS | `DoH` is acceptable only as a constrained technical abbreviation. |
| mozilla.secure_dns | Secure DNS | Защищённый DNS | sicheres DNS | 安全 DNS | DNS sécurisé | DNS seguro | User-facing summary for DNS over HTTPS. |
| mozilla.site_permissions | Site permissions | Разрешения сайтов | Website-Berechtigungen | 网站权限 | permissions des sites | permisos del sitio | Website permission controls. |
| mozilla.addons | Add-ons | Дополнения | Add-ons | 附加组件 | modules complémentaires | complementos | Umbrella term; use locale extension term when specifically describing extensions. |
| mozilla.extensions | Extensions | Расширения | Erweiterungen | 扩展 | extensions | extensiones | Use when specifically describing extension policy/settings. |
| mozilla.website_translations | Website translations | Перевод сайтов | Website-Übersetzungen | 网站翻译 | traductions des sites web | traducciones de sitios web | Feature/behavior label after `GLOC-102` normalization. |
| mozilla.visual_search | Visual search | Визуальный поиск | visuelle Suche | 视觉搜索 | recherche visuelle | búsqueda visual | AI/smart feature surface. |
| mozilla.ai_smart_features | AI & smart features | ИИ и умные функции | KI und intelligente Funktionen | AI 与智能功能 | IA et fonctionnalités intelligentes | IA y funciones inteligentes | Keep the AI step standalone in the Guided editor. |
| mozilla.built_in_vpn | Built-in VPN | Встроенный VPN | Integriertes VPN | 内置 VPN | VPN intégré | VPN integrada | Visible label for the Mozilla VPN/IP protection availability area. |
| mozilla.ip_protection | IP protection | защита IP-адреса | IP-Schutz | IP 保护 | protection IP | protección IP | Policy/schema explanation term; keep `IP` as technical abbreviation unless locale guidance differs. |

## Policy And Schema Terms

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| policy.policy | Policy | Политика | TBD | TBD | TBD | TBD | Firefox enterprise policy. |
| policy.policies | Policies | Политики | TBD | TBD | TBD | TBD | Plural. |
| policy.policy_key | Policy key | Ключ политики | TBD | TBD | TBD | TBD | Technical key in schema or JSON. |
| policy.managed_policy | Managed policy | Управляемая политика | TBD | TBD | TBD | TBD | Contrast with unmanaged/default behavior. |
| policy.managed_preferences | Managed preferences | Управляемые параметры | Verwaltete Einstellungen | 托管首选项 | préférences gérées | preferencias gestionadas | Current All settings section. |
| policy.preference | Preference | Параметр | TBD | TBD | TBD | TBD | Firefox preference. |
| policy.setting | Setting | Настройка | TBD | TBD | TBD | TBD | Generic UI setting/control. |
| policy.schema | Schema | Схема | TBD | TBD | TBD | TBD | JSON/schema model. |
| policy.schema_channel | Schema channel | Канал схемы | TBD | TBD | TBD | TBD | `Release` / `ESR` selector. |
| policy.firefox_release | Firefox Release | Firefox Release | Firefox Release | Firefox Release | Firefox Release | Firefox Release | Product/channel label; keep `Release` when it is a channel name. |
| policy.firefox_esr | Firefox ESR | Firefox ESR | Firefox ESR | Firefox ESR | Firefox ESR | Firefox ESR | Keep `ESR` untranslated. |
| policy.deprecated | Deprecated | Устаревшие | TBD | TBD | TBD | TBD | Schema status. |
| policy.unknown | Unknown | Неизвестные | TBD | TBD | TBD | TBD | Imported or unsupported keys. |
| policy.outside_guided | Outside Guided editor | Вне Пошагового редактора | Außerhalb des geführten Editors | 引导式编辑器之外 | Hors éditeur guidé | Fuera del editor guiado | Review/filter term for items not covered by Guided editor. |
| policy.policies_json | policies.json | policies.json | TBD | TBD | TBD | TBD | File name; never translate. |
| policy.json | JSON | JSON | TBD | TBD | TBD | TBD | File/data format; never translate. |
| policy.yaml | YAML | YAML | TBD | TBD | TBD | TBD | File/data format; never translate. |

## CIS And Compliance Terms

| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| cis.benchmark | CIS benchmark | Бенчмарк CIS | TBD | TBD | TBD | TBD | Compliance source concept. |
| cis.overlay | CIS benchmark overlay | Наложение бенчмарка CIS | TBD | TBD | TBD | TBD | Optional layer over a selected baseline. |
| cis.level_1 | CIS Level 1 | CIS Level 1 | TBD | TBD | TBD | TBD | Keep `CIS` and `Level 1` stable unless locale QA decides otherwise. |
| cis.level_2 | CIS Level 2 | CIS Level 2 | TBD | TBD | TBD | TBD | Keep `CIS` and `Level 2` stable unless locale QA decides otherwise. |
| cis.exceptions | CIS exception notes | Примечания к исключениям CIS | TBD | TBD | TBD | TBD | Notes explaining why a CIS value was kept or changed. |
| cis.manual_review | CIS manual review | Ручная проверка CIS | TBD | TBD | TBD | TBD | Review state for unresolved CIS decisions. |
| cis.decision | CIS decision | Решение CIS | TBD | TBD | TBD | TBD | Compact review label. |
| cis.recommendations | CIS recommendations | Рекомендации CIS | TBD | TBD | TBD | TBD | Recommendation ids or short references only; do not copy long CIS prose. |

## Placeholder And Identifier Examples

| Term ID | English source pattern | ru guidance | de | zh-CN | fr | es-ES | Notes |
|---|---|---|---|---|---|---|---|
| placeholder.count | `{count}` | Preserve exactly | TBD | TBD | TBD | TBD | May move within a sentence. |
| placeholder.name | `{name}` | Preserve exactly | TBD | TBD | TBD | TBD | Profile or user-provided name. |
| placeholder.detail | `{detail}` | Preserve exactly | TBD | TBD | TBD | TBD | Error detail; surrounding grammar should not assume its shape. |
| placeholder.schema | `{schema}` | Preserve exactly | TBD | TBD | TBD | TBD | Schema label or channel. |
| placeholder.value | `{value}` | Preserve exactly | TBD | TBD | TBD | TBD | Dynamic value. |
| identifier.policy_key | `DisablePrivateBrowsing` | Preserve exactly | TBD | TBD | TBD | TBD | Firefox policy key example. |
| identifier.preference_key | `browser.startup.homepage` | Preserve exactly | TBD | TBD | TBD | TBD | Firefox preference key example. |
| identifier.url | `https://example.org` | Preserve exactly | TBD | TBD | TBD | TBD | URL example. |
