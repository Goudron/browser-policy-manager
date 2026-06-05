# Mozilla Terminology Verification Workflow

Date: `2026-05-29`

Backlog item: `GLOC-104`

Applies to locales: `de`, `zh-CN`, `fr`, `es-ES`, and future locale maintenance for `ru`.

Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

Source inventory summary: `docs/source_string_inventory_en_2026-05-21.md`

Archived raw inventory: `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`

## Goal

Use one repeatable process to verify Firefox and Mozilla terminology before new locale catalogs are
accepted. The workflow should leave enough evidence that a future maintainer can understand why a
term was accepted, changed, or intentionally kept different from Pontoon/SUMO wording.

## Source Priority

| Priority | Source | Use For | Notes |
|---|---|---|---|
| 1 | Mozilla Pontoon Firefox project and target-locale team pages | Product UI terminology, casing, and approved translations. | Prefer approved Firefox strings over unreviewed suggestions. Check Firefox Enterprise when the term is enterprise-policy specific. |
| 2 | SUMO localized Firefox articles | User-facing support wording and feature names. | Use localized article pages through SUMO's language switch. If no localized article exists, record English SUMO as fallback evidence. |
| 3 | English SUMO and current BPM English source | Source meaning and feature boundaries. | Use when Pontoon/SUMO target-locale evidence is missing or contradictory. |
| 4 | Locale reviewer decision | Final tie-breaker. | Record the reason in the evidence log and glossary notes. |

## Required Term Set

Each locale terminology audit must cover at least these global glossary IDs:

| Group | Term IDs |
|---|---|
| Mozilla brands and account | `mozilla.firefox`, `mozilla.mozilla`, `mozilla.account` |
| Firefox surfaces | `mozilla.firefox_home`, `mozilla.home_page`, `mozilla.address_bar`, `mozilla.search_suggestions` |
| Privacy and permissions | `mozilla.private_browsing`, `mozilla.cookies`, `mozilla.dns_over_https`, `mozilla.secure_dns`, `mozilla.site_permissions` |
| Add-ons and extensions | `mozilla.addons`, `mozilla.extensions` |
| Translation and AI surfaces | `mozilla.website_translations`, `mozilla.visual_search`, `mozilla.ai_smart_features` |
| VPN/IP protection | `mozilla.built_in_vpn`, `mozilla.ip_protection` |
| Policy-adjacent labels | `policy.managed_preferences`, `policy.firefox_release`, `policy.firefox_esr`, `policy.outside_guided` |

Locale-specific audits may add more terms, but they must not skip the required set without recording
why the term is irrelevant for that locale.

## Verification Steps

1. Start from `docs/ui_locale_glossary_global_2026-05-29.md`.
2. Filter the rows where the target locale column is `TBD` or where the note mentions Mozilla,
   Firefox, policy, preference, add-on, privacy, permission, update, translation, AI, VPN, or IP.
3. For each term, search Pontoon in this order:
   - Target locale Firefox project.
   - Target locale Firefox Enterprise project when the term is policy or enterprise-specific.
   - Target locale team terminology download if Pontoon exposes one.
4. Search SUMO in the target locale:
   - Use the language switch on the English article when available.
   - Compare the localized title, navigation labels, headings, and repeated prose terms.
   - Prefer recent Firefox desktop articles over forum posts or old archived wording.
5. Compare the evidence:
   - If Pontoon and SUMO agree, use that term.
   - If Pontoon and SUMO differ, prefer Pontoon for in-product labels and SUMO for explanatory
     support-style prose, then record the split.
   - If only English evidence exists, keep the target glossary cell as `TBD` or mark it
     `needs-review`; do not invent a term silently.
6. Update the global glossary:
   - Fill the target locale cell.
   - Add a compact note when a term is intentionally different from English word order, casing, or
     literal meaning.
   - Keep placeholders and technical identifiers unchanged.
7. Create or update a locale audit document for the locale task, for example
   `docs/de_mozilla_terminology_audit_YYYY-MM-DD.md`.
8. Run the locale glossary/documentation tests.

## Evidence Log Template

Use this table in each locale audit document.

| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |
|---|---|---|---|---|---|---|
| `mozilla.firefox_home` | Firefox Home | TBD | URL + short context | URL + short context | accept/change/needs-review | Explain conflicts or casing. |

Evidence should be short and linked. Do not paste long Pontoon or SUMO passages into the repo.

## Baseline Source Links

| Source | URL |
|---|---|
| Pontoon Firefox project | `https://pontoon.mozilla.org/projects/firefox/` |
| Pontoon German team | `https://pontoon.mozilla.org/de/` |
| Pontoon Simplified Chinese Firefox project | `https://pontoon.mozilla.org/zh-CN/firefox/` |
| Pontoon French team | `https://pontoon.mozilla.org/fr/` |
| Pontoon Spanish (Spain) Firefox project | `https://pontoon.mozilla.org/es-ES/firefox/` |
| SUMO Firefox settings article | `https://support.mozilla.org/en-US/kb/firefox-options-preferences-and-settings` |
| SUMO Firefox Translations article | `https://support.mozilla.org/en-US/kb/website-translation` |
| SUMO DNS over HTTPS article | `https://support.mozilla.org/en-US/kb/firefox-dns-over-https` |
| SUMO Site Permission Add-ons article | `https://support.mozilla.org/en-US/kb/site-permission-add-ons` |
| SUMO built-in VPN article | `https://support.mozilla.org/en-US/kb/use-firefox-vpn-on-firefox` |

For SUMO target-language evidence, open the English article and use the page language switch. Record
the exact localized URL that was checked.

## Conflict Rules

- Do not translate `Firefox`, `Mozilla`, `JSON`, `YAML`, `policies.json`, `ESR`, `Release`, `CIS`,
  policy keys, preference keys, URLs, API paths, or extension IDs unless official Mozilla evidence
  shows a localized visible label.
- Do not prefer literal translation when Mozilla has an established term for the locale.
- Do not accept machine translation by itself as evidence.
- If a locale's Mozilla community keeps an English product term, copy that choice into the glossary
  and explain it in the notes column.
- If BPM needs a policy/schema term that SUMO does not expose, keep the technical term stable and
  explain it in the locale audit document.

## Done Criteria Per Locale

- Required term set reviewed.
- Global glossary target locale column updated or explicitly left `TBD`/`needs-review`.
- Locale audit document includes Pontoon/SUMO evidence links for changed or accepted Mozilla terms.
- Any catalog string changes preserve placeholders and technical identifiers.
- Relevant locale/documentation tests pass.
