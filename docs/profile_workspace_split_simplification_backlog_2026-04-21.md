# Profile Workspace Split And Wizard Simplification Backlog

Date: `2026-04-21`

## Goal

Turn `/profiles` into a simple profile library and move profile editing into dedicated routes:

- library
- visual wizard
- advanced `policies.json` editor
- final review and export surfaces

The product should let administrators and security officers work with multiple profiles in parallel through normal browser tabs, while keeping the visual wizard focused on decisions, state, risks, and actions.

## Product Direction

The current `/profiles` page is doing too many jobs at once:

- profile library
- new-profile wizard
- existing-profile editor
- advanced document editor
- guided coverage explorer
- CIS explainability surface
- final validation/export surface

The next iteration should separate those responsibilities. Documentation will later explain product concepts, Firefox policies, CIS mapping, advanced-only settings, and per-policy behavior. The UI should not try to be the documentation.

## Core Principles

1. Library first.
   `/profiles` should be a profile library and command center, not a combined editor.

2. One profile per editor tab.
   Creating and editing should happen in dedicated routes so users can edit several profiles in different browser tabs.

3. Advanced is a separate destination.
   The advanced editor should open as its own route/tab, not as an embedded secondary UI inside the visual wizard.

4. Explicit saves.
   Policy editing should use explicit save actions. Avoid autosave in the first implementation.

5. Optimistic locking.
   Multiple tabs must not silently overwrite each other.

6. The wizard is not documentation.
   The wizard should show decisions, current state, real risks, and next actions. Long explanations, policy reference material, and CIS rationale should move to documentation or drilldown surfaces.

## Route Model

Target routes:

- `GET /profiles`
  Profile library.

- `GET /profiles/new`
  Visual wizard for a new profile draft.

- `GET /profiles/{id}/edit`
  Visual wizard for an existing profile.

- `GET /profiles/{id}/advanced`
  Full `policies.json` editor for an existing profile.

- Optional later route: `GET /profiles/{id}/review`
  Dedicated final review and export workspace if step 8 remains too heavy inside the visual wizard.

## Backlog Shape

The original 18 workstreams are too large to treat as one-iteration implementation tickets. This backlog splits them into five milestones and smaller tickets. Each ticket is intended to be small enough for one focused implementation pass, with the usual allowance for follow-up fixes found during QA.

## Workstream Mapping

- `WS-01` Route split.
- `WS-02` Library-first `/profiles`.
- `WS-03` Separate visual editor tabs.
- `WS-04` Separate advanced editor route.
- `WS-05` Revision-based save protection.
- `WS-06` Conflict resolution UX.
- `WS-07` Local tab draft state.
- `WS-08` Wizard information simplification.
- `WS-09` Step 1 simplification.
- `WS-10` Steps 2-7 simplification.
- `WS-11` Final review checklist.
- `WS-12` Compact CIS summary.
- `WS-13` Advanced terminology cleanup.
- `WS-14` Visible localization cleanup.
- `WS-15` Documentation link placeholders.
- `WS-16` Step navigation scroll behavior.
- `WS-17` Narrow viewport usability.
- `WS-18` End-to-end UX regression coverage.

## Milestone A: Routing Skeleton And Library Shell

Goal:

Make `/profiles` a library-first screen and create dedicated visual editor routes without changing the persistence model yet.

### `WS-A01` Add Web Route Skeletons

Status: Done

Scope:

- Add `GET /profiles/new`.
- Add `GET /profiles/{id}/edit`.
- Keep `/profiles` available.
- Do not move advanced editor yet.

Acceptance:

- `/profiles/new` returns the visual wizard shell in create mode.
- `/profiles/{id}/edit` returns the visual wizard shell in edit mode.
- Unknown profile IDs return the existing not-found behavior or a clear error state.
- Existing API endpoints are unchanged.

Implementation note:

- Added route skeletons for `/profiles/new` and `/profiles/{profile_id}/edit`.
- Added shared profile page context construction with `profiles_route_mode` and `editing_profile_id`.
- Added route metadata to the HTML body for follow-up frontend bootstrapping.
- Edit routes now verify the target profile exists, use the profile name in the page title, and return 404 for unknown profile IDs.
- Added smoke coverage for route registration and editor shell rendering.

### `WS-A02` Split Template Entry Points

Status: Done

Scope:

- Separate library page template from visual editor template.
- Keep shared partials where practical.
- Avoid duplicating large wizard markup unnecessarily.

Acceptance:

- `/profiles` no longer needs to include full wizard markup.
- `/profiles/new` and `/profiles/{id}/edit` render the wizard.
- Existing static assets still load on the editor routes.

Implementation note:

- Added `profiles_library.html` and `profiles_editor.html` as separate top-level template entry points.
- Moved the shared document chrome, static assets, and script includes into `profiles/_page_document.html`.
- Kept `profiles.html` as a compatibility wrapper around the shared document.
- Added `data-profiles-template-kind` to the body so follow-up frontend work can distinguish library and editor entry points.
- The library entry point intentionally still uses the existing full shell for runtime compatibility; replacing it with a library-only shell belongs to the next library shell/front-end split tasks.

