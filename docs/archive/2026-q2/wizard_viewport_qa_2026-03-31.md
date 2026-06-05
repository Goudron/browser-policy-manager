# Wizard Viewport QA Notes

Date: `2026-03-31`

## Tested viewports

- `390x844`
- `412x915`
- `1366x768`

## Method

- Ran the local app in FastAPI/uvicorn outside the sandbox on `127.0.0.1:8766`.
- Used headless Chromium with DevTools automation and cache-disabled reloads.
- Checked the main profiles page and the guided wizard entry area, then navigated into guided steps where possible.

## Fixed during QA

1. Hidden panels were not reliably collapsing.
   Cause:
   Author styles such as `display: grid` were overriding the browser default behavior for `hidden`.
   Fix:
   Added `[hidden] { display: none !important; }` in [app/static/profiles.css](/home/valery/Projects/browser-policy-manager/app/static/profiles.css).
   Impact:
   Fine-tuning and nested details panels now collapse consistently again.

## Remaining findings

1. The page still lands above the wizard on both mobile and small desktop.
   At `390x844`, `412x915`, and `1366x768`, the first screen is dominated by the hero and workspace/action area.
   Guided setup starts below the fold, so the user does not immediately arrive in the wizard they came to use.

2. The mobile rhythm before the first actionable wizard control is still long.
   On narrow screens, the stepper cards and explanatory blocks take a lot of vertical space before the first interactive field inside the current step.
   This is much better than before structurally, but still feels heavy in the first screen or two.

3. Step sections with `Firefox Settings areas` and `Controls in this area` still create a tall preamble on mobile.
   The chips are readable and do not overflow, but they add noticeable height before the primary decision controls begin.
   This is especially visible on steps like `Search` and `Accounts / add-ons / features`.

## Positive findings

1. No meaningful horizontal overflow was reproduced at the tested widths after the `hidden` fix.
   The only out-of-bounds nodes observed in automation were Monaco accessibility/status helper elements that live off-screen intentionally.

2. Button stacking and card wrapping hold up well at the tested widths.
   Primary actions, ghost buttons, and section cards remain readable and tappable.

3. The redesigned stepper and card layout survive `1366x768` without collapsing into cramped multi-column noise.
   The main issue there is vertical prioritization, not broken layout.

## Follow-up pass

Date: `2026-04-03`

### Retested viewports

- `390x844`
- `412x915`
- `1366x768`

### Method

- Ran the local app in uvicorn on `127.0.0.1:8766`.
- Captured fresh headless Chromium screenshots for the current `/profiles` page.
- Compared the first-screen landing behavior before and after a layout change that moved the command deck below guided setup.

### Fixed during follow-up

1. Guided setup no longer starts below the fold on the tested mobile and small-desktop widths.
   Cause:
   The command deck sat above the wizard in the primary page flow, so the first screen was consumed by global actions before the user reached the guided setup they came to use.
   Fix:
   Moved the command deck below the wizard in [app/templates/profiles/_page_shell.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_shell.html) by extracting it into [app/templates/profiles/_page_command_deck.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_command_deck.html).
   Impact:
   At `390x844`, `412x915`, and `1366x768`, the guided wizard title, search, and/or first step controls now appear on the first screen.

### Remaining findings after follow-up

1. Mobile still arrives on a dense first screen, even though it now lands in the right place.
   The wizard is visible immediately, which is the important win, but the top toolbar plus locale/theme controls still take a noticeable amount of vertical space before the first step body breathes.

2. The first stepper row is now visible on mobile, but it remains horizontally scrollable and visually heavy.
   This is acceptable for now and much better than hiding the wizard completely, but it is still a candidate for future rhythm polish if we want an even faster first interaction.

### Positive findings from follow-up

1. The most important landing issue is resolved.
   Guided setup is now clearly the primary path on both mobile and `1366x768`, instead of being pushed behind the command deck.

2. The new ordering does not introduce obvious layout regressions.
   Header, wizard, command deck, and workspace still stack cleanly, and the command deck remains easy to find just below the guided flow.

## Regression Pack

Date: `2026-04-04`

To reduce the chance of silently regressing the landing behavior again, the project now treats the following as viewport regression invariants:

1. `#wizard-panel` must appear in the primary page flow before `#command-deck`.
   This preserves the guided-first landing order that was restored in the `2026-04-03` follow-up.

2. The wizard search and the first guided step must appear before the command deck in rendered HTML.
   This is a structural proxy for the practical UX rule that guided setup should remain the first meaningful interactive area on narrow and small-desktop screens.

3. Mobile and narrow-screen QA still uses the same reference widths:
   - `390x844`
   - `412x915`
   - `1366x768`

4. Static regression checks intentionally protect layout order and guided-first visibility assumptions, not pixel-perfect screenshots.
   This keeps the regression pack stable while still defending the highest-value viewport decisions from the redesign and post-roadmap polish work.
