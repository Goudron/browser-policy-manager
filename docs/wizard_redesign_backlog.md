# Wizard Redesign Backlog

## Goal

Turn the Firefox policy wizard into a task-first flow for engineers, admins, and students.
The main wizard should focus on understandable browser outcomes, while JSON/YAML and schema coverage move into an JSON editor.

## Principles

- Organize steps by user intent, not by raw policy schema structure.
- Keep one main question per section, then reveal fine tuning only when needed.
- Remove raw JSON editing from the default flow.
- Keep advanced controls available, but separate from the primary task path.
- Preserve current policy serialization and validation behavior during the transition.

## Delivery Plan

### Phase 1: Navigation And Structure

- Introduce a data-driven wizard step catalog.
- Rename the current steps to more task-first labels.
- Update stepper and progress text to render from the catalog instead of hardcoded arrays.
- Keep the current policy editors wired as-is.

### Phase 2: Advanced View Separation

- Move Monaco JSON/YAML editing out of the main wizard path.
- Move schema-shell coverage and raw fallback review into an `JSON editor` view.
- Keep export and validation available from the review step.

### Phase 3: Network And Search Rewrite

- Split the current general step into clearer `Network` and `Browser basics` sections.
- Use progressive disclosure for proxy, DNS over HTTPS, and related enterprise controls.
- Keep search controls focused on default engine, managed engines, and address bar behavior.

### Phase 4: Accounts, Add-ons, Language, And AI

- Create focused sections for Mozilla account and Sync controls.
- Rework add-on policy into curated flows and clearer allow/block defaults.
- Add a dedicated `Language, translation, and AI` area for locales, translation, generative AI, visual search, and recommendation surfaces.

### Phase 5: Privacy And Review Rewrite

- Reframe privacy/security around outcomes instead of raw policy groups.
- Replace technical review counters with human-readable summaries.
- Keep technical warnings in an advanced review panel.

### Phase 6: Cleanup

- Remove obsolete wizard labels, hardcoded progress arrays, and dead DOM wiring.
- Tighten RU/EN copy for shorter, clearer guidance.
- Expand tests for step catalog rendering and advanced-view separation.

## First Implementation Slice

1. Add the backlog document.
2. Add a shared wizard step catalog for the current seven-step flow.
3. Update the stepper and progress text to read from that catalog.
4. Refresh RU/EN step labels to reflect a more task-first structure.
5. Keep the old panels in place so behavior stays stable while we refactor later slices.
