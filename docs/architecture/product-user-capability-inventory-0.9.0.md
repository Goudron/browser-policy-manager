# BPM 0.9.0 Product User Capability Inventory

Date: 2026-06-20

Backlog item: `BPM090-M2-01`

## Purpose

This inventory is the coverage source for the case-oriented BPM User Guide. It maps each current
user-visible capability to a stable capability ID and a planned DITA topic ID before authoring
starts. Topic IDs are locale-independent; localized maps and topic files must preserve the mapping.

The inventory is grounded in the current README, web routes, Jinja product surfaces, wizard-step
registry, frontend behavior, and their contract/smoke tests. It does not use the stale pre-0.8.8
`all-settings-current-contracts.md` implementation map as current product evidence.

## Coverage Rules

- `task` topics tell a user how to achieve an outcome.
- `concept` topics explain a product model or decision needed to choose a task.
- `reference` topics define states, fields, or behavior a task depends on.
- `troubleshooting` topics diagnose a visible failure and provide recovery steps.
- One DITA topic may cover several tightly related capability IDs, but no capability may be left
  without a primary topic.
- Policy-by-policy detail belongs to the Firefox Policy Guide, recommendation-by-recommendation
  detail belongs to the CIS Settings Guide, and endpoint-by-endpoint detail belongs to the API
  Integration Guide. The User Guide still covers the user workflows that reach those systems.
- Administrator/distribution tasks remain outside this inventory until BPM distribution formats
  are defined.

## Global Shell And Cross-Surface Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-GLOBAL-001` | Understand the single profile model shared by Library, Guided, All Settings, JSON, and Compare. | `README.md` Product Scope; `app/templates/profiles/_page_editor_chrome.html` | `ug-concept-profile-model` | concept |
| `CAP-GLOBAL-002` | Choose the appropriate product surface for a task. | `README.md` Product Scope and UI Modes | `ug-concept-choose-editor-surface` | concept |
| `CAP-GLOBAL-003` | Open saved-profile modes in separate browser tabs. | Editor mode links and Library row links use `target="_blank"`. | `ug-task-work-across-editor-tabs` | task |
| `CAP-GLOBAL-004` | Keep a new unsaved draft in Guided until its first save creates an ID. | `/profiles/new`; disabled All Settings/JSON mode links before save | `ug-task-create-first-profile` | task |
| `CAP-GLOBAL-005` | Select `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`, or system language. | `#lang`; active locale catalog matrix | `ug-task-change-interface-language` | task |
| `CAP-GLOBAL-006` | Understand browser-language matching and supported-locale fallback. | Locale runtime contract and README Localization | `ug-concept-language-detection-fallback` | concept |
| `CAP-GLOBAL-007` | Select system, light, or dark theme. | `#theme` in `_page_header.html` | `ug-task-change-interface-theme` | task |
| `CAP-GLOBAL-008` | Identify the running BPM version. | Header `v{{ app_version }}` and root version contract | `ug-reference-product-version` | reference |
| `CAP-GLOBAL-009` | Read profile name, ID, schema, lifecycle, dirty/saved, and validation context. | `_page_editor_chrome.html` profile metadata/status fields | `ug-reference-profile-status` | reference |
| `CAP-GLOBAL-010` | Create a draft or save changes to an existing profile. | `#save`; new/edit route modes | `ug-task-save-profile` | task |
| `CAP-GLOBAL-011` | Validate the current profile on demand. | `#validate`; validation preview/status | `ug-task-validate-profile` | task |
| `CAP-GLOBAL-012` | Switch among Guided, All Settings, and JSON for a saved profile. | Editor mode grid | `ug-task-switch-editor-mode` | task |
| `CAP-GLOBAL-013` | Resolve concurrent save conflicts by reloading, saving a copy, or overwriting. | `#save-conflict-panel` and its three actions | `ug-troubleshoot-save-conflict` | troubleshooting |
| `CAP-GLOBAL-014` | Inspect profile lifecycle and compliance summaries. | `#profile-lifecycle-panel`; `#profile-compliance-panel` | `ug-task-review-profile-context` | task |
| `CAP-GLOBAL-015` | Use localized status, error, focus, and keyboard feedback across responsive layouts. | ARIA live regions, focus contracts, responsive UI contract tests | `ug-concept-accessible-product-operation` | concept |

