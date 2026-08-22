# BPM 0.9.6 profile documentation editorial review

Date: 2026-08-21

Backlog item: `BPM096-M10-05`

Status: source editorial review complete. M10-06 owns the release preflight;
site and PDF candidate work remain M10-07 and M10-08.

## Scope and reader ownership

This review uses the executable [profile documentation impact
inventory](profile-documentation-impact-inventory-0.9.6.md) and the source,
locale, help/search, and screenshot evidence from M10-02 through M10-04. It
reviews published source only: English DITA, five authored locale peers, guide
maps, source-owned help/search inputs, and screenshot references. It does not
inspect or edit generated site, search-index, manifest, PDF, package, or
installed-site output.

Every published guide is affected. No guide is untouched, so no unaffected
reason is available or needed before a site or PDF build.

| Guide map | Primary reader and 0.9.6 ownership | Map and topic review decision |
| --- | --- | --- |
| User Guide | Profile author; atomic preparation, eight-step editor, and recovery. | The six locale `user-guide.ditamap` maps retain reachable preparation, Guided, All settings, JSON, and troubleshooting topics. The current source assigns SearchEngines to Step 1 and URLs/sites/navigation to Step 2. |
| Firefox Policy Guide | Firefox policy author; schema shape, AMO boundary, URLs/sites, and certificates/trust. | The six maps retain policy-selection, channel, preset, complex-family, review, and managed-preference topics. The complex-family topic is the one source for the extension, certificate, URL/site, and policy-shape explanation. |
| CIS Settings Guide | CIS baseline reviewer; preparation input, attribution, conflict, and manual review. | The six maps retain orientation, levels/channels, selection, attribution, deviation, and Level 1/2 workflows. A selected baseline and certificate/trust path attribution remain review facts, not compliance claims. |
| Administrator Guide | Administrator, DevOps operator, and API integrator; supported public lifecycle and Firefox interchange boundary. | The six maps retain API conventions, limitations, preparation lifecycle, import/export/validate, and recovery topics within Administrator rather than creating a fifth API guide. |

## Editorial completeness and exclusions

The reviewed User tasks include a purpose, prerequisite, task steps, expected
outcome, recovery, and related tasks for preparation, duplicate conversion,
the three distinct Guided domains, All settings, JSON, name errors, schema
mismatch, and policy validation. The Firefox Policy, CIS, and Administrator
topics supply the corresponding policy-shape, benchmark, manual-review, API,
and operation boundaries without duplicating deployment instructions in the
User Guide.

