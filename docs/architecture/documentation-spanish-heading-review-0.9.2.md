# BPM 0.9.2: Spanish Documentation Heading Review

Date: 2026-07-19
Status: ready for Spanish-language product-owner sign-off
Backlog item: `BPM092-M10-09`
Policy: [Locale Editorial Style Policy](documentation-locale-editorial-style-0.9.2.md)

## Scope and method

The review covers Spanish DITA titles and immediately related captions or
instructions where the same literal construction appeared. It applies the
Spanish convention: task titles use the infinitive, concept headings use concise
noun phrases, and procedures consistently use the formal imperative. It checks
sentence case, punctuation, accent marks, and exact BPM UI names against the
interface-name authority.

The review uses the Spanish convention in the locale editorial policy and the
[RAE/ASALE orthography guidance](https://www.rae.es/ortograf%C3%ADa-b%C3%A1sica/uso-de-las-may%C3%BAsculas/la-may%C3%BAscula-condicionada-por-la-puntuación).
The exact BPM UI terms come from
[`interface-name-authority-0.9.1.json`](../../documentation/config/interface-name-authority-0.9.1.json).

## Corrected findings

| Topic or element | Before | After | Rationale |
| --- | --- | --- | --- |
| `admin-concept-api-limitations` / `admin-concept-integration-audience` | repeated or singular English-shaped noun stacks | `Limitaciones actuales de la API y de seguridad` / `Audiencia de integración y límites de la API` | Uses concise Spanish concept phrases. |
| `admin-task-gate-control-product-startup` | `Inicio del producto de control de puerta…` | `Iniciar el producto de control tras comprobar la integridad…` | Replaces the literal `gate` noun stack with an infinitive task title. |
| `admin-task-record-devops-operational-boundaries` / `admin-task-record-ha-production-deferred-boundaries` | `Registro…` noun stacks | `Registrar…` titles | Restores the infinitive task convention. |
| `admin-task-refresh-source-revision-dependencies` | title with terminal full stop | `Actualizar la revisión del código fuente y las dependencias` | Removes sentence punctuation and clarifies the source relation. |
| `admin-task-review-devops-configuration-sources` / `admin-task-run-control-product-inventory-pull` | missing article / conjugated `Extrae` | `Revisar las fuentes…` / `Extraer y revisar…` | Corrects grammar and the task-title verb form. |
| `admin-task-export-firefox-policies-json` / `admin-task-validate-firefox-policies-json` | `Firefox canónico policies.json` / missing article | `un archivo Firefox policies.json canónico` / `un candidato Firefox policies.json` | Restores Spanish noun order without changing the filename literal. |
| `cis-concept-levels-channels-layers`, `cis-concept-orientation`, and `cis-concept-presets-layers-merge` | verb or question-like concept titles | noun phrases | Uses the Spanish convention for concepts. |
| `fx-concept-bpm-firefox-boundary`, `fx-concept-policy-selection`, and `fx-concept-starter-presets` | translated question or verb forms | `Límite…` / `Selección…` | Uses concise noun phrases and restores the missing accent in `Límite`. |
| `fx-concept-release-esr-differences` | `la versión de Firefox y la política ESR` | `Firefox Release y ESR` | Names the two schema channels directly. |
| `ug-concept-choose-editor-surface` / `ug-concept-documentation-search-boundary` | `Elegir…` / `Navegar y buscar…` | `Elección…` / `Navegación y búsqueda…` | Uses noun phrases for concepts. |
| `ug-concept-policies-and-managed-preferences` / `ug-concept-when-to-use-json-editor` | English-style capitalization and question form | `Políticas y preferencias gestionadas` / `Uso del «Editor JSON»` | Restores sentence case and preserves the UI name. |
| `ug-reference-all-settings-review-states` | `Todos los ajustes estados de revisión` | `Estados de revisión en «Todos los ajustes»` | Restores Spanish word order and preserves the exact UI label. |
| `ug-task-choose-profile-identity-schema` | `Establecer Identidad…` | `Establecer la identidad del perfil…` | Restores required articles. |
| `ug-task-filter-all-settings` / `ug-task-search-all-settings` | unquoted UI-name noun stacks | `Filtrar la lista «Todos los ajustes»` / `Buscar en «Todos los ajustes»` | Keeps the exact UI label in natural Spanish grammar. |
| `ug-task-review-attention-items` | `Revisar Todos los ajustes elementos…` | `Revisar los elementos que requieren atención en «Todos los ajustes»` | Replaces the literal noun stack with natural help wording. |
| `ug-task-search-guided-settings` | `Búsqueda de configuraciones guiadas` | `Buscar ajustes en el «Editor guiado»` | Uses the infinitive task form and the exact UI label. |
| `ug-task-use-all-settings` / caption | unquoted title and `Todos los ajustes Revisión` | `Usar «Todos los ajustes»` / `Modo «Revisión» en «Todos los ajustes»` | Makes the mode/interface relationship explicit. |
| `ug-task-use-guided-editor` | reader-addressed title and broken ampersand list | `Navegar por los seis pasos del «Editor guiado»` and a complete summary | Uses infinitive grammar and coherent Spanish prose. |
| `ug-task-use-json-editor` | unquoted UI title | `Usar el «Editor JSON»` | Keeps the exact UI label in Spanish typography. |

## Nearby instruction corrections

- The guided-editor overview now describes the six steps in a complete Spanish
  sentence rather than a literal sequence joined by ampersands.
- The filter and review descriptions distinguish state filters from the
  `«Revisión»` mode and retain the `«Todos los ajustes»` UI label.
- Captions for all-settings and guided-editor views now identify the mode and
  interface in natural Spanish order.

Representative normalized headings are `Elección de la interfaz de BPM adecuada`,
`Estados de revisión en «Todos los ajustes»`, and
`Navegar por los seis pasos del «Editor guiado»`.

## Exceptions and sign-off

Accepted exceptions: none. Spanish task titles use infinitives; formal
imperatives remain in procedure steps, consistently within each topic. Concept
and reference titles use concise noun phrases.

Release-gate sign-off: accepted — Valery Ledovskoy, 2026-07-22.

| Review responsibility | Evidence | State |
| --- | --- | --- |
| Automated source scan | No Spanish title contains the recorded malformed word stacks or a terminal full stop. | complete |
| Contract and metadata validation | Heading-style, terminology, interface-name, and locale-parity contracts. | complete |
| Spanish-language product-owner review | Read the rendered Spanish titles in the installed documentation and accept or amend the wording. | pending sign-off |

Any accepted exception must record the topic ID, visible text, linguistic
rationale, and approving Spanish-language reviewer.
