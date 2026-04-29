# Profile Wizard Cognitive Load Backlog

Date: `2026-04-14`

## Goal

Reduce cognitive load across the guided profile wizard without removing the current policy coverage.

The wizard should keep the main path focused on one decision at a time, keep long technical lists behind deliberate disclosure, and make heavy profiles such as `corporate + CIS Level 2` reviewable without scrolling through a long unstructured page.

## Current UX Diagnosis

The current wizard has accumulated several useful guidance layers, but many of them are now visible at the same hierarchy level:

- scenario cards
- baseline and preset cards
- CIS cards
- settings maps and documentation jump lists
- workflow cards
- fine-tuning panels
- local review cards
- advanced-only preference and schema-shell sections
- final export readiness, compatibility, explainability, guided summary, CIS exceptions, and shareable summary

This creates three recurring problems:

1. Duplicated choices.
   Some steps show multiple sets of cards that answer similar questions, especially the setup step and feature-heavy steps.

2. Long unbounded lists.
   CIS and corporate presets can create many configured settings, and review surfaces expose too many rows at once.

3. Unbalanced desktop layouts.
   Two-column review layouts work for short symmetric cards, but fail when one column contains a long list while the other is mostly empty.

## Product Principles

1. One primary decision per section.
   Each section should start with the main outcome choice. Supporting detail comes after the choice or stays collapsed.

2. Summary before detail.
   Every heavy section should show a compact state summary first: `default`, `changed`, `needs attention`, `advanced-only`, and count badges.

3. Details on demand.
   Long lists, technical compatibility, raw/deprecated/unknown items, and advanced preference controls should be hidden behind explicit disclosure by default.

4. Changed items first.
   Review surfaces should default to configured or attention-worthy items. Full lists should be available, but not the default.

5. Full-width for long content.
   Any block that can grow beyond 7 visible rows should use a full-width layout or a drawer, not a narrow desktop column.

6. Advanced is a destination, not inline clutter.
   Advanced-only sections should be reachable from guided mode through targeted handoff cards, but should not occupy default guided vertical space.

## Shared Backlog

### `UX-CL-00` Shared Disclosure And Review Pattern - Completed

Create a reusable pattern for all guided steps:

- compact step header with current state badges
- optional step index with jump links to subsections
- one visible main choice area
- one compact `What changed here` summary
- collapsed `Fine tuning`
- collapsed `Advanced and technical details`
- local review filtered to configured or attention states

Acceptance criteria:

- All steps can use the same visual grammar.
- A user can identify the main action on a step without reading settings maps or review rows first.
- Step-local review never shows a long unbounded list by default.

Implementation note:

- Added a shared `data-wizard-disclosure-toggle` primitive and applied it to the schema-shell technical coverage block across wizard steps.
- Added shared review filters for existing summary-card lists: `Changed`, `Needs attention`, and `All`.

### `UX-CL-01` Settings Map Compression - Completed

Move settings maps and docs from the top of each section into a collapsed `Settings covered` disclosure.

Affected patterns:

- policy settings maps in general, home, search, sync, extensions, privacy
- preference settings maps in advanced-only sections

Acceptance criteria:

- Settings maps remain available and searchable.
- They no longer appear before the primary choice in guided mode.

Implementation note:

- Added a shared `render_settings_reference` macro that preserves the existing settings map/docs IDs while moving the map and jump controls into the common disclosure pattern.
- Applied it to guided policy maps and advanced preference maps across the general, home, search, privacy, sync, and extensions areas.

### `UX-CL-02` Local Review Filter - Completed

Add a shared filter to review cards:

- `Changed`
- `Needs attention`
- `Advanced-only`
- `All`

Default to `Changed` unless the step has nothing configured, then show a short empty state.

Acceptance criteria:

- Review blocks on network, home, search, privacy, extensions, bookmarks, website access, AI, and export use consistent filtering.
- Large profiles do not produce full review lists without user action.

Implementation note:

