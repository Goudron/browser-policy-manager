# Guided Editor Six-Step Mapping

Date: `2026-05-16`

This document maps the current eight-step Guided editor onto the target six-step model before implementation starts.
It is the migration contract for `GID-002` through `GID-010`: every current guided capability, data binding,
summary, and jump target must remain represented after the step model changes.

## Target Model

| New step | Target label | Current source steps |
|---|---|---|
| `1` | `Profile & baseline` | old step `1` |
| `2` | `Browser access & defaults` | old steps `2`, `3`, `4` |
| `3` | `Security & privacy` | old step `5` |
| `4` | `Users, add-ons & sites` | old step `6` |
| `5` | `AI & smart features` | old step `7` |
| `6` | `Review & export` | old step `8` |

## Current-To-Target Step Map

| Current step | Current label | Target step | Migration rule |
|---|---|---|---|
| `1` | `Start` | `1` | Keep the start experience, rename it to task-first wording. |
| `2` | `Network & browser basics` | `2` | Keep as the first section group inside the merged browser-defaults step. |
| `3` | `Home & startup` | `2` | Move after network/browser basics inside the merged browser-defaults step. |
| `4` | `Search & navigation` | `2` | Move after home/startup inside the merged browser-defaults step. |
| `5` | `Privacy & security` | `3` | Keep as one dedicated posture step. |
| `6` | `Accounts, languages, add-ons & sites` | `4` | Keep as one operational step, with clearer local navigation. |
| `7` | `AI & smart features` | `5` | Keep standalone and full-width for future Firefox growth. |
| `8` | `Review & export` | `6` | Keep as the final step, update all summaries to six-step wording. |

## Target Step Contracts

### Step 1: `Profile & baseline`

Current source:

- `app/templates/profiles/_page_wizard_step_setup.html`
- `app/static/profiles_wizard_flow.js`

Controls that stay in step `1`:

- Profile identity: `wizard-name`
- Schema channel: `wizard-schema`
- Hidden export mode field: `wizard-mode`
- Scenario selector: `data-scenario-key`
- Starter baseline selector: `data-starter-key`
- CIS layer selector: `data-cis-layer-key`

State and binding contract:

- Step `1` remains the only full-snapshot scope in `getStepScope()`.
- Existing wizard state keys stay owned here:
  - `wizardScenario`
  - `wizardStarter`
  - `wizardComplianceLayer`
- Review/export must still consume:
  - `wizard-summary-name`
  - `wizard-summary-schema`
  - `wizard-summary-starter`
  - `wizard-summary-cis`
  - `wizard-summary-derived`
  - `wizard-summary-lifecycle-list`
  - `wizard-export-baseline-list`

No-loss check:

- Profile name, schema channel, scenario presets, baseline presets, `keep_current`, `blank`, and CIS layer selection remain visible and editable.

### Step 2: `Browser access & defaults`

Current sources:

- old step `2`: `app/templates/profiles/_page_wizard_step_general.html`
- old step `3`: `app/templates/profiles/_page_wizard_step_home.html`
- old step `4`: `app/templates/profiles/_page_wizard_step_search.html`

Recommended internal section order:

1. `Browser basics`
2. `Proxy`
3. `Trust and authentication`
4. `Home and startup`
5. `New tab and first-run surfaces`
6. `Firefox Home`
7. `Default search`
8. `Managed engines`
9. `Suggestions`
10. `Local review`

Controls that move into target step `2`:

| Current source | Controls and bindings |
|---|---|
| Browser basics | `wizard_manual_policy_groups["general_browser_behavior"]`, `wizard-general-policy-presets` |
| Proxy | `wizard-proxy-mode`, `wizard-proxy-auto-config-url`, `wizard-proxy-http`, `wizard-proxy-ssl`, `wizard-proxy-ftp`, `wizard-proxy-socks`, `wizard-proxy-socks-version`, `wizard-proxy-passthrough`, `wizard-proxy-locked`, `wizard-proxy-use-http-for-all`, `wizard-proxy-auto-login`, `wizard-proxy-use-dns` |
| Trust/authentication | `DNSOverHTTPS`, `WindowsSSO`, `Authentication`, `Certificates` mounted cards |
| Home/startup | `wizard-homepage-url`, `wizard-homepage-start-page`, `wizard-homepage-additional`, `wizard-homepage-locked` |
| New tab / overrides | `wizard-new-tab-page`, `wizard-override-first-run`, `wizard-override-post-update` |
| Firefox Home | `FirefoxHome` fields: `Search`, `TopSites`, `Pocket`, `SponsoredTopSites`, `Highlights`, `Stories`, `SponsoredPocket`, `SponsoredStories`, `Snippets`, `Locked`, plus `wizard_manual_policy_groups["home_surfaces"]` |
| Default search | `wizard-search-suggest`, `wizard-search-default-engine`, `wizard-search-bar`, `wizard-search-prevent-installs`, `wizard-search-remove` |
| Managed engines | `wizard-search-engine-add`, custom `SearchEngines.Add` rows, preset buttons in `searchEnginePresetCatalog` |
| Suggestions | `FirefoxSuggest` fields: `WebSuggestions`, `SponsoredSuggestions`, `ImproveSuggest`, `Locked` |

