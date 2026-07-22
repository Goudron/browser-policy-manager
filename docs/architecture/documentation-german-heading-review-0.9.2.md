# BPM 0.9.2: German Documentation Heading Review

Date: 2026-07-19
Status: ready for German-language product-owner sign-off
Backlog item: `BPM092-M10-06`
Policy: [Locale Editorial Style Policy](documentation-locale-editorial-style-0.9.2.md)

## Scope and method

The review covers German DITA titles and the immediately related captions or
instructional wording where a heading exposed the same calque. It checks the
German infinitive convention for task titles, sentence capitalization,
punctuation, compounds, and exact UI names from the interface-name authority.
Reader-addressed `Sie` and `Ihnen` are permitted in procedure steps but not in
titles.

The review uses the German convention in the locale editorial policy and the
[Duden capitalization rule](https://www.duden.de/sprachwissen/rechtschreibregeln/Gro%C3%9F-%20und%20Kleinschreibung).
The exact BPM UI terms come from
[`interface-name-authority-0.9.1.json`](../../documentation/config/interface-name-authority-0.9.1.json).

## Corrected findings

| Topic or element | Before | After | Rationale |
| --- | --- | --- | --- |
| `admin-task-assess-single-node-source-readiness` | `Die aktuelle Bereitschaft der Einzelknotenquelle bewerten` | `Die Bereitschaft einer Einzelknoten-Quellbereitstellung bewerten` | Restores a natural German compound and the deployment scope. |
| `admin-task-gate-control-product-startup` | `Start des Torsteuerungsprodukts mit BPM-Gesundheit und -Bereitschaft` | `Start eines Steuerungsprodukts mit BPM-Health- und Readiness-Prüfungen` | Replaces the literal `Torsteuerung` calque with the established integration term. |
| `admin-task-prepare-source-update-evidence` | `Nachweise vor dem Aktualisieren aus den Quellen vorbereiten` | `Nachweise vor einer Quellaktualisierung vorbereiten` | Uses the concise German noun compound. |
| `admin-task-record-devops-operational-boundaries` | `Quelloperationsgrenzen aufzeichnen` | `Betriebsgrenzen einer Quellbereitstellung dokumentieren` | Clarifies the grammatical relation and uses the documentation verb naturally. |
| `admin-task-record-ha-production-deferred-boundaries` | `Datensatz HA und Produktionsverzögerungsgrenzen` | `HA- und Produktionsgrenzen dokumentieren` | Replaces an ungrammatical noun stack with a clear infinitive title. |
| `admin-task-record-integration-failure-audit` | `Wiederherstellung nach Integrationsfehlern und Aufzeichnung von Prüfnachweisen` | `Wiederherstellung nach Integrationsfehlern und Dokumentation von Prüfnachweisen` | Uses the natural noun for recorded evidence. |
| `admin-task-run-control-product-inventory-pull` | `… abrufen und lesen` | `… abrufen und prüfen` | `prüfen` is the natural operation after retrieving BPM profile records. |
| `admin-task-use-reusable-api-examples` | `DevOps API-Beispiele` | `DevOps-API-Beispiele` | Corrects the compound hyphenation. |
| `fx-reference-managed-preference-locking` | `Verwaltete Einstellungssperrreferenz` | `Sperren verwalteter Einstellungen` | Replaces the literal `reference` compound with an idiomatic reference subject. |
| `ug-concept-documentation-search-boundary` | `Produktdokumentation navigieren und durchsuchen` | `Navigation und Suche in der Produktdokumentation` | Uses a noun phrase for a concept title. |
| `ug-concept-policies-and-managed-preferences` | `Richtlinien und Verwaltete Einstellungen` | `Richtlinien und verwaltete Einstellungen` | Applies normal German capitalization to a generic concept, not the UI section label. |
| `ug-concept-when-to-use-json-editor` | `Wann sollte JSON-Editor verwendet werden?` | `Einsatz des JSON-Editors` | Uses a compact concept heading instead of an English-shaped question. |
| `ug-reference-all-settings-review-states` | `Alle Einstellungen Überprüfungsstatus` | `Prüfstatus in „Alle Einstellungen“` | Restores grammar and preserves the exact UI label. |
| `ug-task-edit-raw-policies-json` | `Rohrichtlinien-JSON bearbeiten` | `Rohes Richtlinien-JSON bearbeiten` | Corrects the malformed compound. |
| `ug-task-filter-all-settings` | `Die Liste Alle Einstellungen filtern` | `Die Liste „Alle Einstellungen“ filtern` | Preserves the exact UI name as a quoted label. |
| `ug-task-filter-settings-by-source` | `Einstellungen filtern nach Quelle` | `Einstellungen nach Quelle filtern` | Uses idiomatic German word order. |
| `ug-task-handle-raw-unknown-settings` | `Behandelt rohe und unbekannte Einstellungen` | `Roh- und unbekannte Einstellungen behandeln` | Corrects the accidental third-person form. |
| `ug-task-manage-destructive-actions` | `Zerstörerische Aktionen sicher verwalten` | `Unumkehrbare Aktionen sicher verwalten` | Uses the product-relevant meaning instead of a literal adjective. |
| `ug-task-review-attention-items` | `Aufmerksamkeitselemente in Alle Einstellungen prüfen` | `Elemente mit Handlungsbedarf in „Alle Einstellungen“ prüfen` | Uses native help vocabulary and preserves the UI label. |
| `ug-task-search-all-settings` | `Suche nach Alle Einstellungen` | `„Alle Einstellungen“ durchsuchen` | Uses the task infinitive and exact UI label. |
| `ug-task-search-guided-settings` | `Suchgeführte Einstellungen` | `Einstellungen im Modus „Geführter Editor“ durchsuchen` | Removes a malformed compound and preserves the editor label. |
| `ug-task-use-guided-editor` | `Durch die sechs Schritte des Geführten Editors navigieren` | `Durch die sechs Schritte im Modus „Geführter Editor“ navigieren` | Avoids inflecting the exact UI label. |
| `ug-task-use-guided-editor` figure title | `Geführter Editor Übersicht` | `Überblick über den Modus „Geführter Editor“` | Corrects word order and preserves the editor label. |
| `ug-task-use-guided-fine-tuning` | `Geführte Feinabstimmungs-Steuerelemente verwenden` | `Steuerelemente für die Feinabstimmung im Modus „Geführter Editor“ verwenden` | Uses a natural phrase and the catalogue-owned editor label. |
| `ug-troubleshoot-schema-mismatch` | `Eine Schemainkongruenz beheben` | `Einen Schema-Konflikt beheben` | Replaces an unnatural calque with a common technical help term. |

## Nearby instruction corrections

- `Aufmerksamkeitselemente` is replaced by `Elemente mit Handlungsbedarf` in
  the review result, the All-settings context, and the CIS Level 2 workflow.
- `Rohrichtlinienform` is replaced by `Rohform der Richtlinie` in the browser
  access recovery instruction.
- The All-settings context now distinguishes the full editor, the
  `Verwaltete Einstellungen` section, and the `Prüfung` mode without treating
  them as interchangeable names.

## Exceptions and sign-off

Accepted exceptions: none. German task titles retain infinitive phrases; direct
formal imperatives remain in body steps where an administrator or user performs
an action.

| Review responsibility | Evidence | State |
| --- | --- | --- |
| Automated source scan | No German title contains `Sie`, `Ihnen`, or a terminal full stop. | complete |
| Contract and metadata validation | Heading-style, terminology, interface-name, and locale-parity contracts. | complete |
| German-language product-owner review | Read the rendered German titles in the installed documentation and accept or amend the wording. | pending sign-off |

Any accepted exception must record the topic ID, visible text, linguistic
rationale, and approving German-language reviewer.

Release-gate sign-off: accepted — Valery Ledovskoy, 2026-07-22.
