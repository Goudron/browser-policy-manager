# Locale Placeholder And Identifier Rules

Date: `2026-05-29`

Backlog item: `GLOC-105`

Applies to locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`

Source inventory summary: `docs/source_string_inventory_en_2026-05-21.md`

Archived raw inventory: `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`

Global glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

Visible English allowlists: `docs/locale_visible_english_allowlists_2026-05-30.md`

## Goal

Make locale review deterministic: reviewers should be able to tell the difference between an
untranslated English defect and a technical token that must stay unchanged.

## Preserve Exactly

| Token family | Examples | Rule |
|---|---|---|
| Runtime placeholders | `{count}`, `{name}`, `{detail}`, `{schema}`, `{value}`, `{searchTerms}` | Preserve the complete token exactly, including braces and case. You may move it within the sentence. |
| Firefox policy keys | `DisablePrivateBrowsing`, `ExtensionSettings`, `InstallAddonsPermission`, `IPProtectionAvailable` | Preserve exactly. Do not split CamelCase or localize the words inside the key. |
| Firefox preference keys | `browser.startup.homepage`, `browser.tabs.warnOnClose`, `browser.startup.page` | Preserve exactly, including dots and capitalization. |
| File names and formats | `policies.json`, `JSON`, `YAML`, `CSV` | Preserve exactly. Surrounding prose may be localized. |
| Schema/channel labels | `ESR`, `Release`, `CIS`, `Level 1`, `Level 2` | Preserve exactly unless a locale-specific glossary entry says otherwise. |
| URLs and query strings | `https://example.org`, `q={searchTerms}&source=firefox` | Preserve URL syntax and embedded placeholders exactly. Do not localize domains, paths, or query parameter names. |
| API paths and browser URLs | `/api/profiles`, `about:config`, `about:profiles` | Preserve exactly. |
| Extension IDs and email-like IDs | `uBlock0@raymondhill.net`, `bad_addon_id@mozilla.org`, `ops@example.org` | Preserve exactly. |
| Protocols and abbreviations | `HTTPS`, `HTTP`, `DNS`, `DoH`, `VPN`, `URI`, `URL`, `MIME`, `SPNEGO`, `NTLM` | Preserve as technical abbreviations unless the glossary has a localized prose term. |
| Literal values | `true`, `false`, `null`, `default`, `locked`, `<local>` | Preserve exactly when the value is shown as a literal setting value. |
| Product and brand names | `Firefox`, `Mozilla`, `BPM`, `Browser Policy Manager`, `DuckDuckGo`, `AdGuard`, `uBlock` | Preserve brand spelling and casing unless official brand guidance says otherwise. |

## Translate Surrounding Prose

Technical tokens do not make the whole string English-only. Translate the explanatory text around
them.

| English source | Good localized shape | Bad localized shape |
|---|---|---|
| `Validation OK for {schema}.` | localized words + unchanged `{schema}` | translated or renamed `{schema}` |
| `Download Firefox policies.json` | localized action + unchanged `Firefox policies.json` | localized `policies.json` file name |
| `Search by control, policy key, preference, or settings area` | fully localized prose | leaving `Search by control` in English |
| `Use true/false, numbers, or text.` | localized prose + unchanged `true`/`false` literals | localizing `true` and `false` as literal values |

## Placeholder Review Rules

1. Every target locale key must contain the same placeholder set as the English source key.
2. Placeholder order may change when grammar requires it.
3. Placeholder spelling may not change: `{count}` is valid, `{counts}` and `{_COUNT_}` are defects.
4. Do not add a placeholder that is not present in English.
5. Do not remove a placeholder unless the source string is also changed and the inventory is
   regenerated.
6. Embedded placeholders inside URL examples must stay embedded, for example
   `https://www.example.org/search?q={searchTerms}`.

## Identifier Review Rules

1. Treat CamelCase policy names and dotted preference names as identifiers, not prose.
2. Do not insert spaces, punctuation, or locale-specific quotation marks inside identifiers.
3. Do not inflect identifiers for grammar. Move the surrounding words instead.
4. Keep examples realistic but neutral. Example domains may stay in English because they are
   technical placeholders, not visible prose.
5. If an identifier appears in a sentence as a concept rather than a literal key, translate the
   concept and keep the literal key only if the source string includes it.

## Brand And Mozilla Term Rules

1. Preserve official brand spelling for `Firefox` and `Mozilla`.
2. Use `docs/mozilla_terminology_verification_workflow_2026-05-29.md` for Firefox feature terms such
   as `Firefox Home`, `Private Browsing`, `Website translations`, `Add-ons`, and `DNS over HTTPS`.
3. A Mozilla term may be localized when Pontoon/SUMO shows a locale-specific product term.
4. A brand or product term left in English is not an untranslated defect when the glossary or
   Pontoon/SUMO evidence says to keep it.

## HTML-Sensitive And Literal Fragments

The source inventory currently records one HTML-sensitive literal:

| Key | Literal | Rule |
|---|---|---|
| `profiles.wizard_proxy_passthrough_placeholder` | `<local>` | Preserve exactly. It is a proxy bypass literal, not markup. |

If future source strings add angle-bracket or entity-like fragments, update
`docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json` or create a new inventory snapshot before
translation.

## Reviewer Checklist

Use this checklist before accepting a locale catalog:

- Placeholder set matches English for every key.
- No placeholder token was renamed, translated, split, or stripped of braces.
- Policy keys, preference keys, URLs, API paths, extension IDs, file names, and literal values remain
  exact.
- Brand and Mozilla terms match the global glossary and the Mozilla terminology workflow evidence.
- English words outside the allowed technical categories are reviewed as possible translation
  defects.
- Visible English fragments match `docs/locale_visible_english_allowlists_2026-05-30.md`; ordinary
  English prose is not accepted just because technical terms are allowed.
- The catalog is valid JSON.
- The relevant locale parity and accidental-English tests pass once those tests exist for the target
  locale.

## Defect Labels

Use these labels in locale audit notes:

| Label | Meaning |
|---|---|
| `placeholder-missing` | Target string dropped a source placeholder. |
| `placeholder-renamed` | Target string changed placeholder spelling or braces. |
| `identifier-translated` | Technical key, URL, file name, or literal value was localized incorrectly. |
| `brand-casing` | Brand/product spelling or casing no longer matches glossary guidance. |
| `untranslated-prose` | English prose remains without being an allowed technical token. |
| `needs-mozilla-evidence` | Term choice needs Pontoon/SUMO confirmation. |

## Source Data

The complete placeholder inventory is in `placeholder_map` inside
`docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`.

The complete technical-token inventory is in `technical_token_map` inside
`docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`.