Summaries and local review that must survive:

- Network review:
  - `wizard-network-summary-authentication`
  - `wizard-network-summary-certificates`
  - `wizard-network-summary-dns`
  - `wizard-network-summary-windows-sso`
- Home review functions and targets stay represented:
  - homepage
  - overrides
  - Firefox Home
- Search review functions and targets stay represented:
  - defaults
  - removed engines
  - custom engines
  - suggestions

State and binding contract:

- Merge `stepScopedPolicyKeys[2]`, `[3]`, and `[4]` into the new step `2` scope.
- Merge `stepPreferenceSections[2]`, `[3]`, and `[4]` into the new step `2` scope:
  - `general`
  - `home`
  - `search`
- `wizardSearchSectionSteps.general`, `.home`, and `.search` must all resolve to target step `2`.
- Schema shell policy sections currently split across old steps `2`, `3`, and `4` must all remain reachable from the merged guided step.
- Existing review/export fragments `network`, `home`, and `search` should become one guided-area group in the final six-step review, while their internal summaries may stay separate for readability.

Hard-coded references that must be remapped:

- `#wizard-step-4-managed-engines` in `app/static/profiles_network.js`
- compare area grouping for old `step_two`, `step_three`, and `step_four`
- shell-policy preferred step lookups for old `2`, `3`, and `4`
- step-memory snapshots and recent-change labels for old `2`, `3`, and `4`

No-loss check:

- Proxy, trust, updates/downloads/common browser behavior, all home surfaces, default search, custom search engines, and Firefox Suggest remain visually editable.

### Step 3: `Security & privacy`

Current source:

- `app/templates/profiles/_page_wizard_step_privacy.html`

Controls that stay in target step `3`:

- Hardening posture presets
- Cleanup sub-posture presets
- Site-data posture presets
- `Permissions`
- `Cookies`
- `IPProtectionAvailable`

Current policy scope that remaps from old step `5` to target step `3`:

- `DisableTelemetry`
- `DisableFirefoxStudies`
- `DisablePrivateBrowsing`
- `OfferToSaveLogins`
- `PasswordManagerEnabled`
- `BlockAboutConfig`
- `BlockAboutProfiles`
- `DisableDeveloperTools`
- `DisableBuiltinPDFViewer`
- `HttpsOnlyMode`
- `SanitizeOnShutdown`
- `Permissions`
- `Cookies`
- `IPProtectionAvailable`

Summaries and jump targets that must survive:

- `wizard-privacy-summary-user-data`
- `wizard-privacy-summary-cleanup`
- `wizard-privacy-summary-permissions`
- `wizard-privacy-summary-cookies`
- current `data-privacy-review-jump` targets

State and binding contract:

- Old `stepScopedPolicyKeys[5]` becomes target step `3`.
- Old `stepPreferenceSections[5] = ["privacy"]` becomes target step `3`.
- Mounted cards for `IPProtectionAvailable`, `Permissions`, and `Cookies` must request shell data from target step `3`.
- `wizardSearchSectionSteps.privacy` must resolve to target step `3`.

No-loss check:

- Hardening, telemetry/privacy posture, cleanup, site permissions, cookies, and VPN visibility stay editable and reviewable in one place.

### Step 4: `Users, add-ons & sites`

Current source:

- `app/templates/profiles/_page_wizard_step_sync.html`

Controls that stay in target step `4`:

| Area | Controls and bindings |
|---|---|
| Accounts | `wizard_manual_policy_groups["sync_accounts"]`, `UserMessaging` |
| Language | `RequestedLocales`, `TranslateEnabled` |
| Extensions | `wizard-extension-default-mode`, install/locked/uninstall rule textareas, curated extension profiles, `InstallAddonsPermission`, `ExtensionSettings` |
| Bookmarks | bookmarks handoff, configured bookmark jump actions |
| Websites | `WebsiteFilter`, `Handlers`, website posture selectors |

Summaries and handoffs that must survive:

- `wizard-sync-section-status`
- `wizard-language-section-status`
- `wizard-language-ai-handoff`
- `wizard-extension-section-status`
- `wizard-bookmarks-section-status`
- `wizard-website-section-status`
- bookmark review jump buttons
- website access review jump buttons

State and binding contract:

- Old `stepScopedPolicyKeys[6]` becomes target step `4`.
- Old `stepPreferenceSections[6] = ["sync"]` becomes target step `4`.
- `wizardSearchSectionSteps.sync` must resolve to target step `4`.
- Mounted-card preferred steps currently hard-coded as `6` must become `4`.
- Extension fallback query `#wizard-step-6 [data-policy-key]` must be remapped.

No-loss check:

- Mozilla account controls, language/translation, add-on governance, curated add-on profiles, bookmarks, and website handling all remain accessible.

### Step 5: `AI & smart features`

Current source:

- `app/templates/profiles/_page_wizard_step_ai.html`

Controls that stay in target step `5`:

- AI posture presets
- `AIControls`
- `GenerativeAI`
- `VisualSearchEnabled`
- provider handoff to the visual settings surface
- ESR empty state

Summaries and jump targets that must survive:

- AI review summary for availability, providers, and surfaces
- `wizard-ai-providers-section-anchor`
- fallback jump target currently using `wizard-step-7`

State and binding contract:

- Old `stepScopedPolicyKeys[7]` becomes target step `5`.
- AI remains a full standalone step, not a subsection under language or privacy.
- Mounted-card preferred steps currently hard-coded as `7` must become `5`.
- `wizardSearchSectionSteps.ai` must resolve to target step `5`.

No-loss check:

- AI remains first-class and ready for future growth without losing current explicit controls.

### Step 6: `Review & export`

Current source:

- `app/templates/profiles/_page_wizard_step_export.html`

Controls that stay in target step `6`:

- Save / validate / download actions
- readiness summary
- included / missing / review-now explainability lists
- profile baseline summary
- guided-area summaries
- CIS summary and exception details
- shareable summary
- technical review shell and compatibility panel

Required review grouping after migration:

| New guided review group | Current fragments absorbed |
|---|---|
| `Profile & baseline` | baseline/profile metadata currently outside guided-area cards |
| `Browser access & defaults` | old `network`, `home`, `search` groups |
| `Security & privacy` | old `privacy` group |
| `Users, add-ons & sites` | old `features` group |
| `AI & smart features` | old `ai` group |

State and binding contract:

- Old review panel `wizard-step-8` becomes target `wizard-step-6`.
- Final wizard save should land on step `6`, not the old AI step fallback.
- All advanced/raw focus routing currently anchored to `settings-schema-shell-step-8` needs a compatibility decision:
  - guided review step number becomes `6`
  - raw/all-settings shell routing should either keep a stable semantic token or move together intentionally
- `data-final-review-jump` values may remain semantically named (`network`, `home`, `search`, `privacy`, `features`, `ai`) even when the visible grouped cards are consolidated.

No-loss check:

- Export readiness, validation, download, final summaries, CIS review, shareable summary, and technical fallbacks all remain available.

## Cross-Cutting Runtime Remap

### Step registry and localized copy

Update:

- `app/web/firefox_wizard_steps.py`
- `app/i18n/en.json`
- `app/i18n/ru.json`
- `_page_wizard.html`

Required change:

- Registry length changes from `8` to `6`.
- Progress text changes from `Step n of 8` to `Step n of 6`.
- Visible labels become the six target labels in both locales.

### Wizard flow state

Update:

- `app/static/profiles_wizard_flow.js`

Required change:

- `wizardTotalSteps`
- `stepScopedPolicyKeys`
- `stepPreferenceSections`
- `renderRecentStepMemory()` loop currently fixed to `[1, 2, 3, 4, 5, 6, 7]`
- `finishWizard()` currently lands on old step `7`
- any direct `setWizardStep(7)` usage

### Guided settings search

Update:

- `app/static/profiles_catalogs.js`
- `app/static/profiles_settings_search.js`

Required change:

- Section ids stay semantic (`general`, `home`, `search`, `privacy`, `sync`, `ai`, `review`).
- Their `step` metadata changes to the six-step model.
- Search results for `general`, `home`, and `search` must all open target step `2`.

### Schema shell and mounted cards

Update:

- `app/web/firefox_wizard_shell/catalog.py`
- `app/static/profiles_schema_shell_sections.js`
- tests in `tests/test_firefox_wizard_shell.py`

Required change:

- Shell buckets currently keyed as old `2..8` must be remapped to new `2..6`.
- Browser behavior, home/startup, and search sections need one shared target guided step while keeping internal policy sections intact.
- Mounted-card preferred-step lookups for old `5`, `6`, and `7` must become `3`, `4`, and `5`.

### Review, compare, and jump routing

Update:

- `app/static/profiles_review.js`
- `app/static/profiles_workspace.js`
- `app/static/profiles_library_bootstrap.js`
- `app/static/profiles_runtime.js`
- `app/web/profiles.py`

Required change:

- Compare group keys collapse from seven current guided areas to five target guided areas.
- Old compare buckets `step_two`, `step_three`, and `step_four` merge.
- `wizard-export-guided-group-network`, `-home`, and `-search` become one visible guided group, while internal summaries may remain distinct.
- `wizard-export-guided-group-features` becomes the new users/add-ons/sites group.
- hard-coded references to:
  - `wizard-step-7`
  - `wizard-step-6`
  - `wizard-step-4-managed-engines`
  - `settings-schema-shell-step-8`
  must be audited and either remapped or intentionally preserved behind a semantic compatibility alias.

## No-Loss Coverage Checklist

The six-step target model is complete only if all current guided areas remain represented:

- [x] profile identity
- [x] schema channel
- [x] scenarios
- [x] starter baselines
- [x] CIS layer
- [x] common browser behavior
- [x] updates and downloads
- [x] proxy
- [x] DNS over HTTPS
- [x] Windows SSO
- [x] authentication
- [x] certificates
- [x] homepage
- [x] startup mode
- [x] new tab
- [x] first-run override
- [x] post-update override
- [x] Firefox Home
- [x] default search
- [x] managed search engines
- [x] Firefox Suggest
- [x] hardening posture
- [x] cleanup posture
- [x] site permissions
- [x] cookies
- [x] IP protection availability
- [x] Mozilla account controls
- [x] user messaging
- [x] requested locales
- [x] translation
- [x] extension governance
- [x] curated extension profiles
- [x] extension install / lock / uninstall rules
- [x] bookmarks
- [x] website filtering
- [x] handlers
- [x] AI controls
- [x] generative AI
- [x] visual search
- [x] save / validate / download
- [x] readiness review
- [x] guided-area review
- [x] CIS summary and exceptions
- [x] shareable summary
- [x] advanced/raw technical review

## Implementation Sequence Implied By This Map

1. Update the step registry and locale labels.
2. Merge the old step templates and local anchors into the target template structure.
3. Remap wizard-flow scope tables and search metadata.
4. Remap schema-shell buckets and mounted-card preferred steps.
5. Collapse review and compare visible groups while keeping internal summaries readable.
6. Update tests only after the new numbering model is stable.

## Source Inventory Used For This Mapping

- `app/web/firefox_wizard_steps.py`
- `app/web/firefox_wizard_shell/catalog.py`
- `app/templates/profiles/_page_wizard.html`
- `app/templates/profiles/_page_wizard_step_setup.html`
- `app/templates/profiles/_page_wizard_step_general.html`
- `app/templates/profiles/_page_wizard_step_home.html`
- `app/templates/profiles/_page_wizard_step_search.html`
- `app/templates/profiles/_page_wizard_step_privacy.html`
- `app/templates/profiles/_page_wizard_step_sync.html`
- `app/templates/profiles/_page_wizard_step_ai.html`
- `app/templates/profiles/_page_wizard_step_export.html`
- `app/static/profiles_catalogs.js`
- `app/static/profiles_settings_search.js`
- `app/static/profiles_wizard_flow.js`
- `app/static/profiles_review.js`
- `app/static/profiles_schema_shell_sections.js`
- `app/static/profiles_workspace.js`
- `app/static/profiles_library_bootstrap.js`
- `app/static/profiles_network.js`
- `app/static/profiles_extensions.js`
- `app/static/profiles_runtime.js`
- `app/web/profiles.py`
- `app/i18n/en.json`
- `app/i18n/ru.json`
