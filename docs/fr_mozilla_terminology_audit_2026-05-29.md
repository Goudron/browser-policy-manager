# French Mozilla Terminology Audit

Date: `2026-05-29`

Backlog item: `GLOC-303`

Catalog: `app/i18n/fr.json`

Glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

## Scope

This audit verifies the required French Firefox/Mozilla terminology set from
`docs/mozilla_terminology_verification_workflow_2026-05-29.md`.

The audit is terminology-focused. It does not claim that every French sentence in the first-pass
runtime catalog has been fully copy-edited.

## Evidence Log

| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |
|---|---|---|---|---|---|---|
| `mozilla.firefox` | Firefox | Firefox | French Pontoon team/project context keeps brand names unchanged: `https://pontoon.mozilla.org/fr/` | French SUMO Firefox articles keep `Firefox`: `https://support.mozilla.org/fr/kb/comment-definir-page-accueil` | accept | Brand, do not translate. |
| `mozilla.mozilla` | Mozilla | Mozilla | French Pontoon team/project context keeps brand names unchanged: `https://pontoon.mozilla.org/fr/` | French SUMO account and VPN articles keep `Mozilla`: `https://support.mozilla.org/fr/products/mozilla-account/accounts` | accept | Brand, do not translate. |
| `mozilla.account` | Mozilla account | compte Mozilla | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `compte Mozilla`: `https://support.mozilla.org/fr/products/mozilla-account/accounts` | accept | Replaced malformed `compte Mozillas` strings with `Comptes Mozilla`. |
| `mozilla.firefox_home` | Firefox Home | page d’accueil de Firefox | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `page d’accueil de Firefox`: `https://support.mozilla.org/fr/kb/comment-definir-page-accueil` | accept | Keep lowercase in sentence-style UI copy. |
| `mozilla.home_page` | Home page | page d’accueil | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `page d’accueil`: `https://support.mozilla.org/fr/kb/comment-definir-page-accueil` | accept | Generic home page term. |
| `mozilla.address_bar` | Address bar | barre d’adresse | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO DoH and search articles use `barre d’adresse`: `https://support.mozilla.org/fr/kb/dns-over-https` | accept | Use for urlbar/search surface. |
| `mozilla.search_suggestions` | Search suggestions | suggestions de recherche | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `suggestions de recherche`: `https://support.mozilla.org/fr/kb/suggestions-recherche-firefox` | accept | Updated several on/off labels for French agreement. |
| `mozilla.private_browsing` | Private Browsing | navigation privée | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `navigation privée`: `https://support.mozilla.org/fr/kb/navigation-privee-naviguer-avec-firefox-sans-enregistrer-historique` | change | Replaced visible English `Private browsing` remnants in audited values. |
| `mozilla.cookies` | Cookies | cookies | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO privacy articles use `cookies`: `https://support.mozilla.org/fr/kb/navigation-privee-naviguer-avec-firefox-sans-enregistrer-historique` | accept | Keep as visible browser term. |
| `mozilla.dns_over_https` | DNS over HTTPS | DNS via HTTPS | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `DNS via HTTPS`: `https://support.mozilla.org/fr/kb/dns-over-https` | change | Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `DNS via HTTPS`. |
| `mozilla.secure_dns` | Secure DNS | DNS sécurisé | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO DoH article uses `DNS sécurisé`: `https://support.mozilla.org/fr/kb/dns-over-https` | accept | Use as explanatory summary, not as replacement for the feature name. |
| `mozilla.site_permissions` | Site permissions | permissions des sites | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO extension and site-control articles use site permission wording: `https://support.mozilla.org/fr/topics/add-ons-extensions-and-themes/firefox` | accept | Keep for site permission categories. |
| `mozilla.addons` | Add-ons | modules complémentaires | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `modules complémentaires`: `https://support.mozilla.org/fr/kb/trouver-installer-modules-firefox` | accept | Umbrella term. |
| `mozilla.extensions` | Extensions | extensions | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO distinguishes `extensions`: `https://support.mozilla.org/fr/kb/trouver-installer-modules-firefox` | accept | Use when specifically describing extension policy/settings. |
| `mozilla.website_translations` | Website translations | traductions des sites web | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `traductions des sites web`: `https://support.mozilla.org/fr/kb/traduction-sites-web` | accept | Keep as feature label. |
| `mozilla.visual_search` | Visual search | recherche visuelle | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Natural French term; revisit during AI-specific QA if Mozilla publishes localized wording. |
| `mozilla.ai_smart_features` | AI & smart features | IA et fonctionnalités intelligentes | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Use `IA` for visible French UI headings. |
| `mozilla.built_in_vpn` | Built-in VPN | VPN intégré | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | SUMO uses `VPN intégré`: `https://support.mozilla.org/fr/kb/vpn-integre` | accept | Keep `VPN` unchanged. |
| `mozilla.ip_protection` | IP protection | protection IP | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | Built-in VPN articles describe masking the IP address: `https://support.mozilla.org/fr/kb/masquage-adresse-ip` | accept | Keep policy key technical where it appears; use `protection IP` only in prose. |
| `policy.managed_preferences` | Managed preferences | préférences gérées | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | Firefox settings articles use preferences/settings wording in French contexts. | accept | Current catalog term for managed Firefox preferences. |
| `policy.firefox_release` | Firefox Release | Firefox Release | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | BPM schema/channel source uses Release as a channel identifier. | accept | Keep `Release` unchanged as a channel label. |
| `policy.firefox_esr` | Firefox ESR | Firefox ESR | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | BPM schema/channel source uses ESR as a channel identifier. | accept | Keep `ESR` unchanged. |
| `policy.outside_guided` | Outside Guided editor | Hors éditeur guidé | Pontoon source priority checked through French team page: `https://pontoon.mozilla.org/fr/` | No SUMO equivalent; this is a BPM UI review/filter term. | accept | Product-specific UI term. |

## Catalog Changes

- Replaced malformed `compte Mozillas` strings with `Comptes Mozilla`.
- Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `DNS via HTTPS`.
- Replaced visible `Private browsing` remnants with `navigation privée` / `mode de navigation privée`.
- Cleaned several French term-adjacent labels for search suggestions, account sign-in, and AI/smart
  feature headings while preserving placeholders and technical identifiers.

## Remaining Follow-Up

The French catalog still contains first-pass prose that needs a broader language copy-edit and
layout-density review. That is outside the terminology-only scope of `GLOC-303` and should be
handled by later locale QA or the `GLOC-502` overflow pass.
