# French Locale Catalog Notes

Backlog item: `GLOC-203`
Catalog: `app/i18n/fr.json`
Source catalog: `app/i18n/en.json`

## Scope

`fr` is now a complete runtime catalog with the same key order as the English source catalog.
The catalog preserves placeholders, URLs, policy identifiers, preference identifiers, JSON terms,
and product names that should remain technical literals.

This is the first complete French pass for runtime availability. The `GLOC-303` audit has now
completed the focused Pontoon/SUMO terminology review in
`docs/archive/2026-q2/fr_mozilla_terminology_audit_2026-05-29.md`.

## Initial Mozilla Term Alignment

| English source term | French catalog term | Initial source/rationale |
|---|---|---|
| Mozilla account | compte Mozilla | SUMO fr account pages use `compte Mozilla` and `comptes Mozilla`. |
| Firefox Home | page d’accueil de Firefox | SUMO fr account/settings pages use page d’accueil wording for the browser home surface. |
| Private Browsing | navigation privée | SUMO fr has a dedicated article titled with `Navigation privée`. |
| DNS over HTTPS | DNS via HTTPS | SUMO fr uses `DNS via HTTPS`, with `DNS over HTTPS` as the English expansion. |
| Website translations | traductions des sites web | SUMO fr uses `traductions des sites web` when describing Firefox translation prompts. |
| Add-ons | modules complémentaires | SUMO fr settings pages use `modules complémentaires`; use `extensions` when specifically naming extensions. |
| Cookies | cookies | SUMO fr keeps the browser term as `cookies`. |
| Built-in VPN | VPN intégré | SUMO fr uses `VPN intégré` for the Firefox built-in VPN feature. |

## Validation

- `fr.json` is valid JSON.
- It contains the same 2,615 keys as `en.json`, in the same order after the `GLOC-404`
  All settings search/filter audit additions.
- Placeholder parity with `en.json` has zero mismatches.
- Literal examples such as `https://www.example.org/search?q={searchTerms}` and `<local>` are
  preserved exactly.
- `fr` is promoted to `has_catalog=True` in the locale matrix and served from `/i18n/fr.json`.

## Follow-Up For `GLOC-303`

- Completed in `docs/archive/2026-q2/fr_mozilla_terminology_audit_2026-05-29.md`.

## Remaining Follow-Up

- Replace remaining awkward first-pass phrases with natural French during a broader locale QA pass.
- Review dense UI labels for line length before the later viewport overflow pass.