- Extended the shared review filter to include `Advanced-only`.
- Added per-filter empty states so review cards default to `Changed` without falling back to full lists when nothing is configured.
- Advanced-only matching now covers rows inside advanced workspace panels and final technical review jumps.

### `UX-CL-03` Long List Budget - Completed

Introduce a visible item budget for dynamic lists:

- show up to 5 important rows by default
- show counts for hidden rows
- expose `Show all N` or open a dedicated drawer

Apply to:

- CIS impact and exceptions
- export included/missing/review lists
- advanced drilldown
- preferences presets/bundles/known lists
- extension profiles and arbitrary extension rules
- website filters and handlers
- bookmarks and managed bookmarks
- search engines

Acceptance criteria:

- No dynamic list renders more than 5-7 rows by default in guided mode.
- Full content is still accessible.

Implementation note:

- Added a shared long-list budget for wizard dynamic lists with a default visible limit of 5 rows.
- Added `Show all {count}` / `Show fewer` controls that preserve access to the full list.
- Applied the budget to wizard export plans, baseline summaries, guided search/preference lists, schema-shell lists, settings targets, and checklist/workflow lists while excluding schema editor nested array/dictionary lists.

### `UX-CL-04` Desktop Layout Rules For Heavy Content - Completed

Replace fixed two-column layouts on heavy review surfaces with adaptive layouts:

- readiness/status blocks can use compact cards
- long summaries become full-width sections
- technical detail moves to tabs, accordions, or drawers
- if one column would be empty, the layout collapses to one column

Acceptance criteria:

- `corporate + CIS Level 2` has no desktop screen where one column is a long page and the other is visually empty.
- Long content does not live in a narrow side column.

Implementation note:

- Replaced the final review grid's fixed two-column split with an adaptive `auto-fit` grid.
- Made the main export/review action card span the full available width, so long final summaries, CIS notes, shareable text, and export explainability do not live in a narrow side column.

## Step Backlog

### Step 1: Setup And Starting Point

Current issues:

- Scenario cards, recommended baselines, CIS cards, and secondary starter cards compete as parallel choices.
- Scenario and baseline summaries add more vertical space between choice groups.
- CIS Level 2 can make the first decision feel like a policy audit before the user has started.

Backlog:

1. `UX-CL-10` Merge scenario and starter preset selection. - Completed
   Present one `Starting point` choice. Scenario selection should directly imply or recommend a baseline instead of showing a second competing baseline grid.
   Delivered: scenario cards now remain the primary setup choice, apply their matching baseline, and keep alternate recommended baselines behind a disclosure for deliberate override.

2. `UX-CL-11` Make `blank` and `keep current` secondary actions. - Completed
   Move them into compact links or a small segmented control.
   Delivered: the alternate start options now render as compact secondary buttons with accessible labels, instead of another large starter-card grid.

3. `UX-CL-12` Replace CIS cards with a compact CIS layer selector. - Completed
   Use `None`, `Level 1`, `Level 2` as a segmented control with a short impact line and a collapsed detail preview.
   Delivered: CIS now uses a compact segmented selector while detailed copy remains available through accessible labels and the existing baseline summary/preview panels.

4. `UX-CL-13` Collapse setup summaries into one impact summary. - Completed
   Replace separate scenario summary, baseline summary, shared-device workflow, clone handoff, and CIS preview blocks with one `What this will apply` panel.
   Delivered: setup impact now lives in one compact panel with scenario, baseline, shared-device/clone workflow, and preview sections while preserving the existing dynamic anchors.

Acceptance criteria:

- The first step has one primary choice, one CIS selector, and one compact summary.
- Starter options are not repeated in multiple grids.

### Step 2: General, Network, Proxy, Trust

Current issues:

- Browser behavior, proxy, enterprise trust, local network review, and advanced preferences sit in one long step.
- Proxy shows both preset cards and a manual mode select, which can feel duplicative.
- Enterprise trust mixes workflow, presets, inline cards, fine tuning, and review.
- Advanced preferences add a second workflow inside the same step.