### `WS-A03` Bootstrap Editor Mode From Route Context

Status: Done

Scope:

- Pass `mode=new` or `mode=edit` to frontend bootstrap.
- Pass profile ID for edit routes.
- Load the target profile on `/profiles/{id}/edit`.

Acceptance:

- New route starts with an empty draft.
- Edit route loads the target profile into wizard fields.
- The wizard context copy and save button reflect create versus edit mode.

Implementation note:

- Added runtime route-context parsing from `data-profiles-route-mode` and `data-editing-profile-id`.
- Editor startup now runs route-aware bootstrapping after Monaco initialization.
- `/profiles/{id}/edit` resets the initial draft state, then loads the target profile with `skipConfirm: true`.
- `/profiles` and `/profiles/new` keep the empty draft startup path and load the library list.
- Added static regression coverage for route-context bootstrap behavior.

### `WS-A04` Convert Library Actions To Route Links

Status: Done

Scope:

- `Create profile` links to `/profiles/new`.
- `Open profile` links to `/profiles/{id}/edit`.
- Preserve clone, compare, archive, and import actions where they currently exist.

Acceptance:

- Library actions use normal links where possible.
- Users can open editors in new browser tabs.
- Opening a profile from the library lands on the correct editor route.

Implementation notes:

- Added a library toolbar link to `/profiles/new`.
- Converted rendered profile title/open actions from JavaScript-only buttons to anchors targeting `/profiles/{id}/edit`.
- Kept compare and clone as in-page buttons.
- Added static regression coverage for the route-link contract.

### `WS-A05` Set Route-Specific Page Titles

Status: Done

Scope:

- Use clear titles for library, new editor, existing editor, and later advanced routes.

Acceptance:

- `/profiles` title identifies the library.
- `/profiles/new` title identifies a new profile draft.
- `/profiles/{id}/edit` title includes the profile name after load.

Implementation notes:

- `/profiles` now renders `Profile library — Browser Policy Manager`.
- `/profiles/new` now renders `New profile draft — Browser Policy Manager`.
- `/profiles/{id}/edit` now renders `{profile name} — Profile editor — Browser Policy Manager`.
- Added regression coverage for all three page-title contracts.

### `WS-A06` Add Route Smoke Tests

Status: Done

Scope:

- Add tests for the new route responses and key DOM contracts.

Acceptance:

- Tests cover `/profiles`, `/profiles/new`, and `/profiles/{id}/edit`.
- Tests assert that `/profiles` is library-first and editor routes contain the wizard.

Implementation notes:

- Added a route smoke test that exercises all three profile workspace routes through the test client.
- The library route contract now checks library metadata, search/list controls, create link, and compare panel.
- The editor route contract now checks editor template metadata, wizard shell, wizard schema selector, starter catalog, and command deck.
- The smoke test also asserts that only edit routes expose `data-editing-profile-id`.

## Milestone B: Advanced Editor As A Separate Destination

Goal:

Move the advanced `policies.json` editor out of the visual wizard and into its own route.

### `WS-B01` Add `/profiles/{id}/advanced` Route

Status: Done

Scope:

- Add route and template entry point for full `policies.json` editing.
- Load the target profile into the advanced editor.

Acceptance:

- Direct navigation opens the advanced editor for the profile.
- Unknown profile IDs produce a clear not-found or error state.
- Existing advanced editor save/validate/download behavior still works.

Implementation notes:

- Added `/profiles/{profile_id}/advanced` with profile lookup and 404 handling.
- Added `profiles_advanced.html` as a separate template entry point with `data-profiles-template-kind="advanced"`.
- Advanced route bootstrapping loads the profile, clears guided handoff context, and switches the workspace to advanced scope.
- Added route, template, title, DOM, and runtime bootstrap regression coverage.

### `WS-B02` Remove Default Inline Advanced Editor From Visual Wizard

Status: Done

Scope:

- Stop rendering the full advanced editor by default inside the visual wizard.
- Keep only targeted links/actions from guided steps.

Acceptance:

- Visual editor no longer shows the full JSON editor inline.
- Wizard steps still expose an `Advanced settings` or `Full policies.json` action where needed.

Implementation notes:

- The advanced content grid is hidden on visual editor routes and remains visible on `/profiles/{id}/advanced`.
- The guided advanced handoff now links to `/profiles/{id}/advanced` for saved profiles and is disabled for unsaved drafts.
- Visual-route advanced actions now route to the advanced destination instead of switching to the inline advanced scope.
- Visual routes ignore persisted `advanced` workspace scope and start in guided mode.
- Hidden compatibility elements remain in the visual route for now so the current wizard runtime can keep using the policy document as its backing state.

### `WS-B03` Add Return And Focus Query Support

Status: Done

Scope:

- Support `return=/profiles/{id}/edit`.
- Support `focus=<policy-or-path>` as a best-effort highlight/focus target.

Acceptance:

