# CJK Font Fallback Audit

Backlog item: `GLOC-507`

Scope: CJK font and fallback check for Simplified Chinese (`zh-CN`) in the profile UI.

Findings:

- The UI previously relied on the generic `sans-serif` fallback after `"Avenir Next"`, `"Segoe UI Variable"`, and `"Helvetica Neue"`.
- On the audit host, `fc-match sans-serif:lang=zh-cn` resolves to `Noto Sans CJK SC`, so Simplified Chinese did not depend on a missing glyph path in the local Linux environment.
- The CSS now makes the expected CJK fallback explicit: `Noto Sans CJK SC` for Linux, `Microsoft YaHei` for Windows, and `PingFang SC` for macOS.
- Monospace areas now include `Noto Sans Mono CJK SC` and `Noto Sans CJK SC` after the Latin monospace stack so policy/value panes can render Chinese content without tofu boxes.
- Existing component line heights for body copy, cards, table cells, and review panels remain at or above the previously audited readable values, and the rendered `zh-CN` page exposes `lang="zh-CN"` so browser font selection can use language-aware fallback.

Verification:

- Static contract: `tests/test_cjk_font_fallback_contract.py`
- Local fontconfig evidence:
  - `fc-match sans-serif:lang=zh-cn` -> `Noto Sans CJK SC`
  - `fc-match "Noto Sans Mono CJK SC":lang=zh-cn` -> `Noto Sans Mono CJK SC`