Backlog:

1. `UX-CL-20` Split step-local navigation into `Browser basics`, `Proxy`, `Trust and authentication`, `Review`. - Completed
   Add a compact index with counts.
   Delivered: step 2 now starts with a compact step map linking to Browser basics, Proxy, Trust and authentication, and Review, each with a small count/complexity hint.

2. `UX-CL-21` Convert proxy presets into mode chips. - Completed
   Make `Inherit`, `No proxy`, `System`, `PAC`, `Manual` the main choice. Show manual/PAC fields only after the mode is selected.
   Delivered: proxy now uses one visible mode selector backed by the existing hidden `wizard-proxy-mode` state, with manual/PAC fields still revealed only for the selected mode.

3. `UX-CL-22` Make enterprise trust a grouped disclosure. - Completed
   Default view shows DNS over HTTPS, Windows SSO, and trust status cards. Authentication and certificates remain collapsed unless changed or selected.
   Delivered: the default trust view keeps presets, DNS/Windows SSO cards, and status visible, while the workflow plus Authentication/Certificates editors now live inside one detail disclosure that still auto-opens for custom auth/cert state.

4. `UX-CL-23` Move general advanced preferences behind a targeted handoff. - Completed
   Keep advanced preference editing out of default guided scroll.
   Delivered: General Preferences editing now sits behind a collapsed targeted handoff, preserving all existing controls and anchors without adding them to the default step scroll.

Acceptance criteria:

- Proxy has one visible way to choose mode.
- Trust and authentication details do not expand unless relevant.
- Advanced preferences do not appear inline by default.

### Step 3: Home, Startup, Firefox Home

Current issues:

- Homepage has general presets and shared-device presets as separate card grids.
- Home overrides and Firefox Home each repeat the same preset/fine-tuning/review rhythm.
- Firefox Home has many simple show/hide selectors that become noisy.
- Workflow and review blocks add a second summary layer.

Backlog:

1. `UX-CL-30` Merge homepage and shared-device presets. - Completed
   Use one `Startup behavior` choice with optional shared-device recommendations.
   Delivered: homepage and shared-device startup choices now render as one startup behavior panel, with shared-device options shown as compact recommendations inside the same decision area.

2. `UX-CL-31` Group home surfaces as `Startup`, `New tab`, `Firefox Home`. - Completed
   Show each group as a compact state row; expand one group at a time.
   Delivered: Startup, New tab, and Firefox Home now render as compact surface rows with only one expanded group at a time, while review/jump targets open their containing group automatically.

3. `UX-CL-32` Replace Firefox Home fine-tuning grid with grouped toggles. - Completed
   Default visible controls: search, shortcuts, Pocket. Sponsored/stories/snippets/lock state stay collapsed.
   Delivered: Firefox Home keeps Search, Top sites, and Pocket visible, while stories/sponsored content, snippets, and layout/advanced Home policies are grouped into collapsed fine-tuning disclosures.

4. [x] `UX-CL-33` Convert home workflow and review into one step summary.
   The summary should show configured homepage, overrides, Firefox Home state, and user messaging with jump actions.
   Delivered: Step 3 now uses one Home setup summary block that keeps the workflow list, homepage/override/Firefox Home/user messaging review rows, and existing jump actions together.

Acceptance criteria:

- The user does not see two homepage preset grids.
- Firefox Home advanced toggles are not all visible at once.

### Step 4: Search And Suggestions

Current issues:

- Search defaults, custom engines, Firefox Suggest, local review, and advanced search preferences all live in one step.
- Custom search engine cards expose many fields at once.
- Preset cards appear both for search posture and for adding engines.
- Advanced preference presets/bundles/known lists can become long.

Backlog:

1. [x] `UX-CL-40` Split into `Default search`, `Managed engines`, `Suggestions`, `Review`.
   Add compact step-local navigation with counts.
   Delivered: Step 4 now starts with a local search step map and separates default search, managed engines, Firefox Suggest, and review into anchored sections.

