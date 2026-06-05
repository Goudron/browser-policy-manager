# Simplified Chinese Locale Catalog Notes

Backlog item: `GLOC-202`
Catalog: `app/i18n/zh-CN.json`
Source catalog: `app/i18n/en.json`

## Scope

`zh-CN` is now a complete runtime catalog with the same key order as the English source catalog.
The catalog preserves placeholders, URLs, policy identifiers, preference identifiers, JSON terms,
and product names that should remain technical literals.

This was the first complete Simplified Chinese pass for runtime availability. `GLOC-302` completed
the focused Mozilla/SUMO terminology audit in
`docs/archive/2026-q2/zh_cn_mozilla_terminology_audit_2026-05-29.md`. The remaining follow-up is broader prose
copy-editing and UI density review outside the terminology-only scope of that task.

## Initial Mozilla Term Alignment

| English source term | Simplified Chinese catalog term | Initial source/rationale |
|---|---|---|
| Mozilla account | Mozilla 账号 | SUMO zh-CN account pages use `Mozilla 账号` in article titles and summaries. |
| Firefox Home | Firefox 主页 | SUMO zh-CN account/settings pages use `Firefox 主页` for the browser home surface. |
| Private Browsing | 隐私浏览 | SUMO zh-CN has a dedicated `隐私浏览` article. |
| DNS over HTTPS | 基于 HTTPS 的 DNS / DNS over HTTPS | SUMO zh-CN uses `基于 HTTPS 的 DNS（DoH）`; keep the English technical form where the UI is naming the policy concept directly. |
| Website translations | 网站翻译 | SUMO zh-CN translation article uses `禁用网站翻译`; headings may also say full-page translation. |
| Add-ons | 附加组件 | SUMO zh-CN settings pages use `附加组件`. |
| Extensions | 扩展 | SUMO zh-CN add-on settings pages distinguish extensions under add-ons. |
| Cookies | Cookie | SUMO zh-CN keeps `Cookie` as the visible term. |
| Built-in VPN | 内置 VPN | Matches the English source intent while preserving the product/technical `VPN` abbreviation. |

## Validation

- `zh-CN.json` is valid JSON.
- It contains the same 2,615 keys as `en.json`, in the same order after the `GLOC-404`
  All settings search/filter audit additions.
- Placeholder parity with `en.json` has zero mismatches.
- Literal examples such as `https://www.example.org/search?q={searchTerms}` and `<local>` are
  preserved exactly.
- `zh-CN` is promoted to `has_catalog=True` in the locale matrix and served from
  `/i18n/zh-CN.json`.

## Follow-Up After `GLOC-302`

- Replace remaining awkward first-pass phrases with natural Simplified Chinese.
- Review short labels in dense controls for line breaking and button width before the UI script pass.
