# English Source Copy Normalization

Date: `2026-05-21`

Backlog item: `GLOC-102`

Source catalog: `app/i18n/en.json`

Updated inventory summary: `docs/source_string_inventory_en_2026-05-21.md`

Archived raw snapshot: `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`

## Scope

This pass normalized English source strings that would otherwise create avoidable ambiguity for
German, Simplified Chinese, French, and Spanish translation work. It does not add new UI concepts or
change locale keys.

## Changes

| Area | Normalization | Reason |
|---|---|---|
| Mozilla terminology | Standardized visible labels around `Website translations`, `Private Browsing`, and `built-in VPN`. | Matches the English Mozilla/SUMO terminology check closely enough for translators to start from consistent source terms. |
| Count placeholders | Replaced parenthetical plural forms such as `item(s)`, `conflict(s)`, and `decision(s)` with count-last wording. | Avoids English-specific plural shortcuts and lets target locales reorder the count naturally. |
| Context words | Replaced several ambiguous `here` references in language strings with `in this step`. | Makes the UI location explicit without relying on English deictic wording. |
| Policy terminology | Kept `IP protection policy controls` in explanatory copy while using `built-in VPN` for visible user-facing labels. | Preserves schema/policy meaning without overloading the primary UI label. |

## Follow-Up

- New locale catalogs should translate from the updated inventory snapshot, not the earlier
  pre-normalization SHA.
- `GLOC-103` should promote these normalized source terms into the shared terminology sheet.
