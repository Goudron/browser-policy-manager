# Spanish Locale Catalog Notes

Backlog item: `GLOC-204`
Catalog: `app/i18n/es-ES.json`
Source catalog: `app/i18n/en.json`

## Scope

`es-ES` is now a complete runtime catalog with the same key order as the English source catalog.
The catalog preserves placeholders, URLs, policy identifiers, preference identifiers, JSON terms,
and product names that should remain technical literals.

This is the first complete Spanish pass for runtime availability. The `GLOC-304` audit has now
completed the focused Pontoon/SUMO terminology review in
`docs/archive/2026-q2/es_es_mozilla_terminology_audit_2026-05-30.md`.

## Initial Mozilla Term Alignment

| English source term | Spanish catalog term | Initial source/rationale |
|---|---|---|
| Mozilla account | Mozilla account | SUMO es currently keeps `Mozilla account` in product/account copy. |
| Firefox Home | página de inicio de Firefox | SUMO es uses `página de inicio de Firefox`. |
| Private Browsing | Navegación privada | SUMO es has a dedicated `Navegación privada` article. |
| DNS over HTTPS | DNS sobre HTTPS | SUMO es uses `DNS sobre HTTPS`. |
| Website translations | traducciones de sitios web | SUMO es translation pages use site/web translation wording for Firefox translation prompts. |
| Add-ons | complementos | SUMO es settings pages group add-ons as `complementos`; use `extensiones` when specifically naming extensions. |
| Cookies | cookies | SUMO es keeps the browser term as `cookies`. |
| Built-in VPN | VPN integrada | SUMO es uses `VPN integrada` for the Firefox built-in VPN feature. |

## Validation

- `es-ES.json` is valid JSON.
- It contains the same 2,615 keys as `en.json`, in the same order after the `GLOC-404`
  All settings search/filter audit additions.
- Placeholder parity with `en.json` has zero mismatches.
- Literal examples such as `https://www.example.org/search?q={searchTerms}` and `<local>` are
  preserved exactly.
- `es-ES` is promoted to `has_catalog=True` in the locale matrix and served from
  `/i18n/es-ES.json`.

## Follow-Up For `GLOC-304`

- Completed in `docs/archive/2026-q2/es_es_mozilla_terminology_audit_2026-05-30.md`.

## Remaining Follow-Up

- Replace remaining awkward first-pass phrases with natural Spanish during a broader locale QA pass.
- Review label length in dense panels before the later viewport overflow pass.