- Advanced editor shows `Return to visual editor` when `return` is supplied.
- Focus query can highlight or scroll to a known policy area.
- Unsupported focus targets fail quietly with no broken UI.

Implementation notes:

- Advanced route now accepts safe `/profiles...` return URLs and exposes them as a return link.
- Advanced route now accepts a bounded focus target and exposes it to runtime through body data attributes.
- Visual editor advanced links include `return=/profiles/{id}/edit`.
- Runtime resolves focus targets through known advanced aliases, settings targets, or element IDs, then reuses the existing reveal/highlight behavior.
- Unsupported focus targets are ignored without changing the visible UI.

### `WS-B04` Convert Guided Advanced Handoffs To Links

Status: Done

Scope:

- Replace embedded advanced toggles with route links.
- Preserve intent from search results and step-level handoffs.

Acceptance:

- Handoff from visual wizard opens `/profiles/{id}/advanced`.
- Links include `return` and useful `focus` values when available.
- New unsaved profiles handle advanced handoff gracefully, either by requiring save first or by opening a draft-safe advanced path.

Implementation notes:

- Guided AI and export advanced handoffs now render route links with focus targets instead of inline scope toggles.
- Runtime advanced route building now preserves both `return=/profiles/{id}/edit` and optional `focus`.
- Runtime derives focus intent from settings targets, advanced panels, editor panels, or element IDs when existing jump logic targets an advanced area.
- Remaining dynamic guided coverage and final-review actions route to advanced with a best-effort focus target instead of revealing inline advanced panels on visual routes.

### `WS-B05` Add Advanced Route Regression Tests

Status: Done

Scope:

- Test direct load, return link, focus parameter, and save/validate surface.

Acceptance:

- Tests fail if the advanced route does not load the requested profile.
- Tests fail if visual wizard still renders the full advanced editor by default.

Implementation notes:

- Added an explicit advanced route regression test for direct profile load, page title, route/template metadata, return/focus context, and save/validate/download surface.
- The same regression test asserts that the visual editor route keeps the advanced content grid hidden.
- Existing B01-B04 tests also cover missing profile 404s, template context, focused handoff links, and runtime bootstrap behavior.

## Milestone C: Safe Multi-Tab Editing

Goal:

Allow several editor tabs without silent overwrites.

### `WS-C01` Choose And Document The Revision Token

Status: Done

Scope:

- Decide whether to use a dedicated integer `revision` or strict `updated_at`.
- Document the chosen contract in this backlog or API docs.

Acceptance:

- The save conflict contract is explicit.
- Frontend and backend tickets can use the same token semantics.

Decision:

- Use a dedicated integer `revision` field, not strict `updated_at`, as the optimistic concurrency token.

Contract:

- Every profile has a server-owned integer `revision`.
- New profiles start at `revision = 1`.
- Every successful mutating operation increments `revision` exactly once:
  - profile update;
  - soft delete;
  - restore;
  - any future mutation that changes the saved profile record or its lifecycle state.
- Read endpoints return the latest `revision` in both list and detail responses.
- Update endpoints accept an expected revision token from the client.
- If the supplied expected revision differs from the current saved profile revision, the backend returns `409 Conflict` and does not mutate the profile.
- If no expected revision is supplied during the transition period, existing clients keep working. After visual and advanced editors are wired, UI saves must always send the expected revision.
- Conflict response should include enough context for UI recovery: current profile id, current revision, supplied revision, and a short conflict message.

Rationale:

- `updated_at` remains useful for sorting and display, but it is a weaker conflict token because timestamp precision and timezone behavior can vary by database and driver.
- A monotonic integer is easier for frontend state, tests, logs, and future multi-tab recovery actions.
- The integer token keeps conflict semantics independent from human-readable update timestamps.

### `WS-C02` Add Revision Token To Profile API Responses

Status: Done

Scope:

- Include the revision token in profile list and detail responses.
- Preserve existing response compatibility where possible.

Acceptance:

- List and detail API responses expose the token.
- Tests cover token presence and token changes after update.

Implementation notes:

- Added `revision` to the `Profile` ORM model with default/server default `1`.
- Added `revision` to `ProfileRead`, so profile create/list/detail/update responses expose the token.
- Extended SQLite legacy schema bridge and normalization migration to add `revision` to existing profile tables.
- Added regression expectations for API responses, legacy schema bridge, Alembic migration output, and sync DB helper upgrade.
- Token is exposed but not incremented yet; revision mutation and stale-save rejection are handled by the next tickets.

### `WS-C03` Add Conditional Update Support

Status: Done

Scope:

- Accept expected revision token on profile update.
- Reject stale updates with a conflict response.

Acceptance:

- Update with current revision succeeds.
- Update with stale revision returns conflict and does not mutate the profile.
- Tests cover both paths.

Implementation notes:

- `ProfileUpdate` now accepts optional `expected_revision`.
- Backend update rejects stale `expected_revision` with `409 Conflict` and does not call the service update path.
- Conflict detail includes message, profile id, current revision, and expected revision.
- Successful profile updates increment `revision` by one.
- Omitted `expected_revision` remains accepted during the transition period for existing frontend saves.
- Added service-core and API regression coverage for successful revision increments and stale conflict non-mutation.