## Profile Library Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-LIB-001` | Open the saved-profile Library and understand filtered/total counts. | `GET /profiles`; `#list-summary`; `#list-total-summary` | `ug-task-use-profile-library` | task |
| `CAP-LIB-002` | Search profiles by name. | Library `#search` | `ug-task-find-profile` | task |
| `CAP-LIB-003` | Filter profiles by Firefox schema channel. | `#library-schema-filter` | `ug-task-filter-profile-library` | task |
| `CAP-LIB-004` | Filter active, archived, or all lifecycle states. | `#library-lifecycle-filter` | `ug-task-filter-profile-library` | task |
| `CAP-LIB-005` | Filter passed, failed, or not-yet-validated profiles. | `#library-validation-filter` | `ug-task-filter-profile-library` | task |
| `CAP-LIB-006` | Sort by updated, created, name, schema, or ID in either direction. | `#sort`; `#order` | `ug-task-sort-profile-library` | task |
| `CAP-LIB-007` | Refresh the Library and interpret load/action status. | `#refresh`; `#status` | `ug-task-refresh-profile-library` | task |
| `CAP-LIB-008` | Start a new Guided profile draft. | `#create-profile-link` to `/profiles/new` | `ug-task-create-first-profile` | task |
| `CAP-LIB-009` | Import a Firefox Enterprise `policies.json` file. | `#import-firefox-policies`; file/status controls | `ug-task-import-policies-json` | task |
| `CAP-LIB-010` | Inspect row identity, schema, note, validation/lifecycle state, and update time. | Library row renderer and table headings | `ug-reference-library-profile-row` | reference |
| `CAP-LIB-011` | Open a profile in Guided Editor. | Library row title/open action | `ug-task-open-saved-profile` | task |
| `CAP-LIB-012` | Open a profile in All Settings. | Library `library_action_all_settings` | `ug-task-open-saved-profile` | task |
| `CAP-LIB-013` | Open a profile in JSON Editor. | Library `library_action_json` | `ug-task-open-saved-profile` | task |
| `CAP-LIB-014` | Open the dedicated Compare interface in a new tab. | `#compare-profiles-link` | `ug-task-compare-profiles` | task |
| `CAP-LIB-015` | Duplicate a profile into a named Guided draft. | Clone-name panel, required/duplicate validation, confirm/cancel | `ug-task-duplicate-profile` | task |
| `CAP-LIB-016` | Export an active profile as downloadable Firefox `policies.json`. | Library export action | `ug-task-export-policies-json` | task |
| `CAP-LIB-017` | Archive an active profile reversibly. | Lifecycle action `archive` | `ug-task-archive-profile` | task |
| `CAP-LIB-018` | Restore an archived profile. | Lifecycle action `restore` | `ug-task-restore-profile` | task |
| `CAP-LIB-019` | Permanently delete an active or archived profile after confirmation. | Lifecycle action `hard-delete`; irreversible confirmation | `ug-task-permanently-delete-profile` | task |
| `CAP-LIB-020` | Understand archived-profile limitations, including unavailable direct export. | Archived row state and disabled export action | `ug-reference-archived-profile-behavior` | reference |
| `CAP-LIB-021` | Recover from Library load, import, lifecycle, or deletion failures. | Library status/error paths and ARIA feedback | `ug-troubleshoot-library-operation` | troubleshooting |

