# BPM 0.9.2: French Documentation Heading Review

Date: 2026-07-19
Status: ready for French-language product-owner sign-off
Backlog item: `BPM092-M10-08`
Policy: [Locale Editorial Style Policy](documentation-locale-editorial-style-0.9.2.md)

## Scope and method

The review covers French DITA titles and the immediately related captions or
instructions where the same literal construction appeared. It applies the French
convention: task titles use the infinitive, concept headings use a concise noun
phrase, and body steps may use the second-person plural imperative. It also
checks sentence case, punctuation, apostrophes, and exact BPM UI names against
the interface-name authority.

The review uses the French convention in the locale editorial policy and the
[Académie française language guidance](https://www.academie-francaise.fr/questions-de-langue).
The exact BPM UI terms come from
[`interface-name-authority-0.9.1.json`](../../documentation/config/interface-name-authority-0.9.1.json).

## Corrected findings

| Topic or element | Before | After | Rationale |
| --- | --- | --- | --- |
| `admin-task-gate-control-product-startup` | `Démarrage du produit de contrôle de porte…` | `Démarrer le produit de contrôle après vérification…` | Replaces the literal noun stack with a task infinitive and names the health/readiness gate naturally. |
| `admin-task-record-ha-production-deferred-boundaries` | `Enregistrement HA et limites…` | `Enregistrer les limites HA et de production différées` | Restores the infinitive task form. |
| `admin-task-prepare-source-update-evidence` | `…mettre à jour à partir de la source` | `…une mise à jour depuis les sources` | Uses an idiomatic noun phrase after the infinitive. |
| `admin-task-export-firefox-policies-json` / `admin-task-validate-firefox-policies-json` | `Firefox canonique policies.json` / `le candidat Firefox policies.json` | `un fichier Firefox policies.json canonique` / `un fichier Firefox policies.json candidat` | Restores French noun order without altering the filename literal. |
| `cis-concept-levels-channels-layers` / `cis-concept-presets-layers-merge` | reader-addressed question forms | `Niveaux CIS, canaux et couches générées` / `Fusion des préréglages…` | Uses noun phrases for concepts. |
| `fx-concept-bpm-firefox-boundary` / `fx-concept-policy-selection` / `fx-concept-starter-presets` | question or reader-addressed forms | `Limite entre…` / `Choix…` | Uses compact concept headings rather than translated English question structure. |
| `ug-concept-choose-editor-surface` | `Choisir l’interface BPM adaptée` | `Choix de l’interface BPM adaptée` | Uses a noun phrase for a concept heading. |
| `ug-concept-documentation-search-boundary` | `Parcourir et rechercher…` | `Navigation et recherche…` | Uses a concept noun phrase. |
| `ug-concept-policies-and-managed-preferences` | `Règles et Préférences gérées` | `Stratégies et préférences gérées` | Uses the established documentation term and normal French sentence case. |
| `ug-concept-when-to-use-json-editor` | `Quand utiliser Éditeur JSON` | `Cas d’utilisation de l’« Éditeur JSON »` | Removes the English-shaped question and retains the exact UI label. |
| `ug-reference-all-settings-review-states` | `Tous les paramètres états d’examen` | `États de revue dans « Tous les paramètres »` | Restores French word order and preserves the UI name. |
| `ug-task-choose-profile-identity-schema` | `Définir le Identité…` | `Définir l’identité du profil…` | Corrects the article and agreement. |
| `ug-task-edit-raw-policies-json` / `ug-task-export-policies-json` | `stratégies brutes JSON` / `en Firefox policies.json` | `stratégies JSON brutes` / `au format Firefox policies.json` | Uses natural French technical noun order. |
| `ug-task-filter-all-settings` / `ug-task-search-all-settings` | unquoted `Tous les paramètres` noun stacks | `Filtrer la liste « Tous les paramètres »` / `Rechercher dans « Tous les paramètres »` | Keeps the exact UI label without borrowing English order. |
| `ug-task-review-attention-items` | `Examiner Tous les paramètres éléments d’attention` | `Examiner les éléments à traiter dans « Tous les paramètres »` | Uses natural French help vocabulary and grammar. |
| `ug-task-search-guided-settings` | `Paramètres guidés de recherche` | `Rechercher des paramètres dans l’« Éditeur guidé »` | Replaces a malformed noun stack with a task infinitive and exact UI label. |
| `ug-task-use-all-settings` / caption | unquoted title and `Tous les paramètres Revue` | `Utiliser « Tous les paramètres »` / `Mode « Revue » dans « Tous les paramètres »` | Preserves the French UI labels and makes the relation explicit. |
| `ug-task-use-guided-editor` | `Parcourez les six étapes Éditeur guidé` and broken short description | `Parcourir les six étapes de l’« Éditeur guidé »` and a complete summary | Replaces reader-addressed title and literal ampersand list with native French prose. |
| `ug-task-use-json-editor` | unquoted UI title | `Utiliser l’« Éditeur JSON »` | Keeps the exact UI label in French typography. |

## Nearby instruction corrections

- The guided-editor overview now explains the six steps in one coherent French
  sentence rather than a copied sequence joined by literal ampersands.
- The filter and review descriptions distinguish a filter state from the
  `« Revue »` mode and use the established `« Tous les paramètres »` label.
- Captions for the all-settings and guided-editor views now state the UI mode
  and interface in natural French order.

## Exceptions and sign-off

Accepted exceptions: none. French task titles use infinitives; direct
second-person plural imperatives remain in procedural steps where the user must
perform an action. Concept and reference titles use concise noun phrases.

| Review responsibility | Evidence | State |
| --- | --- | --- |
| Automated source scan | No French title contains the recorded malformed word stacks or a terminal full stop. | complete |
| Contract and metadata validation | Heading-style, terminology, interface-name, and locale-parity contracts. | complete |
| French-language product-owner review | Read the rendered French titles in the installed documentation and accept or amend the wording. | pending sign-off |

Any accepted exception must record the topic ID, visible text, linguistic
rationale, and approving French-language reviewer.

Release-gate sign-off: accepted — Valery Ledovskoy, 2026-07-22.
