# English Locale Mozilla Terminology Check

Date: `2026-05-21`

Related backlog item: `GLOC-101`

Scope: lightweight check of high-signal English UI terminology in `app/i18n/en.json` against
current Mozilla/SUMO English surfaces. This is not a full source-copy rewrite; any copy changes
belong in `GLOC-102`.

## Sources Checked

- Mozilla Pontoon Firefox project: `https://pontoon.mozilla.org/projects/firefox/`
- SUMO: Change Firefox options, preferences and settings:
  `https://support.mozilla.org/en-US/kb/firefox-options-preferences-and-settings`
- SUMO: Firefox Translations:
  `https://support.mozilla.org/en-US/kb/website-translation`
- SUMO: Firefox DNS over HTTPS:
  `https://support.mozilla.org/en-US/kb/firefox-dns-over-https`
- SUMO: Configure DNS over HTTPS protection levels in Firefox:
  `https://support.mozilla.org/en-US/kb/dns-over-https`
- SUMO: Site Permission Add-ons:
  `https://support.mozilla.org/en-US/kb/site-permission-add-ons`
- SUMO: Use built-in VPN in Firefox:
  `https://support.mozilla.org/en-US/kb/use-firefox-vpn-on-firefox`

## Result

The English locale is broadly aligned with Mozilla/SUMO terminology for the main Firefox surfaces
used in BPM. No blocking terminology mismatch was found for the source inventory freeze.

| BPM English term | Mozilla/SUMO signal | Status |
|---|---|---|
| `Mozilla account` | SUMO uses `Mozilla account` in Sync and built-in VPN prose; navigation may title the product area as `Mozilla Account`. | OK. Keep lowercase `account` in prose; title case is acceptable for product-area labels. |
| `Firefox Home` | SUMO uses `Firefox Home`, `default Firefox home page`, and `Firefox Home content`. | OK. |
| `Firefox Settings` / `Settings` | SUMO article title and panels use `Firefox Settings`, `Settings`, `General`, `Home`, `Search`, `Privacy and security`, `Sync`, and `AI Controls`. | OK. BPM can use `Firefox Settings areas` when referring to browser panels. |
| `Add-ons`, `add-ons`, `Add-ons Manager` | SUMO uses add-ons broadly and has `Site Permission Add-ons`; Firefox settings prose mentions installing add-ons. | OK. BPM mixes `extensions` and `add-ons` appropriately: extension policy specifics can keep `extension`, user-facing Firefox surface can use `add-on`. |
| `Site permissions` / `site permission add-ons` | SUMO uses `site permissions` and `Site Permission Add-ons`. | OK. |
| `Cookies` / `Cookies and site data` | SUMO uses `Cookies and site data`, `website cookies`, and cookie references in privacy settings. | OK. |
| `Private windows` / `Private Browsing` | SUMO uses `Private Browsing`; BPM often uses `private windows` for policy behavior. | Acceptable. Consider normalizing headings to `Private Browsing` in `GLOC-102` where the UI describes the Firefox feature rather than a policy effect. |
| `Website translation` / `Translations` | SUMO article is titled `Firefox Translations` and has `Disable website translations` / `Translations` settings language. | Acceptable. Consider `Firefox Translations` for feature titles and `website translations` for behavior labels in `GLOC-102`. |
| `DNS over HTTPS` / `DoH` | SUMO uses `DNS over HTTPS (DoH)`, `DoH`, and `secure DNS`. | OK. |
| `Built-in VPN` / `IP protection` | SUMO currently emphasizes `built-in VPN in Firefox`, `Mozilla VPN`, and the enterprise policy name `IPProtectionAvailable`. | Acceptable but watch in `GLOC-102`: visible prose may read closer to SUMO as `built-in VPN`; keep `IP protection` where it maps to policy/schema terminology. |
| `AI Controls` / AI feature labels | SUMO Settings overview includes `AI Controls` and individual AI features such as website translations, alt text, tab group suggestions, link previews, and AI chatbots. | OK. |

## Follow-Up For `GLOC-102`

- Review whether headings currently saying `Website translation` should become `Firefox
  Translations` when they name the Firefox feature rather than a policy behavior.
- Review whether `Built-in VPN and IP protection` should stay as-is for policy/schema clarity or
  shift visible prose toward SUMO's `built-in VPN` wording.
- Review `Private windows` headings and summaries for places where `Private Browsing` would better
  match Firefox user-facing terminology.
