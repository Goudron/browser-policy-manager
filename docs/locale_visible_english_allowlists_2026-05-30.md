# Locale Visible English Allowlists

Date: `2026-05-30`

Backlog item: `GLOC-306`

Catalogs: `app/i18n/{ru,de,zh-CN,fr,es-ES}.json`

Glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

Placeholder and identifier rules: `docs/locale_placeholder_identifier_rules_2026-05-29.md`

## Scope

This document records the visible English fragments that may remain in non-English locale catalogs
without being treated as untranslated prose.

The `GLOC-306` guard now covers full-catalog source-phrase reuse for every runtime non-English
locale. It catches ordinary untranslated English in any catalog string while preserving technical
identifiers, brands, and Mozilla terms that official locale evidence keeps in English.

## Shared Allowed Categories

These fragments are allowed in visible UI when the source string intentionally exposes them:

- Brands and product names: `Firefox`, `Mozilla`, `Pocket`, `Microsoft`, `Windows`, `DuckDuckGo`,
  `Bing`, `AdGuard`, `uBlock`, `Browser Policy Manager`.
- File names and formats: `policies.json`, `JSON`, `YAML`, `CSV`.
- Channels and compliance labels: `ESR`, `Release`, `CIS`, `Level 1`, `Level 2`.
- Protocols and technical abbreviations: `DNS`, `DoH`, `HTTPS`, `HTTP`, `VPN`, `IP`, `URL`, `URI`,
  `MIME`, `SPNEGO`, `NTLM`, `SAML`, `OIDC`, `IdP`, `LDAP`, `SSO`.
- Literal values and examples: `true`, `false`, `null`, `default`, `locked`, `<local>`,
  `https://www.example.org/search?q={searchTerms}`.
- Identifiers: Firefox policy keys, preference keys, API paths, browser URLs, extension IDs, and
  email-like examples.

## Locale-Specific Allowed Mozilla Terms

| Locale | Allowed visible English or Latin fragments | Rationale |
|---|---|---|
| `ru` | `Firefox`, `Mozilla`, `DNS`, `HTTPS`, `VPN`, `IP`, `JSON`, `YAML`, `ESR`, `Release`, `CIS` | Current Russian catalog already has strict visible Latin token coverage. |
| `de` | `Firefox`, `Mozilla`, `Add-ons`, `Cookies`, `DNS`, `HTTPS`, `VPN`, `IP`, `JSON`, `YAML`, `ESR`, `Release`, `CIS` | German SUMO/Pontoon keep several browser terms and abbreviations in Latin form. |
| `zh-CN` | `Firefox`, `Mozilla`, `Cookie`, `DNS`, `HTTPS`, `VPN`, `IP`, `AI`, `JSON`, `YAML`, `ESR`, `Release`, `CIS` | Simplified Chinese Mozilla terminology keeps brands and technical abbreviations in Latin form. |
| `fr` | `Firefox`, `Mozilla`, `DNS`, `HTTPS`, `VPN`, `IP`, `JSON`, `YAML`, `ESR`, `Release`, `CIS` | French audit localizes major Mozilla terms while preserving brands and technical abbreviations. |
| `es-ES` | `Firefox`, `Mozilla`, `Mozilla account`, `Mozilla accounts`, `DNS`, `HTTPS`, `VPN`, `IP`, `JSON`, `YAML`, `ESR`, `Release`, `CIS` | Spanish SUMO currently keeps `Mozilla account` in product/account copy. |

## Forbidden Regression Fragments

These fragments must not reappear in the audited locale surfaces:

| Locale | Forbidden fragments |
|---|---|
| `ru` | `DNS over HTTPS`, `IP protection`, `Firefox Home`, `Enabled`, `Chatbot`, `LinkPreviews`, `TabGroups` |
| `de` | `Private browsing`, `DNS-over-HTTPS`, `Firefox Account`, `Mozilla account`, `Built-in VPN` |
| `zh-CN` | `Mozilla 账户`, `DNS over HTTPS`, `DNS-over-HTTPS`, `Built-in VPN`, `Mozilla sign-in` |
| `fr` | `compte Mozillas`, `DNS over HTTPS`, `DNS-over-HTTPS`, `Private browsing`, `AI & fonctionnalités intelligentes`, `AI and fonctionnalités intelligentes` |
| `es-ES` | `cuenta Mozillas`, `DNS over HTTPS`, `DNS-over-HTTPS`, `Private browsing`, `AI & funciones inteligentes`, `AI and funciones inteligentes` |

## Guard Rules

- Preserve shared allowed categories exactly.
- Allow locale-specific Mozilla exceptions only when they are recorded in the global glossary and the
  locale audit evidence log.
- Flag ordinary English commands or prose such as `Open profile`, `Save changes`, `Use this when`,
  and `Task-first setup` unless they are part of an explicit future QA exception.
- Apply the current guard to the full catalog, not only to high-signal wizard and All settings
  surfaces.
