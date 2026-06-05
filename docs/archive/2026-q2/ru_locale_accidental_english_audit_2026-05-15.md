# Russian Locale Accidental English Audit

Date: `2026-05-15`

Scope: `app/i18n/ru.json`.

This is an internal localization QA note for LOC-002 and LOC-003. It is not an in-app documentation surface.

## Fixed Translation Defects

The audit found and replaced visible English fragments or unnecessary English-derived wording in Russian UI copy:

| Previous fragment | Replacement direction |
|---|---|
| `allowlist` | `список разрешённых источников` / `списки разрешённых источников установки` |
| `approved-набор` | `одобренный набор` |
| `Контролов` / `Контролы` as UI noun | `Элементов управления` / `Элементы управления` |
| `outcome-группе` | `группе результата` |
| `override-правила` | `правила переопределения` |
| `финального review` | `финальной проверки` |
| `cookie` in Russian prose | `куки` |

## Mozilla Terminology Follow-up

LOC-003 verified the remaining Firefox/Mozilla product terms against current Russian Mozilla/SUMO usage and aligned the visible UI copy:

| Previous fragment | Replacement direction |
|---|---|
| `DNS over HTTPS` in Russian visible labels | `DNS через HTTPS` |
| `DoH-настроек` | `Настроек DNS через HTTPS` |
| `Firefox Home` / standalone `Home` in Russian prose | `Домашняя страница Firefox` or grammatical forms such as `Домашней страницы Firefox` |
| `IP protection` | `защита IP-адреса` |

## Runtime String Follow-up

LOC-004 reviewed dynamic UI strings produced by JavaScript and templates. The profile library counter was moved from hardcoded JavaScript labels into the supported locale catalogs:

| Runtime surface | Locale-backed keys |
|---|---|
| Library profile counter | `profiles.library_count_one`, `profiles.library_count_few`, `profiles.library_count_many` |

The runtime i18n contract test now scans static JavaScript and templates for `t("profiles...")`, `data-i18n`, `data-i18n-placeholder`, `data-i18n-title`, and `data-i18n-aria-label` keys, and verifies that each referenced key exists in both `en` and `ru`.

## Allowlist Guard

LOC-005 added a Russian-locale allowlist guard. It removes non-prose technical material before checking the remaining Latin tokens:

- runtime placeholders such as `{count}`;
- URLs and email-like values;
- dotted preference/policy identifiers such as `browser.startup.page`;
- colon identifiers such as `about:config`.

The test then allows:

- all-uppercase technical abbreviations such as `JSON`, `DNS`, `VPN`, `CIS`;
- CamelCase identifiers such as `AIControls`, `ExtensionSettings`, `SameSite`;
- a short explicit allowlist for visible brands and accepted technical/product fragments such as `Firefox`, `Mozilla`, `Pocket`, `Windows`, `Preferences`, `true`, and `false`.

Everything else fails the test, which is meant to catch new accidental English prose in `ru.json` before it reaches the UI.

## Browser QA Follow-up

LOC-006 added a Chromium regression pass for the four primary Russian UI modes:

- Library;
- Guided editor;
- All settings;
- JSON editor.

The browser check verifies Russian route markers, rejects known accidental-English fragments such as `Guided editor`, `All settings catalog`, and `Advanced settings`, and confirms that each primary route stays within the viewport width without horizontal document overflow.

## Accepted Latin Fragments

The remaining Latin text in `ru.json` was treated as valid when it falls into one of these categories:

- Brands and product names: `Firefox`, `Mozilla`, `Pocket`, `Windows`, `Microsoft Entra`, `DuckDuckGo`, `uBlock Origin`, `AdGuard`, `HTTPS Everywhere`.
- File formats and technical identifiers: `JSON`, `policies.json`, `ESR`, `Release`, `CIS`, `SOC`, `PDF`, `VPN`, `URL`, `URI`, `MIME`, `TLS`, `DNS`, `HTTPS`, `HTTP`, `FTP`, `SSL`, `SOCKS`, `PAC`, `WPAD`, `SPNEGO`, `NTLM`, `TRR`.
- Firefox policy keys, preference keys, and schema identifiers: examples include `Preferences`, `ExtensionSettings`, `InstallAddonsPermission`, `GenerativeAI`, `AIControls`, `SameSite`, `browser.startup.page`, `browser.tabs.warnOnClose`.
- Placeholders and runtime interpolation variables: `{name}`, `{count}`, `{value}`, `{schema}`, `{detail}`, `{path}`, `{time}`, `{revision}`.
- URLs, email-like placeholders, extension IDs, and query strings.
- Boolean and method literals shown as editable technical values: `true`, `false`, `GET`, `POST`.

## Follow-up

Future locale edits should keep these forms aligned with the glossary and re-check Mozilla/SUMO/Pontoon terminology when Firefox changes the feature names.
