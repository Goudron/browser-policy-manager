# Spanish Mozilla Terminology Audit

Date: `2026-05-30`

Backlog item: `GLOC-304`

Catalog: `app/i18n/es-ES.json`

Glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

## Scope

This audit verifies the required Spanish Firefox/Mozilla terminology set from
`docs/mozilla_terminology_verification_workflow_2026-05-29.md`.

The audit is terminology-focused. It does not claim that every Spanish sentence in the first-pass
runtime catalog has been fully copy-edited.

## Evidence Log

| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |
|---|---|---|---|---|---|---|
| `mozilla.firefox` | Firefox | Firefox | Spanish Firefox project context: `https://pontoon.mozilla.org/es-ES/firefox/` | Spanish SUMO Firefox articles keep `Firefox`: `https://support.mozilla.org/es/products/firefox` | accept | Brand, do not translate. |
| `mozilla.mozilla` | Mozilla | Mozilla | Spanish Firefox project context: `https://pontoon.mozilla.org/es-ES/firefox/` | Spanish SUMO account and VPN articles keep `Mozilla`: `https://support.mozilla.org/es/products/mozilla-account/accounts` | accept | Brand, do not translate. |
| `mozilla.account` | Mozilla account | Mozilla account | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | Spanish SUMO currently keeps the product term `Mozilla account`: `https://support.mozilla.org/es/products/firefox/accounts` | change | Replaced malformed `cuenta Mozillas` strings and key account labels with `Mozilla account` / `Mozilla accounts`. |
| `mozilla.firefox_home` | Firefox Home | página de inicio de Firefox | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `página de inicio de Firefox`: `https://support.mozilla.org/es/kb/como-configurar-la-pagina-de-inicio` | accept | Use for Firefox home/start surface. |
| `mozilla.home_page` | Home page | página de inicio | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `página de inicio`: `https://support.mozilla.org/es/kb/como-configurar-la-pagina-de-inicio` | accept | Generic home page term. |
| `mozilla.address_bar` | Address bar | barra de direcciones | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `barra de direcciones`: `https://support.mozilla.org/es/kb/barra-de-busqueda-firefox` | accept | Use for urlbar/search surface. |
| `mozilla.search_suggestions` | Search suggestions | sugerencias de búsqueda | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `sugerencias de búsqueda`: `https://support.mozilla.org/en-US/kb/search-suggestions-firefox?lang=es` | accept | Updated several on/off labels for Spanish agreement. |
| `mozilla.private_browsing` | Private Browsing | navegación privada | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `Navegación privada`: `https://support.mozilla.org/es/kb/navegacion-privada-Firefox-no-guardar-historial-navegacion` | change | Replaced visible English `Private browsing` remnants in audited values. |
| `mozilla.cookies` | Cookies | cookies | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO privacy pages use `cookies`: `https://support.mozilla.org/es/products/firefox/privacy-and-security` | accept | Keep as visible browser term. |
| `mozilla.dns_over_https` | DNS over HTTPS | DNS sobre HTTPS | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `DNS sobre HTTPS`: `https://support.mozilla.org/en-US/kb/firefox-dns-over-https?lang=es` | change | Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `DNS sobre HTTPS`. |
| `mozilla.secure_dns` | Secure DNS | DNS seguro | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO DoH article uses `DNS seguro`: `https://support.mozilla.org/en-US/kb/dns-over-https?lang=es` | accept | Use as explanatory summary, not as replacement for the feature name. |
| `mozilla.site_permissions` | Site permissions | permisos del sitio | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `Panel de permisos del sitio`: `https://support.mozilla.org/es/kb/panel-permisos-sitio` | accept | Keep for site permission categories. |
| `mozilla.addons` | Add-ons | complementos | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `complementos`: `https://support.mozilla.org/es/kb/encontrar-e-instalar-complementos-para-agregar-car` | accept | Umbrella term. |
| `mozilla.extensions` | Extensions | extensiones | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO distinguishes `extensiones`: `https://support.mozilla.org/es/kb/firma-de-complementos-en-firefox` | accept | Use when specifically describing extension policy/settings. |
| `mozilla.website_translations` | Website translations | traducciones de sitios web | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `traducciones de sitios web`: `https://support.mozilla.org/es/kb/traduccion-pagina-web` | accept | Keep as feature label. |
| `mozilla.visual_search` | Visual search | búsqueda visual | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Natural Spanish term; revisit during AI-specific QA if Mozilla publishes localized wording. |
| `mozilla.ai_smart_features` | AI & smart features | IA y funciones inteligentes | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Use `IA` for visible Spanish UI headings. |
| `mozilla.built_in_vpn` | Built-in VPN | VPN integrada | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | SUMO uses `VPN integrada`: `https://support.mozilla.org/es/kb/usar-la-vpn-de-firefox-en-firefox` | accept | Keep `VPN` unchanged. |
| `mozilla.ip_protection` | IP protection | protección IP | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | Built-in VPN article describes masking the IP address and policy `IPProtectionAvailable`: `https://support.mozilla.org/es/kb/usar-la-vpn-de-firefox-en-firefox` | accept | Keep policy key technical where it appears; use `protección IP` only in prose. |
| `policy.managed_preferences` | Managed preferences | preferencias gestionadas | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | Firefox settings articles use settings/preference wording in Spanish contexts. | accept | Current catalog term for managed Firefox preferences. |
| `policy.firefox_release` | Firefox Release | Firefox Release | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | BPM schema/channel source uses Release as a channel identifier. | accept | Keep `Release` unchanged as a channel label. |
| `policy.firefox_esr` | Firefox ESR | Firefox ESR | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | BPM schema/channel source uses ESR as a channel identifier. | accept | Keep `ESR` unchanged. |
| `policy.outside_guided` | Outside Guided editor | Fuera del editor guiado | Pontoon source priority checked through Spanish Firefox project: `https://pontoon.mozilla.org/es-ES/firefox/` | No SUMO equivalent; this is a BPM UI review/filter term. | accept | Product-specific UI term. |

## Catalog Changes

- Replaced malformed `cuenta Mozillas` strings and key account labels with `Mozilla account` /
  `Mozilla accounts`.
- Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `DNS sobre HTTPS`.
- Replaced visible `Private browsing` remnants with `navegación privada` /
  `modo de navegación privada`.
- Cleaned several Spanish term-adjacent labels for search suggestions, account sign-in, and AI/smart
  feature headings while preserving placeholders and technical identifiers.

## Remaining Follow-Up

The Spanish catalog still contains first-pass prose that needs a broader language copy-edit and
layout-density review. That is outside the terminology-only scope of `GLOC-304` and should be
handled by later locale QA or the `GLOC-503` overflow pass.