### `WS-C04` Wire Revision Token Into Visual Editor Saves

Status: Done

Scope:

- Capture revision at editor load.
- Send expected revision on save.
- Store returned revision after successful save.

Acceptance:

- Visual editor saves include revision protection.
- Successful save refreshes the local revision token.
- Stale save shows a conflict state instead of claiming success.

Implementation notes:

- Existing profile saves now include `expected_revision` from the loaded profile.
- Successful saves keep refreshing the local profile state from the API response, including the returned `revision`.
- `PATCH` errors preserve HTTP status and structured detail for frontend conflict handling.
- `409 Conflict` now shows a dedicated stale-tab message and marks the validation/status preview as an error instead of reporting a generic save failure.
- Added static regression coverage for the visual save contract and locale coverage for the conflict message.

### `WS-C05` Wire Revision Token Into Advanced Editor Saves

Status: Done

Scope:

- Apply the same revision protection to advanced editor saves.

Acceptance:

- Advanced editor saves include revision protection.
- Stale advanced save does not overwrite a newer visual editor save.

Implementation notes:

- Advanced editor route already uses the shared `saveCurrent` implementation, so it now sends `expected_revision` through the `WS-C04` save contract.
- Advanced bootstrapping loads the current profile before switching to advanced scope, which captures the loaded `revision` token.
- The advanced save button and `Ctrl/Cmd+S` path both call the same protected save function.
- Added a dedicated advanced regression contract so future route or editor splitting cannot bypass revision protection.

### `WS-C06` Add Shared Conflict UI State

Status: Done

Scope:

- Add a common conflict message and action area.
- Expose `Reload latest`, `Save as copy`, and explicit `Overwrite anyway` if allowed.

Acceptance:

- Visual editor and advanced editor use consistent conflict language.
- Conflict actions are visible and keyboard reachable.
- `Overwrite anyway` copy is explicit about replacing newer changes.

Implementation notes:

- Added a shared conflict panel to the common command deck, so visual and advanced routes show the same conflict language and actions.
- `409 Conflict` now opens the panel with current/expected revision context when available.
- `Reload latest` loads the latest saved profile intentionally, bypassing the dirty-discard prompt because the user has chosen that recovery action.
- `Overwrite anyway` asks for explicit confirmation and then retries the save without the expected revision token, replacing the newer saved version.
- `Save as copy` is visible and keyboard reachable as the next recovery path; `WS-C07` wires it to create the copy.
- Added static regression coverage for the shared conflict UI, DOM wiring, and overwrite retry path.

### `WS-C07` Implement Save As Copy From Conflict

Status: Done

Scope:

- Create a new profile from the local draft after conflict.
- Preserve user-entered changes.

Acceptance:

- `Save as copy` creates a new profile.
- The new profile name clearly indicates it is a copy or prompts for a new name.
- The original profile remains unchanged.

Implementation notes:

- `Save as copy` now creates a new profile from the current local editor content instead of touching the conflicted original.
- The generated copy name includes the source name, stale revision, and timestamp so it is visibly a conflict copy and avoids ordinary duplicate-name collisions.
- The new profile is loaded after creation, which refreshes the local revision token and clears the conflict panel.
- Original conflicted profile remains unchanged because the copy path uses `POST /api/profiles`, not the stale `PATCH`.
- Added static regression coverage for the conflict copy creation path and locale coverage for copy naming/status text.

### `WS-C08` Add Unsaved Draft Leave Protection

Status: Done

Scope:

- Warn before reload/navigation when local draft is dirty.
- Apply to visual and advanced editors.

Acceptance:

- Dirty editors warn before accidental tab close or route navigation.
- Clean editors do not warn.

Implementation notes:

- Existing `beforeunload` protection remains the browser-level guard for tab close and hard reload.
- Added a shared guarded-link handler for internal `/profiles` route links, including library-to-editor, create, visual-to-advanced, and advanced return links.
- The guard ignores local hash jumps, external links, and links that intentionally open in a new browsing context.
- Programmatic visual-to-advanced route navigation now uses the same dirty confirmation before `window.location.assign`.
- Added regression coverage for internal route-link guarding and the advanced route handoff confirmation.

## Milestone D: Wizard Simplification

Goal:

Make the visual editor a decision-first wizard instead of a documentation and coverage surface.

### `WS-D01` Define The Simplified Wizard Component Contract

Status: Done

Scope:

- Define the shared visual grammar:
  - title
  - one-line purpose
  - primary choice
  - active state
  - real warnings
  - advanced link

Acceptance:

- The contract is documented in this backlog or a frontend note.
- Future step tickets can implement against the same structure.

Simplified wizard component contract:

Every default-visible wizard section should answer one admin question and use the same grammar:

1. **Title**
   - Names the job in admin language, not the implementation object.
   - Good: `Proxy routing`, `Managed search`, `Extension install posture`.
   - Avoid: `Proxy policy coverage`, `Search schema fields`, `ExtensionSettings technical controls`.

