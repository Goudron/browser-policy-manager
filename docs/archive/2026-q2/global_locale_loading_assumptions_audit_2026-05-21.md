# Global Locale Loading Assumptions Audit

Date: `2026-05-21`

Backlog item: `GLOC-002`

Scope: current locale loading, picker, bootstrap, templates, tests, and documentation assumptions
that still behave as if BPM only has `en` and `ru` UI locales.

## Current Boundary

`app/core/locales.py` is the target locale matrix introduced by `GLOC-001`.

- Target first-class UI locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`.
- Active runtime catalogs today: `en`, `ru`.
- English remains the source product language.
- New locale catalogs must not be exposed as active runtime catalogs until their JSON files exist,
  pass key and placeholder parity, and pass terminology review.

## Assumptions And Decisions

| Area | Current assumption | Implementation decision |
|---|---|---|
| `app/core/config.py` | `SUPPORTED_LOCALES` historically meant exactly `["en", "ru"]`. | Keep `SUPPORTED_LOCALES` as active, shippable catalog locales. `de`, `zh-CN`, `fr`, and `es-ES` were promoted through `GLOC-204`; use `TARGET_UI_LOCALES` from `app/core/locales.py` when tests or planning need the complete first-class locale set. |
| `app/main.py` | `/i18n/{locale}.json` accepts only `settings.SUPPORTED_LOCALES` and then checks for a matching JSON file. | Endpoint remains tied to active catalogs. After `GLOC-204`, all six target UI locales have active runtime catalogs. |
| `app/web/profiles.py` | `_resolve_request_locale()` lowercases `Accept-Language`, strips everything after the first hyphen, and only matches active locales. This works for `ru-RU -> ru`, but cannot resolve `zh-CN` or `es-ES` correctly. | Update in `GLOC-004` to use `LOCALE_BROWSER_LANGUAGE_MATCHES`, preserve canonical BCP 47 output, and support configured fallbacks such as `de-AT -> de`, `fr-CA -> fr`, and `es-MX -> es-ES`. |
| `app/web/profiles.py` | `_load_locale_catalog(locale)` directly maps a locale code to `app/i18n/{locale}.json`. | Keep direct file loading, but only call it with canonical active catalog codes. Add fallback handling in `GLOC-004` so unsupported or unavailable locales resolve before this function is called. |
| `app/templates/profiles/_page_header.html` | Locale picker options are hardcoded as `system`, `en`, and `ru`. | Update in `GLOC-003` to render options from locale metadata instead of hardcoded template options. Add locale label keys or server-rendered native labels for `de`, `zh-CN`, `fr`, and `es-ES`. |
| `app/static/profiles_runtime.js` | `applyLanguageMode()` only accepts `system`, `en`, and `ru`; all other values normalize to `system`. | Update in `GLOC-003` to read available locale option metadata from a shared source. Revisit in `GLOC-004` so picker modes and resolved browser locales use the same canonical locale codes. |
| `app/static/profiles_library_bootstrap.js` | Library-only runtime has the same hardcoded language mode allowlist: `system`, `en`, `ru`. | Update together with `profiles_runtime.js` in `GLOC-003` so library and editor routes expose the same locale choices. |
| `app/static/profiles_platform.js` | `resolveBrowserLanguage()` returns `ru` for Russian browser languages and `en` for everything else. | Replace in `GLOC-004` with matrix-backed matching. This is the main client-side blocker for `de`, `zh-CN`, `fr`, and `es-ES` system mode. |
| `app/static/profiles_runtime.js` and `app/static/profiles_library_bootstrap.js` | `loadLocale(lang)` fetches `/i18n/${lang}.json` and logs failures without applying a configured fallback. | Add canonical fallback behavior in `GLOC-004`. Until new catalogs exist, do not let the picker request `de`, `zh-CN`, `fr`, or `es-ES`. |
| `app/static/profiles_shared.js` | Initial locale state trusts `window.__BPM_INITIAL_LANG__` or the document `lang` value and embedded JSON. | No immediate change. Once server-side locale resolution is matrix-backed, this remains a narrow bootstrap cache. |
| `app/static/profiles_page_bootstrap.js` | Page bootstrap mirrors `data-initial-lang`, `document.documentElement.lang`, and embedded locale JSON. | No immediate change. Keep it passive; update only if `GLOC-004` changes the bootstrap payload shape. |
| `app/templates/profiles/_page_document.html` | `<html lang="{{ initial_lang }}">` and `data-initial-lang` assume the server has already resolved a valid active locale. | No immediate change. Server resolver changes in `GLOC-004` should preserve this contract with canonical BCP 47 codes. |
| `app/templates/profiles/_page_legacy_markers.html` | Legacy marker text includes `/i18n/en.json` and `/i18n/ru.json` only. | Update in `GLOC-003` or `GLOC-401` if smoke tests continue to depend on these static markers. Prefer removing locale-specific marker expectations once runtime contract tests cover the real catalog routes. |
| `app/static/profiles_extensions.js` | Requested Firefox browser locales default to `["en-US", "ru"]` for profile policy presets. | Not part of UI locale expansion. Keep separate from BPM UI locales unless a later product task decides Firefox policy presets should follow the UI locale matrix. |
| `README.md` | Product summary and localization section previously said English primary UI with Russian localization, and listed only `en` and `ru`. | Updated in `GLOC-005` to describe the six target locales, active runtime catalogs, English source-language policy, and catalog promotion rule. |
| `docs/archive/2026-q2/ui_locale_glossary_en_ru_2026-05-15.md` | Glossary scope previously implied supported UI locales remain only `en` and `ru`. | Updated in `GLOC-005` to mark the file as the historical EN/RU reference until `GLOC-103` / `GLOC-702` supersedes it with a six-locale terminology sheet. |
| `tests/test_ui_runtime_i18n_contract.py` | Runtime key existence previously covered only `en` and `ru`. | Updated in `GLOC-401` to scan JavaScript and templates for runtime locale-key shapes and require every referenced key in all active catalog locales from the locale matrix. |
| `tests/test_ru_locale_quality.py` | Accidental-English and Mozilla terminology guards exist only for Russian. | Extend in `GLOC-306` with locale-specific allowlists for the new locales after terminology QA begins. |
| `tests/test_web_profiles_page.py` and `tests/test_ui_smoke_profile_workflow.py` | Many endpoint and UI assertions fetch only `/i18n/en.json` and `/i18n/ru.json`, and locale option assertions cover only English and Russian labels. | Update in `GLOC-003`, `GLOC-004`, and `GLOC-601` as the picker, fallback resolver, and browser smoke matrix expand. Keep EN/RU checks as regression anchors. |
| `tests/test_main_and_security_unit.py` | Locale endpoint tests monkeypatch active supported locales as `["en"]` or `["en", "ru"]`. | Keep for active-catalog endpoint behavior. Add matrix-specific tests separately when endpoint promotion starts for the new catalogs. |
| `tests/test_locale_matrix.py` | New matrix test asserts target locales and active catalogs separately. | Keep as the `GLOC-001` contract. Update only when a new catalog is promoted from target-only to active runtime support. |

## Follow-Up Order

1. `GLOC-003`: render locale picker options from locale metadata and add labels for all target
   locales without activating missing catalogs prematurely.
2. `GLOC-004`: replace server and client browser-language matching with matrix-backed canonical
   fallback behavior.
3. `GLOC-005`: updated README and supported-locale documentation to distinguish target locales
   from currently active runtime catalogs.
4. `GLOC-201` through `GLOC-207`: add and validate new catalogs, then promote each catalog in the
   locale matrix.
5. `GLOC-401` and later QA tasks: expand runtime, layout, browser, and accidental-English tests to
   cover all active catalogs.