## Profile Comparison Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-CMP-001` | Search independently for Profile A and Profile B. | `#compare-left-search`; `#compare-right-search` | `ug-task-compare-profiles` | task |
| `CAP-CMP-002` | Select profiles from bounded, scrollable result lists. | Compare result listboxes and bounded-list contract | `ug-task-select-comparison-profiles` | task |
| `CAP-CMP-003` | Review each selected profile summary before comparison. | `data-compare-selected-profile` | `ug-task-select-comparison-profiles` | task |
| `CAP-CMP-004` | Compare the union of policy and managed-preference settings. | `#compare-settings-table`; README comparison contract | `ug-task-interpret-profile-comparison` | task |
| `CAP-CMP-005` | Interpret equal, different, and missing values on either side. | Compare state renderer and README UI Modes | `ug-reference-comparison-states` | reference |
| `CAP-CMP-006` | Use Compare as a dedicated new-tab surface with shared language/theme and no redundant back action. | Library handoff and Compare route contracts | `ug-concept-comparison-workflow` | concept |

## Guided Editor Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-GUIDED-001` | Navigate the six task-first Guided steps. | `get_wizard_steps()`; `#wizard-stepper` | `ug-task-use-guided-editor` | task |
| `CAP-GUIDED-002` | Search Guided controls and jump to a matching setting. | `#wizard-settings-search-input` and result handoff | `ug-task-search-guided-settings` | task |
| `CAP-GUIDED-003` | Set profile name and Firefox schema channel. | Step 1 and editor chrome fields | `ug-task-choose-profile-identity-schema` | task |
| `CAP-GUIDED-004` | Choose a task scenario and starting configuration. | Step 1 scenario-first setup | `ug-task-choose-guided-scenario` | task |
| `CAP-GUIDED-005` | Apply a starter preset. | Step 1 starter preset catalog | `ug-task-apply-starter-preset` | task |
| `CAP-GUIDED-006` | Add a supported CIS layer to the baseline. | Step 1 CIS controls and compliance-aware baseline | `ug-task-apply-cis-layer` | task |
| `CAP-GUIDED-007` | Configure browser access, network behavior, and general defaults. | Step 2 Browser access & defaults | `ug-task-configure-browser-access-defaults` | task |
| `CAP-GUIDED-008` | Configure home surfaces, navigation, managed search engines, and suggestions. | Step 2 home/search sections | `ug-task-configure-home-search-navigation` | task |
| `CAP-GUIDED-009` | Configure privacy, permissions, cookies, cleanup, and hardening posture. | Step 3 Security & privacy | `ug-task-configure-security-privacy` | task |
| `CAP-GUIDED-010` | Configure accounts, language, translation, add-ons, bookmarks, and site handling. | Step 4 Users, add-ons & sites | `ug-task-configure-users-addons-sites` | task |
| `CAP-GUIDED-011` | Configure supported Firefox AI and smart-feature policies on Release. | Step 5 AI & smart features | `ug-task-configure-firefox-ai-policies` | task |
| `CAP-GUIDED-012` | Understand why unsupported AI controls are absent on ESR 140.12. | Step 5 ESR unavailable state | `ug-reference-schema-dependent-guided-controls` | reference |
| `CAP-GUIDED-013` | Expand fine-tuning and advanced controls deliberately. | Guided disclosures and advanced fields | `ug-task-use-guided-fine-tuning` | task |
| `CAP-GUIDED-014` | Review the configuration in plain language before handoff. | Step 6 Review & export | `ug-task-review-guided-profile` | task |
| `CAP-GUIDED-015` | Save and download the reviewed version. | Step 6 plus editor save/export actions | `ug-task-save-export-guided-profile` | task |