2. [x] `UX-CL-41` Make custom engine editor progressive.
   First row: name, URL, alias. Method, icon, encoding, suggest URL, description, post data stay in `Advanced fields`.
   Delivered: Custom engine rows now show only engine name, search URL, and alias first, with method/icon/encoding/suggestions/description/POST payload behind an Advanced fields disclosure that auto-opens when advanced values exist.

3. [x] `UX-CL-42` Move engine presets into an add menu.
   Replace always-visible preset grid with `Add preset engine` menu or compact chips.
   Delivered: Managed engine presets now sit behind an Add preset engine disclosure while the blank Add engine action stays visible.

4. [x] `UX-CL-43` Hide advanced search preferences by default.
   Use targeted handoff plus counts for configured advanced preferences.
   Delivered: Search advanced preferences now sit behind an Advanced Search preferences handoff with a configured-count summary, preserving all existing preference controls and anchors.

Acceptance criteria:

- Adding one search engine does not create a large form unless the user opens advanced fields.
- Search preference catalogs do not dominate guided mode.

### Step 5: Privacy, Cleanup, Hardening

Current issues:

- Hardening, cleanup, governance, privacy user data, lockdown, site controls, review, and advanced preferences make this one of the densest steps.
- Multiple sections repeat similar `defaults/balanced/strict` cards.
- Review splits permissions into configured and locked rows, increasing scan burden.
- CIS Level 2 likely makes this step especially long.

Backlog:

1. [x] `UX-CL-50` Consolidate hardening presets into one posture selector.
   Use `Default`, `Balanced`, `Strict` once, then show affected groups: telemetry, HTTPS-only, private browsing, cleanup, site data.
   Delivered: Step 5 now keeps one visible Security posture selector, adds an impact summary for telemetry, HTTPS-only, private browsing, cleanup, and site data, and moves repeated sub-posture preset grids behind targeted disclosures.

2. [x] `UX-CL-51` Move cleanup under the posture impact summary.
   Keep cleanup as an editable sub-choice, but do not show a separate full preset grid unless expanded.
   Delivered: Cleanup now sits directly under the hardening impact summary as an editable sub-choice, while its full preset grid remains hidden until the user expands that control.

3. [x] `UX-CL-52` Group privacy fine tuning by outcome.
   Use groups such as `Telemetry and studies`, `Passwords and private browsing`, `Lockdown`, `Cookies and permissions`.
   Delivered: Privacy fine-tuning panels now group controls by outcome, keeping telemetry/studies, passwords/private browsing, lockdown, and cookies/permissions as distinct scan targets.

4. [x] `UX-CL-53` Collapse governance checklist into a small recommendation panel.
   Show only the next best action and count of remaining recommendations by default.
   Delivered: The hardening governance card now defaults to a compact next-recommendation panel with a remaining count, while the full checklist stays available behind disclosure.

5. [x] `UX-CL-54` Combine privacy review rows.
   Merge permissions configured/locked into one `Permissions` row with subcounts.
   Delivered: The privacy review now shows one `Permissions` row with configured and strict subcounts, plus one jump target into the permissions editor.

Acceptance criteria:

- Privacy has one hardening posture decision instead of several similar strictness grids.
- CIS Level 2 changes are grouped by outcome and do not display as a raw long list.

### Step 6: Accounts, Language, Extensions, Bookmarks, Websites

Current issues:

- This step contains several different product areas: Sync/accounts, language, extensions, bookmarks, website filters, handlers, advanced extension settings, bookmarks review, and website review.
- Extension rollout has two preset grids: rollout posture and focus.
- Website behavior has three preset grids: filter, shared filter, handlers.
- Curated extension profile cards can become tall even with details collapsed.
- Bookmarks are mostly an advanced handoff but still consume guided space.

Backlog:

1. [x] `UX-CL-60` Split step-local navigation into five groups.
   `Accounts`, `Language`, `Extensions`, `Bookmarks`, `Websites`.
   Delivered: Step 6 now starts with a five-group local index and stable anchors for Accounts, Language, Extensions, Bookmarks, and Websites.

2. [x] `UX-CL-61` Merge extension rollout and focus.
   Use one `Extension governance` selector: `Open`, `Block by default`, `Managed allowlist`, `Curated rollout`, `Mixed`.
   Delivered: Step 6 now uses one Extension governance selector that sets the default install posture and opens the relevant rule or curated add-on details only when needed.

3. [x] `UX-CL-62` Convert curated extensions to compact rows.
   Show extension name, current mode, source status, and one details button. Keep install URL, updates, private browsing in details.
   Delivered: Curated add-on cards now render as compact rows with name, mode, source status, and one details button, while install URL, updates, and private browsing stay inside each details panel.

4. [x] `UX-CL-63` Collapse arbitrary extension rules behind rule groups.
   Show install/locked/uninstall as rows with counts and status. Textareas open only when a rule is expanded.
   Delivered: Install, locked, and uninstall arbitrary extension rules now appear as peer rule rows with count/status summaries, while each textarea stays hidden until that specific row is expanded.

5. [x] `UX-CL-64` Make bookmarks a compact handoff unless configured.
   If no bookmarks are configured, show one row with `Open advanced`. If configured, show counts and jump links.
   Delivered: The bookmarks area is now a single compact handoff row by default, and configured profiles reveal count/status text plus direct jump actions for bookmark links, managed folders, and nested bookmark trees.

6. [x] `UX-CL-65` Merge website filter/shared/handler presets.
   Use one `Website access` decision with subchoices for allow/block posture and handler management.
   Delivered: Website access now uses one decision card with two subchoices: site access posture and handler management, replacing the three separate preset groups.

7. [x] `UX-CL-66` Move advanced extension settings out of default guided scroll.
   Use an advanced drawer or targeted handoff with counts.
   Delivered: Advanced extension settings now stay behind the governance handoff with separate counts and targeted jumps for install-source exceptions and arbitrary ExtensionSettings branches.

Acceptance criteria:

- The step does not read as five unrelated pages stitched together.
- Extension and website choices no longer show multiple competing preset grids.

### Step 7: AI And Browser AI Surfaces

Current issues:

- AI availability, governance, providers, surfaces, review, and advanced provider handoff are all visible.
- Providers are partly guided and partly advanced, which can confuse ownership.
- AI surfaces are light now, but the structure can grow into another long page.

Backlog:

1. [x] `UX-CL-70` Use one AI posture selector.
   `Default`, `Disable AI`, `Manage availability`, `Manage providers`, `Mixed`.
   Delivered: Step 7 now starts with one AI posture selector covering default behavior, disabling AI, availability management, provider handoff, and mixed AI review.

2. [x] `UX-CL-71` Treat providers as advanced unless guided provider support is complete.
   Show provider status and a targeted advanced handoff, not a large guided section.
   Delivered: Provider/model controls now render as a compact advanced handoff row with provider-rule status, instead of a larger guided provider section.

3. [x] `UX-CL-72` Merge governance and review into compact state cards.
   Show availability, providers, and surfaces as three state rows with jump actions.
   Delivered: AI governance now owns the three compact state rows for availability, providers, and surfaces, removing the separate review block and checklist duplication.

4. [x] `UX-CL-73` Keep AI surfaces behind fine tuning.
   Only show visual search or adjacent surface controls when posture or current config makes them relevant.
   Delivered: Smart browser surfaces are hidden by default and only appear when VisualSearchEnabled is already configured or the user chooses a mixed AI posture that opens fine tuning.

Acceptance criteria:

- AI step has one clear posture decision.
- Provider details do not imply full guided support when they still require advanced mode.

### Step 8: Final Review And Export

Current issues:

- Readiness, compatibility, next steps, included/missing/review, basics, guided summary, CIS exceptions, shareable summary, and download are all in one long view.
- Desktop two-column layout becomes unbalanced with long lists.
- Technical compatibility appears before the user has completed primary export tasks.