2. **One-line purpose**
   - One sentence explaining when the section matters.
   - No documentation paragraphs, benchmark explanations, schema inventories, or policy reference text in the default path.

3. **Primary choice**
   - The first interactive control in the section.
   - Prefer presets, segmented controls, toggles, or short forms that match the decision.
   - A section may have supporting fields, but only after the primary choice is visible.

4. **Active state**
   - A compact state line/card showing what is currently configured.
   - It should summarize the resulting posture, not list every policy key.
   - Empty/default state must be explicit.

5. **Real warnings**
   - Show warnings only for actual risk, conflict, invalid input, unsupported schema, or manual review.
   - Do not use warnings for normal explanatory text.
   - CIS exceptions and conflicts count as real warnings; generic “this maps to N settings” does not.

6. **Advanced link**
   - One deliberate handoff when lower-level control is needed.
   - Link to `/profiles/{id}/advanced` with a focus target when the profile is saved.
   - For unsaved drafts, the action should say that saving is required first.
   - Advanced-only content should not be expanded inline by default.

Default-visible section shape:

- Header: `Title` + one-line purpose.
- Decision: one primary choice group or compact form.
- State: current active state and meaningful warnings.
- Optional fine tuning: collapsed unless already configured or invalid.
- Advanced: one deliberate link or disabled save-first action.

What must leave the default path:

- Settings maps and guided coverage maps.
- `remaining N of M` coverage language.
- Schema-shell inventories.
- Long policy reference copy.
- Raw-policy fallback lists.
- Advanced-only controls that are not part of the ordinary admin decision.

What can remain reachable:

- Search index targets.
- Collapsed fine tuning for already configured values.
- Focused advanced links.
- Future documentation links to product/policy docs.
- Final review summaries that show changed, invalid, or attention-needed items.

Completion checklist for `WS-D02` through `WS-D13`:

- The first viewport of the step starts with the main decision, not reference material.
- A sysadmin can identify the next action without opening documentation.
- Existing configured values are still visible somewhere purposeful.
- Advanced controls remain reachable without being the default reading path.
- Tests or static contracts are updated when visible blocks move.

### `WS-D02` Remove Default Coverage Blocks From Wizard Steps

Status: Done

Scope:

- Remove or hide default guided coverage summaries from steps 1-8.
- Keep targeted advanced links where useful.

Acceptance:

- Steps no longer lead with `remaining N of M areas` style copy.
- Advanced coverage remains reachable only through deliberate links or documentation.

Implementation notes:

- Removed the default-visible guided coverage block from the shared `render_wizard_schema_shell` macro, so steps no longer render `wizard-guided-coverage-step-*` cards ahead of the main decisions.
- Stopped runtime rendering for guided coverage summaries in the schema-shell renderer.
- Kept the advanced schema shell nodes and IDs intact for saved-profile advanced route focus, direct advanced work, and technical fallback rendering.
- Existing visual-to-advanced links and route focus behavior remain the deliberate path to coverage details.
- Added regression coverage that fails if guided coverage blocks return to the default wizard path.

### `WS-D03` Remove Settings Maps From The Default Path

Status: Done

Scope:

- Remove settings map blocks from visible step bodies.
- Keep search indexing and future documentation targets intact.

Acceptance:

- The main wizard path does not render settings maps.
- Search still finds settings and can route to the relevant step/control.

Implementation notes:

- Removed `render_settings_reference` and its visible settings-map/doc navigation macros from the default wizard templates.
- Removed settings map calls from the general, home, search, sync, and privacy wizard steps, including preference subsection maps.
- Removed legacy hidden markers that kept old map IDs present in the rendered page.
- Kept global settings search, embedded settings catalog data, and `data-settings-target` anchors on real controls so search can still route users to the relevant step/control.
- Added regression coverage that fails if map/doc navigation blocks return to the default wizard path.

### `WS-D04` Simplify Step 1 Starting Point

Status: Done

Scope:

- Keep profile name, schema, scenario, and CIS layer.
- Make scenario imply baseline by default.
- Move manual baseline override to a compact optional control if still needed.

Acceptance:

- `corporate workstation + CIS Level 2` is selectable without opening extra preset sections.
- Multiple competing baseline grids are gone from the default view.

Implementation notes:

- Changed the setup step default from targeted edits/blank to corporate scenario/basic corporate baseline.
- Removed the visible impact/summary panel from the default setup path so the first step now focuses on name, schema, scenario, and CIS layer.
- Kept manual baseline overrides in the existing collapsed disclosure and moved secondary start options into that optional area.
- Added explicit `aria-pressed` defaults for scenario, baseline, and CIS preset buttons.
- Strengthened the active preset visual state with a clearer border/background/inset marker.
- Added regression coverage for simplified setup defaults, hidden baseline override, and active preset state wiring.

### `WS-D05` Simplify Step 2 Network And Browser Basics

Status: Done

Scope:

- Reduce step 2 to core decisions and active settings.
- Move reference and advanced-only copy out of the default path.

Acceptance:

- Proxy, updates, downloads, trust, and authentication remain configurable.
- The first viewport shows actionable choices, not reference material.

Implementation notes:

- Removed the step 2 schema shell and local step map from the default network/browser basics path.
- Removed upkeep/trust workflow explainer cards and their now-unused DOM/runtime render hooks.
- Removed the general advanced preferences handoff block from step 2; preference editing remains available through search/advanced routes instead of the default step body.
- Kept actionable controls for browser basics, update/download presets, proxy presets/manual fields, DNS/Windows SSO, authentication, certificates, and review jump targets.
- Strengthened the applied preset visual state so selected preset buttons are visibly active in light and dark themes.
- Added regression coverage for the simplified step 2 contract.

### `WS-D06` Simplify Step 3 Home And Startup

Status: Done

Scope:

- Reduce home/startup to homepage, startup behavior, new tab, and active state.

Acceptance:

- Corporate homepage scenario remains easy to inspect and edit.
- Long reference/support blocks are absent from the default path.

Implementation notes:

- Removed the step 3 schema shell from the default home/startup path.
- Removed the home workflow/review summary block and its now-unused DOM/runtime render hook.
- Removed the home advanced preferences block from the step body; preference editing remains outside the simplified default path.
- Kept homepage presets, shared homepage presets, homepage URL/startup fields, new tab/first-run controls, Firefox Home presets, active section statuses, and Firefox Home fine tuning.
- Added regression coverage for the simplified step 3 contract and active preset-state wiring.

### `WS-D07` Simplify Step 4 Search And Navigation

Status: Done

Scope:

- Reduce search to default engine, suggestions, managed engines, and active state.

Acceptance:

- Search presets and custom engines remain usable.
- Technical search-engine details stay hidden until needed.

Implementation notes:

- Removed the step 4 schema shell and local index from the default search path.
- Removed the search workflow card, review summary, and search advanced-preferences handoff from the step body.
- Kept default search presets, default-engine input, managed search engine presets/custom engines, Firefox Suggest presets, active section statuses, and fine tuning.
- Kept technical custom-engine fields behind the existing details disclosure.
- Added regression coverage for the simplified step 4 contract and active preset-state wiring.

### `WS-D08` Simplify Step 5 Privacy And Protection

Status: Done

Scope:

- Reduce privacy to hardening level, cleanup, permissions/cookies, and warnings.

Acceptance:

- CIS Level 2 privacy posture is visible as active state.
- Manual-review privacy items surface as warnings, not long reference lists.

Implementation notes:

- Removed the step 5 schema shell, hardening impact summary, governance checklist, next-action shortcuts, and privacy advanced-preferences block from the default path.
- Collapsed the visual step around hardening posture, cleanup posture, and permissions/cookies controls.
- Removed separate privacy/lockdown submenus from the visual flow; those settings remain represented through the hardening posture and final warning summary.
- Kept privacy warning/review counters for user data, cleanup, permissions, and cookies.
- Kept active preset-state wiring for hardening, cleanup, and site-data presets.
- Added regression coverage for the simplified step 5 contract.

### `WS-D09` Simplify Step 6 Accounts, Language, Extensions, Sites

Status: Done

Scope:

- Keep the mixed feature step compact with clear subsections.
- Remove long workflow guidance from the default path.

Acceptance:

- Mozilla account, language, extensions, bookmarks, and site-access controls remain reachable.
- The step does not become a wall of cards.

Implementation notes:

- Kept step 6 focused on accounts, language/translation, extension posture, bookmark handoff, and website access decisions.
- Removed stale default-path workflow and summary dependencies for language governance, extension governance, bookmark review summaries, and website governance.
- Preserved compact active-state rows, fine-tuning toggles, curated extension controls, bookmark advanced handoff, website filter controls, and handler fine tuning.
- Removed runtime calls to deleted workflow panels so step 6 rendering no longer depends on absent DOM globals.
- Added regression coverage for the compact step 6 contract.

### `WS-D10` Simplify Step 7 AI And Smart Features

Status: Done

Goal:

- Make the standard AI wizard step compact while exposing every AI-related policy available in the current Firefox 149 template.

Scope:

- Keep supported AI controls, unsupported-schema state, and provider handoff compact.

Acceptance:

- AI controls or unsupported state are immediately understandable.
- Provider/model handoff goes to advanced route or docs instead of inline detail.

Implementation notes:

- Moved `GenerativeAI` and `VisualSearchEnabled` into the main standard AI step so Release 149 exposes all currently supported AI policy controls without opening the advanced shell.
- Removed the old AI governance summary rows and hidden smart-surfaces fine-tuning panel from step 7.
- Kept provider/model handling as a compact advanced handoff because the current Firefox 149 policy template does not expose stable provider or model choice fields.
- Updated AI copy and tests to describe the current Firefox 149 contract rather than future provider/model controls.

### `WS-D11` Redesign Step 8 As Final Checklist

Status: Done

Goal:

- Make the final wizard step a compact handoff checklist where save, validate, and policies.json download are visible first.

Scope:

- Lead with save, validate, and download.
- Show compact readiness checklist.

Acceptance:

- Save, validate, and download are visible without scrolling on desktop.
- Final status can be read quickly.

Implementation notes:

- Reworked the step 8 primary card into a final checklist with readiness state, save/validate/download actions, download hint, advanced handoff, next actions, ready items, and technical alert badges in the first section.
- Removed the separate follow-up card so the primary export decision no longer competes with secondary handoff content.
- Kept outcome, guided summary, CIS exceptions, shareable summary, compatibility, schema shell, and advanced-only drilldown below the first handoff area.
- Updated desktop/mobile CSS and regression tokens for the new final checklist contract.

### `WS-D12` Add Compact CIS Final Summary

Status: Done

Goal:

- Add a compact final-step CIS summary that answers what the selected CIS overlay changed, already satisfied, kept from the baseline, and left for manual review.

Scope:

- Show applied, already satisfied, kept from baseline, and manual-review counts.
- Keep detailed reasons behind a focused drilldown or future docs link.

Acceptance:

- `corporate + CIS Level 2` has a clear CIS summary.
- Full CIS decision list is not rendered by default.

Implementation notes:

- Added a final-step CIS summary block with aggregate counts for applied CIS decisions, already satisfied decisions, baseline-kept decisions, and manual-review decisions.
- Rendered the summary from existing CIS merge metadata (`summary`/`decisions`) without expanding the full decision list by default.
- Kept detailed CIS exceptions behind the existing focused reasons/details UI.
- Updated DOM wiring, CSS, i18n, and regression coverage for the compact summary.

### `WS-D13` Rename Advanced Concepts In UI Copy

Status: Done

Scope:

- Replace `Техдокумент` primary labels.
- Normalize English and Russian labels for advanced/full JSON/export semantics.

Acceptance:

- UI uses `Full policies.json`, `Advanced editor`, `Полный policies.json`, or `Расширенный редактор`.
- Export copy clearly distinguishes included, not included, and manual-review states.

Implementation notes:

- Replaced the older `Advanced document` / `Техдокумент` labels in visible UI copy with `Advanced editor` / `Расширенный редактор`.
- Updated advanced handoff, route context, export review, and guidance copy to use `Full policies.json` / `Полный policies.json` when the full document itself is the destination.
- Updated README and changelog references so repository documentation matches the product terminology.

### `WS-D14` Add Documentation Link Placeholders

Status: Done

Scope:

- Add unobtrusive links for future docs.
- Do not reintroduce long explanatory copy.

Acceptance:

- Links are stable and optional.
- Missing docs do not break the workflow.

Implementation notes:

- Added a shared `render_doc_placeholder` macro for disabled, hash-only documentation placeholders.
- Added placeholders for the advanced editor guide, lower-level policy reference, and final-step boundary notes.
- Kept the placeholders short and visually secondary so the wizard remains decision-first while future docs have stable attachment points.

## Milestone E: Polish, Localization, Responsive QA, And Regression Coverage

Goal:

Make the split workspace feel product-ready and protect the new workflows with tests.

### `WS-E01` Complete Visible Localization Cleanup

Status: Done

Scope:

- Replace generic visible English strings in Russian UI.
- Keep raw Firefox policy names only as identifiers.

Acceptance:

- Russian UI has no visible generic labels such as `Show details`, `BLOCK`, or `EXCEPTIONS`.
- Search remains useful with both localized terms and raw policy names.

Implementation notes:

- Kept visible Russian disclosure and review labels localized, while leaving raw Firefox identifiers available only where they function as keys or search targets.
- Finished the advanced-workflow RU terminology cleanup so user-facing copy no longer mixes in the earlier `Техдокумент` wording.

### `WS-E02` Fix Step Navigation Scroll Behavior

Status: Done

Scope:

- Scroll to the top of the active step on normal step navigation.
- Preserve targeted focus from search and advanced handoff.

Acceptance:

- Stepper clicks open the selected step at its beginning.
- Search result clicks still focus exact targets.

Implementation notes:

- Added a dedicated normal-navigation helper for stepper, Previous, and Next actions.
- Kept targeted jumps on the existing reveal paths, so settings search, final-review jumps, and advanced handoff focus still scroll to the exact target control.

### `WS-E03` Polish Library Narrow Viewport

Status: Done

Scope:

- Make `/profiles` usable at `390x844`.
- Prioritize search, create/import actions, and profile cards.

Acceptance:

- No primary library action requires horizontal scrolling.
- Profile cards remain scannable on narrow screens.

Implementation notes:

- Added a `max-width: 560px` library polish layer for the `390x844` class of viewports.
- Search, refresh, create, and import actions now stack as full-width controls on narrow screens.
- Profile rows gain compact mobile labels for schema, updated date, and status while keeping action buttons full-width and avoiding horizontal overflow.

### `WS-E04` Polish Visual Editor Narrow Viewport

Status: Done

Scope:

- Make `/profiles/{id}/edit` usable for emergency edits at `390x844`.
- Reduce card walls and horizontal overflow.

Acceptance:

- Step navigation, save, validate, and advanced link remain reachable.
- Text does not overflow controls.

Implementation notes:

- Added a narrow-viewport visual-editor layer for command deck, wizard header/search, stepper, active panels, and wizard navigation.
- Save, validate, conflict actions, and lifecycle/risk controls stack as full-width buttons on small screens.
- The advanced handoff panel and link now collapse to a single column with wrapping copy and a full-width action.

### `WS-E05` Add Create And Export Browser Regression

Status: Done

Scope:

- Cover create `corporate workstation + CIS Level 2`.
- Save and download `policies.json`.

Acceptance:

- Test fails if the corporate + CIS L2 flow cannot create and export a profile.

Implementation notes:

- Added a browser-facing smoke regression for the `/profiles/new` create path, corporate scenario defaults, CIS Level 2 control, save actions, and Firefox `policies.json` export link wiring.
- The test creates a real `basic_corporate + cis_l2` release profile through the public API using the same merged catalog payload exposed to the wizard.
- The test validates the generated document, saves the profile with CIS metadata, and downloads pretty `policies.json` with attachment headers.

### `WS-E06` Add Library-To-Editor Browser Regression

Status: Done

Scope:

- Create a profile through API or UI.
- Open it from `/profiles`.
- Edit a guided field and save.

Acceptance:

- Test fails if library route links do not load the correct editor profile.

Implementation notes:

- Added a browser-facing smoke regression for the `/profiles` library shell, rendered route-link contract, `/profiles/{id}/edit` route context, and edit-mode title.
- The test creates a profile, verifies the library API can find it, and asserts rendered library rows use `/profiles/${profile.id}/edit` instead of in-page load buttons.
- The test simulates a guided homepage edit by updating the same `Homepage.URL` field the wizard writes, saves with the revision token, and verifies the Firefox `policies.json` export reflects the saved change.

### `WS-E07` Add Visual-And-Advanced Same Profile Regression

Status: Done

Scope:

- Open visual editor and advanced editor routes for the same profile.
- Save from each route in the non-conflict case.

Acceptance:

- Test fails if either route cannot load or save the profile.

Implementation notes:

- Added a browser-facing smoke regression that opens the same saved profile through `/profiles/{id}/edit` and `/profiles/{id}/advanced`.
- The test verifies shared route bootstrap, advanced scope activation, shared `saveCurrent` wiring, and revision-token save payload construction.
- The test saves a visual-route homepage edit, then saves an advanced-route policy edit with the refreshed revision and verifies the combined Firefox `policies.json` export.

### `WS-E08` Add Stale Save Conflict Regression

Status: Done

Scope:

- Simulate two editor tabs with the same initial revision.
- Save tab A.
- Attempt stale save from tab B.

Acceptance:

- Test fails if stale save overwrites silently.
- Test asserts conflict response and conflict UI state.

Implementation notes:

- Added a browser-facing stale-save regression that loads the same profile as tab A and tab B with the same initial revision.
- The test saves tab A, verifies tab B receives structured `409 Conflict`, and confirms tab B's stale Homepage/policy changes do not mutate the saved profile or exported Firefox `policies.json`.
- The test also asserts the shared conflict UI contract: alert panel, reload/latest action, save-as-copy action, overwrite action, `409` detection, structured error detail preservation, and conflict revision detail rendering.

### `WS-E09` Add Save-As-Copy Regression

Status: Done

Scope:

- Trigger stale conflict.
- Use `Save as copy`.

Acceptance:

- Test fails if the local draft is lost.
- Test asserts original profile remains unchanged and a new profile exists.

Implementation notes:

- Added a browser-facing save-as-copy regression that starts from the same stale-conflict setup as `WS-E08`.
- The test verifies the shared `saveConflictAsCopy` UI wiring creates a new profile via `POST /api/profiles`, loads that new profile, clears conflict state, and reports the copy-created status.
- The test confirms the original profile keeps tab A's saved Homepage, while the new copy preserves tab B's local Homepage/policy draft and exports those values through Firefox `policies.json`.

## Recommended Implementation Order

1. Milestone A: routing skeleton and library shell.
2. Milestone B: advanced editor as a separate destination.
3. Milestone C: safe multi-tab editing.
4. Milestone D: wizard simplification.
5. Milestone E: polish, localization, responsive QA, and regression coverage.

## Definition Of Done

- `/profiles` is a focused library, not a combined editor.
- New and existing profiles open in dedicated visual editor routes.
- Advanced editing opens in a dedicated `policies.json` route.
- Multiple profiles can be edited in separate browser tabs.
- Visual editor and advanced editor use explicit saves and detect stale revisions.
- Stale saves do not silently overwrite newer profile versions.
- The visual wizard is substantially shorter and shows only decisions, state, risks, and actions by default.
- Final review clearly answers whether the profile is saved, valid, CIS-reviewed, and ready to export.
- `corporate workstation + CIS Level 2` remains fully createable, editable, validatable, and exportable.
- Browser-level regression coverage protects the main create/edit/advanced/conflict/export workflows.