## All Settings Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-SET-001` | Open All Settings for complete visual control of a saved profile. | `GET /profiles/{id}/settings`; README All Settings | `ug-task-use-all-settings` | task |
| `CAP-SET-002` | Use Review as the default attention-first mode. | `data-settings-mode="review"` | `ug-task-review-attention-items` | task |
| `CAP-SET-003` | Review invalid, CIS manual-review, raw, unknown, deprecated, and imported items. | Review summary/actions and README mode contract | `ug-task-review-attention-items` | task |
| `CAP-SET-004` | Recognize a clean profile with no remaining review items. | Review empty/completion state | `ug-reference-all-settings-review-states` | reference |
| `CAP-SET-005` | Use Configured mode to inspect what the profile applies. | `data-settings-mode="configured"` | `ug-task-inspect-configured-settings` | task |
| `CAP-SET-006` | Review configured domain/category summaries. | `#all-settings-configured-summary` | `ug-task-inspect-configured-settings` | task |
| `CAP-SET-007` | Filter configured values by baseline, CIS, manual, imported, or raw source. | `#all-settings-source-filters` | `ug-task-filter-settings-by-source` | task |
| `CAP-SET-008` | Use Catalog mode to browse every supported policy and known preference. | `data-settings-mode="catalog"` | `ug-task-browse-settings-catalog` | task |
| `CAP-SET-009` | Search configured settings, available policies, preferences, and actions. | All Settings search and grouped-result contract | `ug-task-search-all-settings` | task |
| `CAP-SET-010` | Filter by configured, available, Guided-covered, All-Settings-only, invalid, deprecated, raw, or unknown state. | `[data-settings-list-filter]` toolbar | `ug-task-filter-all-settings` | task |
| `CAP-SET-011` | Work with bounded or paginated large inventories. | `#all-settings-list-budget`; README long-list contract | `ug-reference-large-settings-inventories` | reference |
| `CAP-SET-012` | Select a setting and inspect value, source, validation, and product location. | `#all-settings-detail-panel` | `ug-task-inspect-setting-details` | task |
| `CAP-SET-013` | Apply or edit a policy or managed-preference value. | Primary detail editor apply flow | `ug-task-edit-setting-detail` | task |
| `CAP-SET-014` | Remove or reset a configured value. | Primary detail editor remove/reset flows | `ug-task-remove-reset-setting` | task |
| `CAP-SET-015` | Add a managed preference not yet configured. | `#all-settings-add-preference` | `ug-task-add-managed-preference` | task |
| `CAP-SET-016` | Navigate categories and mapped control clusters. | Category catalog, map filters, jump targets | `ug-task-navigate-settings-categories` | task |
| `CAP-SET-017` | Reach advanced schema-shell and preference controls without duplicate default editors. | `#all-settings-catalog-advanced`; disclosure shells | `ug-task-use-advanced-schema-controls` | task |
| `CAP-SET-018` | Inspect imported unknown keys and raw-fallback values without losing them. | Unknown/raw inventory and attention states | `ug-task-handle-raw-unknown-settings` | task |
| `CAP-SET-019` | Follow focused links between search, All Settings, and JSON locations. | Route focus targets and navigation resolvers | `ug-task-follow-setting-deep-link` | task |

## JSON Editor Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-JSON-001` | Open the complete profile as a Firefox `policies.json` document. | `GET /profiles/{id}/json`; `_page_json_workspace.html` | `ug-task-use-json-editor` | task |
| `CAP-JSON-002` | Edit JSON with the locally bundled Monaco editor. | `#editor`; self-hosted Monaco contract | `ug-task-edit-raw-policies-json` | task |
| `CAP-JSON-003` | Format the current JSON document. | JSON-only `#format` action | `ug-task-format-json-document` | task |
| `CAP-JSON-004` | Validate raw JSON and policy values. | Shared `#validate` action and status | `ug-task-validate-json-document` | task |
| `CAP-JSON-005` | Save a valid raw document back to the canonical profile. | Shared `#save` action | `ug-task-save-json-document` | task |
| `CAP-JSON-006` | Download the current profile as canonical Firefox `policies.json`. | `#download-firefox-policies` | `ug-task-export-policies-json` | task |
| `CAP-JSON-007` | Use JSON for exact review, migration checks, troubleshooting, and raw values. | README JSON Editor | `ug-concept-when-to-use-json-editor` | concept |
| `CAP-JSON-008` | Open JSON at a focused editor/setting location from another surface. | JSON focus query and route navigation mapping | `ug-task-follow-setting-deep-link` | task |