Backlog:

1. [x] `UX-CL-80` Rebuild final step around three tabs or sections.
   `Ready to export`, `What changed`, `Technical details`.
   Delivered: final review now uses three dedicated sections, preserving existing export, summary, and technical ids.

2. [x] `UX-CL-81` Keep readiness and primary actions sticky at the top.
   Save, validate, ready state, download eligibility, and download action should fit in the first desktop viewport.
   Delivered: readiness, save, validate, download, eligibility hint, and checklist now live in a compact sticky primary card; longer next-step lists moved below.

3. [x] `UX-CL-82` Move compatibility into `Technical details`.
   Show raw/deprecated/unknown counts in the top summary only when non-zero.
   Delivered: full compatibility remains in `Technical details`; the sticky export summary shows hidden-by-default technical alert buttons only for non-zero raw/deprecated/unknown counts.

4. [x] `UX-CL-83` Group guided summary by step with filters.
   Default to changed or attention states. Full summary stays available.
   Delivered: guided summary cards are grouped by wizard step, reuse the existing Changed/Needs attention/All filter, and empty groups hide with the active filter.

5. [x] `UX-CL-84` Collapse CIS exceptions.
   Show count and top reasons; full list opens on demand.
   Delivered: final review shows CIS exception count and top reasons first; full note textareas live inside an on-demand details block.

6. [x] `UX-CL-85` Collapse shareable summary.
   Show a `Generate/copy shareable summary` action. Textarea opens only after request.
   Delivered: shareable summary textarea now lives inside a closed details block opened by `Generate/copy shareable summary`; copy remains available after expansion.

7. [x] `UX-CL-86` Replace two-column final layout for heavy content.
   Long detail sections should be full-width or inside drawers.
   Delivered: final guided summary groups now render full-width instead of two columns, while CIS exceptions and shareable summary remain inside on-demand details blocks.

Acceptance criteria:

- The final step's primary readiness and export actions are visible without scrolling on common desktop viewports.
- `corporate + CIS Level 2` final review is navigable through sections and filters, not a single long list.

## Implementation Slices

### Slice A: Cross-Step UX Infrastructure

1. Add shared disclosure primitives for `Settings covered`, `Fine tuning`, `Advanced details`, and `Show all`.
2. Add step-local review filters.
3. Add long-list visible item budgets.
4. Add adaptive layout rules for long content.

### Slice B: Setup And Final Review

1. Implement Step 1 consolidation.
2. Implement Step 8 readiness/change/technical split.
3. Add viewport regression scenario for `corporate + CIS Level 2`.

### Slice C: Heavy Middle Steps

1. Refactor Step 5 privacy/hardening first.
2. Refactor Step 6 extensions/websites second.
3. Refactor Step 2 network/proxy/trust third.

### Slice D: Remaining Guided Steps

1. Refactor Step 3 home.
2. Refactor Step 4 search.
3. Refactor Step 7 AI.
4. Normalize copy budgets across all cards.

## UX Budgets

Use these as regression targets after implementation:

- First step: primary setup path fits within 2 mobile screens.
- Any preset choice group: maximum 5 visible choices before disclosure or grouping.
- Any dynamic list: maximum 5-7 visible rows by default.
- Any local review: defaults to changed/attention rows.
- Final step: readiness and primary actions fit in the first desktop viewport.
- Desktop heavy content: no long list in a narrow side column.
- Guided mode: advanced-only sections are not visible inline unless the user opens advanced details.

## Open Decisions

1. Should step-local navigation be a sticky horizontal index, a compact sidebar, or inline chips?
2. Should long technical details open as drawers, accordions, or tab panels?
3. Should `corporate + CIS Level 2` become a named QA fixture/profile to make UX regression stable?
4. Should advanced-only preference sections be removed from guided DOM flow entirely, or remain hidden behind workspace scope and disclosure?
