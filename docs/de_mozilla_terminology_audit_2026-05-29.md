# German Mozilla Terminology Audit

Date: `2026-05-29`

Backlog item: `GLOC-301`

Catalog: `app/i18n/de.json`

Glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

## Scope

This audit verifies the required German Firefox/Mozilla terminology set from
`docs/mozilla_terminology_verification_workflow_2026-05-29.md`.

The audit is terminology-focused. It does not claim that every German sentence in the first-pass
runtime catalog has been fully copy-edited.

## Evidence Log

| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |
|---|---|---|---|---|---|---|
| `mozilla.firefox` | Firefox | Firefox | German Pontoon team/project context keeps brand names unchanged: `https://pontoon.mozilla.org/de/` | German SUMO Firefox articles keep `Firefox`: `https://support.mozilla.org/de/kb/startseite-festlegen` | accept | Brand, do not translate. |
| `mozilla.mozilla` | Mozilla | Mozilla | German Pontoon team/project context keeps brand names unchanged: `https://pontoon.mozilla.org/de/` | German SUMO account articles keep `Mozilla`: `https://support.mozilla.org/de/kb/firefox-konto-auf-supportmozillaorg` | accept | Brand, do not translate. |
| `mozilla.account` | Mozilla account | Mozilla-Konto | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Mozilla-Konto`: `https://support.mozilla.org/de/kb/firefox-konto-auf-supportmozillaorg` | change | Updated visible `Firefox Account(s)` strings to `Mozilla-Konto` / `Mozilla-Konten`. |
| `mozilla.firefox_home` | Firefox Home | Firefox-Startseite | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Firefox-Startseite`: `https://support.mozilla.org/de/kb/startseite-festlegen` | accept | Keep hyphenated product term. |
| `mozilla.home_page` | Home page | Startseite | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Startseite`: `https://support.mozilla.org/de/kb/startseite-festlegen` | accept | Generic home page term. |
| `mozilla.address_bar` | Address bar | Adressleiste | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Adressleiste`: `https://support.mozilla.org/de/kb/die-suchleiste-in-firefox-verwenden` | accept | Use for urlbar/search surface. |
| `mozilla.search_suggestions` | Search suggestions | Suchvorschläge | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Suchvorschläge`: `https://support.mozilla.org/de/kb/suchvorschlaege-in-firefox` | accept | Updated several on/off labels to avoid mixed English. |
| `mozilla.private_browsing` | Private Browsing | Privater Modus | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Privater Modus`: `https://support.mozilla.org/de/kb/privater-modus` | change | Replaced remaining `Private browsing` and lowercase variants in key visible strings. |
| `mozilla.cookies` | Cookies | Cookies | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO private browsing and settings articles keep `Cookies`: `https://support.mozilla.org/de/kb/privater-modus` | accept | Keep English browser term as German Mozilla wording. |
| `mozilla.dns_over_https` | DNS over HTTPS | DNS über HTTPS | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `DNS über HTTPS`: `https://support.mozilla.org/de/kb/dns-over-https` | change | Replaced visible `DNS-over-HTTPS` remnants with `DNS über HTTPS`. |
| `mozilla.secure_dns` | Secure DNS | sicheres DNS | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO DoH article uses `sicheres DNS`: `https://support.mozilla.org/de/kb/dns-over-https` | accept | Use as explanatory summary, not as replacement for the feature name. |
| `mozilla.site_permissions` | Site permissions | Website-Berechtigungen | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Website-Berechtigungen`: `https://support.mozilla.org/de/kb/add-ons-fur-website-berechtigungen` | accept | Keep for site permission categories. |
| `mozilla.addons` | Add-ons | Add-ons | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Add-ons`: `https://support.mozilla.org/de/kb/Add-ons%20deinstallieren` | accept | Umbrella term. |
| `mozilla.extensions` | Extensions | Erweiterungen | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO distinguishes `Erweiterungen`: `https://support.mozilla.org/de/kb/verwaltung-optionaler-berechtigungen-erweiterungen` | accept | Use when specifically describing extension policy/settings. |
| `mozilla.website_translations` | Website translations | Website-Übersetzungen | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | SUMO uses `Website-Übersetzungen`: `https://support.mozilla.org/de/kb/vollstandige-webseiten-in-firefox-ubersetzen` | accept | Keep plural feature label. |
| `mozilla.visual_search` | Visual search | visuelle Suche | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Natural German term; revisit during AI-specific QA if Mozilla publishes localized wording. |
| `mozilla.ai_smart_features` | AI & smart features | KI und intelligente Funktionen | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Keep `KI`; revisit during AI-specific QA. |
| `mozilla.built_in_vpn` | Built-in VPN | Integriertes VPN | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | German SUMO page is not fully localized; English fallback describes built-in VPN: `https://support.mozilla.org/en-US/kb/use-firefox-vpn-on-firefox` | accept | Keep natural German term and track as fallback-evidence decision. |
| `mozilla.ip_protection` | IP protection | IP-Schutz | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | English built-in VPN article mentions `IPProtectionAvailable`: `https://support.mozilla.org/en-US/kb/use-firefox-vpn-on-firefox` | accept | Keep policy key technical where it appears; use `IP-Schutz` only in prose. |
| `policy.managed_preferences` | Managed preferences | Verwaltete Einstellungen | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | Firefox settings article uses `Einstellungen`: `https://support.mozilla.org/de/kb/firefox-einstellungen` | accept | Use `Einstellungen` for user-facing Firefox settings/preferences. |
| `policy.firefox_release` | Firefox Release | Firefox Release | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | BPM schema/channel source uses Release as a channel identifier. | accept | Keep `Release` unchanged as a channel label. |
| `policy.firefox_esr` | Firefox ESR | Firefox ESR | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | BPM schema/channel source uses ESR as a channel identifier. | accept | Keep `ESR` unchanged. |
| `policy.outside_guided` | Outside Guided editor | Außerhalb des geführten Editors | Pontoon source priority checked through German team page: `https://pontoon.mozilla.org/de/` | No SUMO equivalent; this is a BPM UI review/filter term. | accept | Product-specific UI term. |

## Catalog Changes

- Replaced visible `Firefox Account(s)` remnants with `Mozilla-Konto` / `Mozilla-Konten`.
- Replaced visible `Private browsing` remnants with `Privater Modus`.
- Replaced visible `DNS-over-HTTPS` remnants with `DNS über HTTPS`.
- Cleaned several German term-adjacent labels for search suggestions, private mode, and account
  sign-in while preserving placeholders and technical identifiers.

## Remaining Follow-Up

The German catalog still contains first-pass prose that needs a broader language copy-edit. That is
outside the terminology-only scope of `GLOC-301` and should be handled by later locale QA or UI
script tasks.