## Firefox Boundary, Schema, And CIS User Workflows

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-BOUNDARY-001` | Choose between supported Firefox Release 152 and ESR 140.12 schemas. | Schema channel catalog and README supported schemas | `ug-task-choose-firefox-schema` | task |
| `CAP-BOUNDARY-002` | Understand how schema choice changes validation and available controls. | README schema behavior; conditional Guided controls | `ug-concept-schema-aware-behavior` | concept |
| `CAP-BOUNDARY-003` | Import Firefox `policies.json` into BPM's normalized profile model. | Library import and README boundary contract | `ug-task-import-policies-json` | task |
| `CAP-BOUNDARY-004` | Export BPM's normalized profile as canonical Firefox `policies.json`. | Library/JSON export and README boundary contract | `ug-task-export-policies-json` | task |
| `CAP-BOUNDARY-005` | Understand policies versus managed `Preferences` values and lock states. | Canonical profile model and All Settings inventory | `ug-concept-policies-and-managed-preferences` | concept |
| `CAP-CIS-001` | Start from a built-in corporate, classroom, or security-oriented preset. | Starter preset catalog and README capabilities | `ug-task-apply-starter-preset` | task |
| `CAP-CIS-002` | Choose a supported CIS baseline/level. | Guided baseline/CIS selection | `ug-task-apply-cis-layer` | task |
| `CAP-CIS-003` | Understand how baseline and CIS layers merge into a profile. | Compliance-aware baseline and merge metadata | `ug-concept-cis-layer-merge` | concept |
| `CAP-CIS-004` | Trace configured settings to baseline, CIS, manual, imported, or raw sources. | All Settings source attribution | `ug-task-trace-setting-source` | task |
| `CAP-CIS-005` | Find and resolve CIS recommendations requiring manual review. | Review mode CIS attention state | `ug-task-resolve-cis-manual-review` | task |

## Troubleshooting And Recovery Capabilities

| Capability ID | User capability | Current evidence | Planned DITA topic | Type |
| --- | --- | --- | --- | --- |
| `CAP-RECOVERY-001` | Recover from malformed JSON syntax. | JSON/import parse errors and status surfaces | `ug-troubleshoot-malformed-json` | troubleshooting |
| `CAP-RECOVERY-002` | Recover from a failed file import. | Library import error feedback | `ug-troubleshoot-import-failure` | troubleshooting |
| `CAP-RECOVERY-003` | Interpret structured policy validation failures. | Validation preview, Review mode, API error mapping | `ug-troubleshoot-policy-validation` | troubleshooting |
| `CAP-RECOVERY-004` | Handle an unsupported schema channel or schema-dependent setting. | Supported-channel and conditional-control contracts | `ug-troubleshoot-schema-mismatch` | troubleshooting |
| `CAP-RECOVERY-005` | Preserve and review unknown/imported or raw-fallback settings. | All Settings attention/detail behavior | `ug-task-handle-raw-unknown-settings` | task |
| `CAP-RECOVERY-006` | Resolve an empty or duplicate profile name during creation/clone. | Name hints and clone-name validation | `ug-troubleshoot-profile-name` | troubleshooting |
| `CAP-RECOVERY-007` | Resolve a concurrent update without silently losing changes. | Save-conflict reload/copy/overwrite panel | `ug-troubleshoot-save-conflict` | troubleshooting |
| `CAP-RECOVERY-008` | Recover when a bookmarked profile route no longer exists. | Web route 404 `Profile not found` | `ug-troubleshoot-missing-profile` | troubleshooting |
| `CAP-RECOVERY-009` | Recover from a network or BPM API operation failure. | Library/editor error status contracts | `ug-troubleshoot-product-connection` | troubleshooting |
| `CAP-RECOVERY-010` | Cancel or safely confirm archive/permanent-delete actions. | Library lifecycle confirmations and status | `ug-task-manage-destructive-actions` | task |
| `CAP-RECOVERY-011` | Avoid losing unsaved editor changes during navigation or close. | `profiles_runtime_dirty_guard.js` | `ug-troubleshoot-unsaved-changes` | troubleshooting |
| `CAP-RECOVERY-012` | Open an archived profile deliberately with archived context. | `include_deleted` route behavior and archived badges | `ug-task-review-archived-profile` | task |

## README Main-Capability Closure Matrix

This table closes every bullet in README `Main Capabilities`. More detailed README statements are
covered by the route/surface tables above.

| README capability | Covered capability IDs |
| --- | --- |
| Database-backed Firefox policy profile library | `CAP-GLOBAL-001`, `CAP-LIB-001`–`CAP-LIB-021` |
| Create, edit, duplicate, archive, restore, permanently delete, import, and export workflows | `CAP-GLOBAL-010`, `CAP-LIB-008`–`CAP-LIB-019` |
| Named clone drafts | `CAP-LIB-015`, `CAP-RECOVERY-006` |
| Dedicated saved-profile comparison | `CAP-CMP-001`–`CAP-CMP-006` |
| Firefox Enterprise `policies.json` import and export | `CAP-LIB-009`, `CAP-LIB-016`, `CAP-BOUNDARY-003`, `CAP-BOUNDARY-004` |
| Version-aware validation against bundled schemas | `CAP-GLOBAL-011`, `CAP-BOUNDARY-001`, `CAP-BOUNDARY-002`, `CAP-RECOVERY-003`, `CAP-RECOVERY-004` |
| Guided editor for common scenarios | `CAP-GUIDED-001`–`CAP-GUIDED-015` |
| Dedicated AI and smart browser features step | `CAP-GUIDED-011`, `CAP-GUIDED-012` |
| Schema-aware ESR/Release behavior | `CAP-BOUNDARY-001`, `CAP-BOUNDARY-002`, `CAP-GUIDED-012` |
| Triage-first All Settings | `CAP-SET-001`–`CAP-SET-019` |
| JSON editor backed by local Monaco | `CAP-JSON-001`–`CAP-JSON-008` |
| CIS assets, starter presets, generated layers, and merge logic | `CAP-CIS-001`–`CAP-CIS-005` |
| English source UI with six runtime locales | `CAP-GLOBAL-005`, `CAP-GLOBAL-006`, `CAP-GLOBAL-015` |

## Route And State Closure

| Route/state | User Guide treatment |
| --- | --- |
| `/profiles` | Library tasks and lifecycle/reference topics. |
| `/profiles/compare` | Comparison selection, interpretation, and workflow topics. |
| `/profiles/new` | First-save and Guided creation topics. |
| `/profiles/{id}/edit` | Saved-profile Guided tasks. |
| `/profiles/{id}/settings` | Review, Configured, Catalog, search, detail, and advanced-control tasks. |
| `/profiles/{id}/json` | Raw JSON edit, format, validate, save, export, and recovery tasks. |
| Active profile | Normal edit/export/archive workflows. |
| Unsaved draft | Guided-only workflow until first save creates an ID. |
| Archived profile | Deliberate include-deleted review, restore, permanent deletion, and limitations. |
| Invalid profile/document | Validation, attention-first review, diagnosis, and recovery. |
| Release-only control | Conditional topic content and schema support labeling. |
| ESR-unsupported control | Explicit unavailable-state explanation without rendering a false workflow. |

## Audit Result

- 106 stable capability IDs map to 89 planned locale-independent DITA topic IDs.
- All five product surfaces and every README `Main Capabilities` bullet have primary coverage.
- API operation detail, individual Firefox policy detail, and individual CIS recommendation detail
  intentionally remain assigned to `BPM090-M2-02`, `BPM090-M2-03`, and `BPM090-M2-04`.
- Administrator/distribution documentation remains explicitly deferred.
- Any new user-visible route, action, state, error family, schema-dependent behavior, or README
  capability must update this inventory and its contract test before release.
