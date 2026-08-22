# BPM 0.9.6 M10-03 locale terminology audit

Date: 2026-08-21

Backlog item: BPM096-M10-03

Status: localized-reviewed for the delivered preparation, eight-step Guided,
AMO, CIS attribution, and public preparation-API reader scope. Search aliases,
help targets, maps, screenshots, and generated documentation remain owned by
BPM096-M10-04 and later tasks.

## Evidence and decisions

The English DITA topics updated by M10-02 are the source of workflow meaning.
The native locale peers retain the same topic IDs, links, API paths, policy
identifiers, JSON keys, schema identifiers, CIS, AMO, GUID, URL, XPI, and
policies.json. These are identifiers or product names, not prose to translate.

| Locale | Firefox UI and support evidence | Decision |
| --- | --- | --- |
| ru | [Pontoon Firefox](https://pontoon.mozilla.org/ru/firefox/); [SUMO add-ons](https://support.mozilla.org/ru/kb/find-and-install-add-ons-add-features-to-firefox) | Use Russian native headings and the BPM catalog labels for Guided editor, Library, extensions, certificates, and trust. |
| de | [Pontoon Firefox](https://pontoon.mozilla.org/de/firefox/); [SUMO Add-ons](https://support.mozilla.org/de/kb/addons-finden-und-installieren-und-firefox-anpassen) | Use Erweiterungen and Add-ons in the same distinction as Firefox; headings use German native conventions rather than English word order. |
| zh-CN | [Pontoon Firefox](https://pontoon.mozilla.org/zh-CN/firefox/); [SUMO add-ons](https://support.mozilla.org/zh-CN/kb/find-and-install-add-ons-add-features-to-firefox) | Use simplified-Chinese headings and full native prose; retain technical identifiers exactly. |
| fr | [Pontoon Firefox](https://pontoon.mozilla.org/fr/firefox/); [SUMO modules complémentaires](https://support.mozilla.org/fr/kb/trouver-installer-modules-firefox) | Use Extensions for the product control and modules complémentaires in support prose, following SUMO’s distinction. |
| es-ES | [Pontoon Firefox](https://pontoon.mozilla.org/es-ES/firefox/); [SUMO add-ons](https://support.mozilla.org/es/topics/add-ons-extensions-and-themes/firefox) | Use Extensiones for the product control and natural Spanish task headings; retain AMO/API values. |

The public [Pontoon Firefox project](https://pontoon.mozilla.org/projects/firefox/)
was checked for the upstream Firefox terminology authority. SUMO wording is
used for explanatory prose, while the exact BPM runtime catalog remains the
authority for interface labels. No screenshot or search source is used as a
cross-locale fallback.

## Scope checklist

- ru, de, zh-CN, fr, and es-ES each describe atomic create and duplicate
  preparation, source nonmutation, conversion blocker recovery, and eight
  Guided steps.
- Each locale documents optional AMO name lookup, the query/locale-only
  disclosure, no XPI fetch, and manual GUID plus validated install-URL
  recovery.
- Each locale distinguishes normal value attribution from the separate
  certificate/trust path ledger and does not make a benchmark-compliance claim
  for manual, imported, converted, raw, unavailable, or blocked states.
- Each locale records the narrow public preparation API and value-free
  ProfilePreparationErrorEnvelope recovery boundary.

## Verification

tests/contract/docs/general/test_bpm096_localized_profile_docs.py parses all
135 affected DITA peers and checks the five locale workflow, AMO, CIS, API,
identifier, delivery record, and no-draft conditions. Broader editorial,
search, screenshot, site, and PDF checks remain explicitly sequenced to
M10-04 through M10-09.
