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
