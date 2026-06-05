# Simplified Chinese Mozilla Terminology Audit

Date: `2026-05-29`

Backlog item: `GLOC-302`

Catalog: `app/i18n/zh-CN.json`

Glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

## Scope

This audit verifies the required Simplified Chinese Firefox/Mozilla terminology set from
`docs/mozilla_terminology_verification_workflow_2026-05-29.md`.

The audit is terminology-focused. It does not claim that every Simplified Chinese sentence in the
first-pass runtime catalog has been fully copy-edited.

## Evidence Log

| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |
|---|---|---|---|---|---|---|
| `mozilla.firefox` | Firefox | Firefox | Simplified Chinese Firefox project context: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN Firefox articles keep `Firefox`: `https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security` | accept | Brand, do not translate. |
| `mozilla.mozilla` | Mozilla | Mozilla | Simplified Chinese Firefox project context: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN account/privacy pages keep `Mozilla`: `https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security` | accept | Brand, do not translate. |
| `mozilla.account` | Mozilla account | Mozilla 账号 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN uses `Mozilla 账号`: `https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security` | change | Replaced visible `Mozilla 账户` strings with `Mozilla 账号`. |
| `mozilla.firefox_home` | Firefox Home | Firefox 主页 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN uses `Firefox 主页`: `https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security` | accept | Keep product name unchanged. |
| `mozilla.home_page` | Home page | 主页 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN homepage/add-on articles use `主页`: `https://support.mozilla.org/zh-CN/kb/%E4%B8%80%E4%B8%AA%E6%89%A9%E5%B1%95%E6%9B%B4%E6%94%B9%E4%BA%86%E6%88%91%E7%9A%84%E6%96%B0%E6%A0%87%E7%AD%BE%E9%A1%B5%E6%88%96%E4%B8%BB%E9%A1%B5` | accept | Generic home page term. |
| `mozilla.address_bar` | Address bar | 地址栏 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN DoH and settings articles use `地址栏`: `https://support.mozilla.org/zh-CN/kb/firefox-dns-over-https` | accept | Use for urlbar/search surface. |
| `mozilla.search_suggestions` | Search suggestions | 搜索建议 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN search/settings pages use `搜索建议` in Firefox UI contexts. | accept | Updated several on/off labels to avoid mixed English. |
| `mozilla.private_browsing` | Private Browsing | 隐私浏览 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN privacy topic and add-on pages use `隐私浏览`: `https://support.mozilla.org/zh-CN/products/firefox/privacy-and-security` | accept | Use as the feature label. |
| `mozilla.cookies` | Cookies | Cookie | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN privacy pages use `Cookie`: `https://support.mozilla.org/zh-CN/kb/firefox-privacy-and-security-features` | accept | Keep as visible browser term. |
| `mozilla.dns_over_https` | DNS over HTTPS | 基于 HTTPS 的 DNS | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN article title uses `基于 HTTPS 的 DNS`: `https://support.mozilla.org/zh-CN/kb/firefox-dns-over-https` | change | Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `基于 HTTPS 的 DNS`. |
| `mozilla.secure_dns` | Secure DNS | 安全 DNS | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN DoH protection article uses `安全 DNS`: `https://support.mozilla.org/zh-CN/kb/dns-over-https` | accept | Use as explanatory summary, not as replacement for the feature name. |
| `mozilla.site_permissions` | Site permissions | 网站权限 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN product/support pages use website permission wording in privacy contexts. | accept | Keep for site permission categories. |
| `mozilla.addons` | Add-ons | 附加组件 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN uses `附加组件`: `https://support.mozilla.org/zh-CN/kb/%E5%8D%B8%E8%BD%BD%E9%99%84%E5%8A%A0%E7%BB%84%E4%BB%B6` | accept | Umbrella term. |
| `mozilla.extensions` | Extensions | 扩展 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN distinguishes `扩展`: `https://support.mozilla.org/zh-CN/kb/%E5%8D%B8%E8%BD%BD%E9%99%84%E5%8A%A0%E7%BB%84%E4%BB%B6` | accept | Use when specifically describing extension policy/settings. |
| `mozilla.website_translations` | Website translations | 网站翻译 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN translation article uses `网站翻译`: `https://support.mozilla.org/zh-CN/kb/website-translation` | accept | Keep concise feature label. |
| `mozilla.visual_search` | Visual search | 视觉搜索 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Natural Chinese term; revisit during AI-specific QA if Mozilla publishes localized wording. |
| `mozilla.ai_smart_features` | AI & smart features | AI 与智能功能 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | No strong localized SUMO evidence found in Firefox desktop support pages. | accept | Keep `AI` unchanged as a common technical abbreviation. |
| `mozilla.built_in_vpn` | Built-in VPN | 内置 VPN | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN built-in VPN article uses `内置 VPN`: `https://support.mozilla.org/zh-CN/kb/use-ip-concealment-in-firefox` | accept | Keep `VPN` unchanged. |
| `mozilla.ip_protection` | IP protection | IP 保护 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | SUMO zh-CN built-in VPN article describes hiding the IP address: `https://support.mozilla.org/zh-CN/kb/use-ip-concealment-in-firefox` | accept | Keep policy key technical where it appears; use `IP 保护` only in prose. |
| `policy.managed_preferences` | Managed preferences | 托管首选项 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | No exact SUMO equivalent; Firefox settings pages use settings/preference wording. | accept | Current catalog term for managed Firefox preferences. |
| `policy.firefox_release` | Firefox Release | Firefox Release | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | BPM schema/channel source uses Release as a channel identifier. | accept | Keep `Release` unchanged as a channel label. |
| `policy.firefox_esr` | Firefox ESR | Firefox ESR | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | BPM schema/channel source uses ESR as a channel identifier. | accept | Keep `ESR` unchanged. |
| `policy.outside_guided` | Outside Guided editor | 引导式编辑器之外 | Pontoon source priority checked through zh-CN Firefox project: `https://pontoon.mozilla.org/zh-CN/firefox/` | No SUMO equivalent; this is a BPM UI review/filter term. | accept | Product-specific UI term. |

## Catalog Changes

- Replaced visible `Mozilla 账户` strings with `Mozilla 账号`.
- Replaced visible `DNS over HTTPS` / `DNS-over-HTTPS` remnants with `基于 HTTPS 的 DNS`.
- Cleaned several Chinese term-adjacent labels for search suggestions, private browsing, built-in
  VPN, and account sign-in while preserving placeholders and technical identifiers.

## Remaining Follow-Up

The Simplified Chinese catalog still contains first-pass prose that needs a broader language
copy-edit and layout-density review. That is outside the terminology-only scope of `GLOC-302` and
should be handled by later locale QA or the `GLOC-504` script pass.
