# Locale Picker Layout Audit

Backlog item: `GLOC-505`

Scope: Locale picker layout pass for the profile page header with all active picker options:
English, Русский, Deutsch, 简体中文, Français, Español.

Findings:

- desktop/mobile: clean
- The picker renders all six active localized catalogs with native names and stable locale metadata.
- The header control uses a single-column control shell, full-width select sizing, `min-width: 0`, and max-width bounds so native names cannot force horizontal overflow.
- Long surrounding header copy remains outside the select width calculation and can wrap independently.
- A zh-CN scenario-card fallback found during this pass was corrected because it appeared beside the picker flow in the guided setup surface.

Verification:

- Static layout contract: `tests/test_locale_picker_layout_contract.py`
- zh-CN visible fallback contract: `tests/test_zh_cn_script_layout_contract.py`
- Browser live rerun was not repeated in this pass because the current escalation window is unavailable; the earlier zh-CN pass had clean desktop/mobile captures, and this task is covered by DOM/CSS contracts.