The English source uses concise sentence-case headings, parallel task titles,
one action per step, and plain expected-result/recovery wording in accordance
with the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/).
The localized prose is reviewed as native content, not as an English grammar
template, following the [Microsoft globalization writing
guidance](https://learn.microsoft.com/en-us/style-guide/global-communications/writing-tips).

The following source defects were removed during this review.

| Disposition | Source scope | Current reader-safe result |
| --- | --- | --- |
| Replaced a Step 2 search claim | `ug-task-configure-home-search-navigation` in all six locales | Step 1 owns `SearchEngines` and suggestions. Step 2 owns `Homepage`, startup, site access/filtering, handlers, and managed bookmarks. |
| Replaced stale Guided numbering | `fx-concept-complex-policy-families` in all six locales | Extensions are Step 6, certificates/trust Step 4, and AI/smart-feature controls Step 7. |
| Removed duplicated transitional wording | Five localized complex-policy topics | The temporary `bpm096-delivered-workflow` appendix and conflicting older paragraphs were replaced by one locale-owned description. |
| Removed draft lifecycle claims | Localized CIS selection and Level 2 topics | A reader opens create/duplicate preparation before saving; a deployment risk pauses reuse of a saved profile and updates the external decision record. |
| Restored locale structural parity | English and localized CIS selection and Level 2 topics | The same current-behavior section now exists in every peer, so a localized source change cannot bypass the DITA structural-shape gate. |
| Replaced BPM UI-label drift | Guided-editor and complex-policy topics in all six locales | Every displayed Guided step label now resolves from the same `app/i18n_src/{locale}/wizard.json` key as the runtime: all eight editor steps in the User Guide and Steps 4, 6, and 7 in the Firefox Policy Guide. |
| Separated historical visual evidence | Screenshot matrix, visual-QA record, and their source contracts | The historical accepted BPM091 review remains exactly 36 rows. M10-04 records 30 newly captured localized source PNGs in the current 66-row matrix; no source capture is misrepresented as rendered site/PDF acceptance. |
| Retained as historical, not product source | 0.9.2 heading-review records | Their retrospective “six steps” examples are not publishable DITA and are superseded for current BPM096 reader content by this review. |

No reviewed product topic exposes CI commands, source-tree mutation, database
edits, credentials, private hosts, AMO operator workflow, certificate contents,
or unshipped assistant behavior. The supported boundary remains explicit:
BPM stores certificate/device references literally, does not fetch XPI files,
and does not claim benchmark, deployment, organization, or Firefox-runtime
compliance.

## Locale, UI, and Mozilla terminology decisions

The exact rendered BPM label is taken from `app/i18n_src/{locale}/wizard.json`
and the corresponding current Guided source. The source-review contract parses
the eight `<uicontrol>` values in each locale's User task and the Step 4, 6,
and 7 values in its Firefox Policy peer against those same catalog keys; prose
may explain a control but does not replace its label. The header's schema,
preset, and CIS baseline are read-only profile facts, not selector labels.
Mozilla terminology is independently checked in Pontoon for Firefox UI
language and in SUMO for explanatory support prose. Product identifiers,
policy IDs, paths, URLs, schema channels, JSON keys, GUID, XPI, AMO,
`policies.json`, and placeholders such as `{searchTerms}` remain literals.

| Locale | UI-heading decision | Firefox UI / support evidence | Decision |
| --- | --- | --- | --- |
| `ru` | Nominal titles: `Настройка URL, сайтов и навигации`; `Сложные семейства политик Firefox`. | [Pontoon](https://pontoon.mozilla.org/ru/firefox/); [SUMO add-ons](https://support.mozilla.org/ru/kb/find-and-install-add-ons-add-features-to-firefox) | Preserve BPM labels such as `Пошаговый редактор`, `Дополнения`, and `Сертификаты и доверие`; use Russian prose around unchanged literals. |
| `de` | Infinitive task title: `URLs, Websites und Navigation konfigurieren`. | [Pontoon](https://pontoon.mozilla.org/de/firefox/); [SUMO Add-ons](https://support.mozilla.org/de/kb/addons-finden-und-installieren-und-firefox-anpassen) | Use `Erweiterungen` for the UI and the established Firefox distinction for surrounding Add-ons prose; no `Sie` in headings. |
| `zh-CN` | Compact title: `配置 URL、站点和导航`. | [Pontoon](https://pontoon.mozilla.org/zh-CN/firefox/); [SUMO add-ons](https://support.mozilla.org/zh-CN/kb/find-and-install-add-ons-add-features-to-firefox) | Use compact simplified-Chinese headings without Chinese word spacing; preserve technical literals. |
| `fr` | Infinitive task title: `Configurer les URL, les sites et la navigation`. | [Pontoon](https://pontoon.mozilla.org/fr/firefox/); [SUMO modules complémentaires](https://support.mozilla.org/fr/kb/trouver-installer-modules-firefox) | Use `Extensions` for the BPM control and `modules complémentaires` only in explanatory support prose. |
| `es-ES` | Infinitive task title: `Configurar URL, sitios y navegación`. | [Pontoon](https://pontoon.mozilla.org/es-ES/firefox/); [SUMO add-ons](https://support.mozilla.org/es/topics/add-ons-extensions-and-themes/firefox) | Use `Extensiones` for the BPM control, natural sentence case, and unchanged AMO/API literals. |

The common upstream reference is the [Firefox Pontoon
project](https://pontoon.mozilla.org/projects/firefox/). The prior
[M10-03 terminology audit](../bpm096_m10_03_locale_terminology_audit_2026-08-21.md)
records the same evidence and its delivery-scope decisions; this review adds
the corrected current-source locations and heading decisions.

The Chinese heading guard no longer rejects `配置文件`: it is the legitimate
current BPM term for a profile and its former blanket prohibition was an M8
false positive. The guard continues to reject `个人资料`, Chinese word spacing,
and terminal Chinese sentence stops; this change does not introduce a fallback
or an independently translated UI label.

## Search and documentation assistant remain separate

M10-04 aliases and contextual help resolve changed actions to canonical topics
or policy identities. They are deterministic search inputs and do not invoke,
train, query, or depend on the documentation assistant. The User Guide keeps
the deterministic-search boundary and the assistant task as separate reachable
topics: ordinary search is local, deterministic, and available independently;
the assistant has its own delivered availability and refusal boundary. Firefox
AI policy controls are product settings and are separate from both facilities.

## Build boundary and follow-up

This is source-review evidence only. The current screenshot matrix records a
complete M10-04 source capture (30 new localized PNGs; 66 matrix rows), but
the later rows have `not-reviewed` rendered visual acceptance. M10-06 must run
and record DITA, links, metadata, locale parity, documentation contracts,
source-bound inventories, and the prescribed fast preflight before a candidate
exists. M10-07 and M10-08 alone own site and PDF build, rendered visual review,
and publication evidence.
