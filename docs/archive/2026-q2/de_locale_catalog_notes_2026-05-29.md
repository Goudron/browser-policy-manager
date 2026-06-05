# German Locale Catalog Notes

Date: `2026-05-29`

Backlog item: `GLOC-201`

Catalog: `app/i18n/de.json`

Source inventory: `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`

## Scope

This pass adds the first complete German runtime catalog. The catalog mirrors the English key order,
preserves all runtime placeholders, and keeps technical identifiers such as `policies.json`, Firefox
policy keys, preference keys, URLs, and literal values unchanged.

## Initial Mozilla Terminology

| English source | German catalog term | Evidence / rationale |
|---|---|---|
| Mozilla account | Mozilla-Konto | Matches German Mozilla privacy/SUMO-style account wording. |
| Firefox Home | Firefox-Startseite | Matches German SUMO settings wording for the default Firefox home page. |
| Private Browsing | Privater Modus | Matches German Firefox.com private browsing feature wording. |
| DNS over HTTPS | DNS über HTTPS | Matches German SUMO DNS over HTTPS article title and wording. |
| Website translations | Website-Übersetzungen | Aligned with German Firefox translation feature wording. |
| Add-ons | Add-ons | Mozilla German surfaces commonly keep the term `Add-ons`. |
| Cookies | Cookies | Mozilla German surfaces commonly keep `Cookies`. |
| Built-in VPN | Integriertes VPN | User-facing wording for the VPN/IP protection area; policy-specific IP wording stays technical where needed. |

## Follow-Up

`GLOC-301` completed the focused Mozilla/SUMO terminology audit in
`docs/archive/2026-q2/de_mozilla_terminology_audit_2026-05-29.md`. The remaining German follow-up is broader prose
copy-editing outside the terminology-only scope of that task.
