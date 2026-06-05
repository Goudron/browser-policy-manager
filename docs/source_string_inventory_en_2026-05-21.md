# English Source String Inventory

Date: `2026-05-21`

Backlog item: `GLOC-101`

Normalized by backlog item: `GLOC-102`

Source catalog: `app/i18n/en.json`

Machine-readable snapshot: `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json`

The JSON snapshot is archived behind `docs/docs-index.md` so active documentation stays light.
Use this summary for routine review, and open the archived JSON only when raw key-level data is
needed.

## Snapshot

| Field | Value |
| --- | --- |
| Source locale | `en` |
| Source file | `app/i18n/en.json` |
| SHA-256 | `3e051517232f6d12deb907bda712d1017bab0d652d355f80cab76ea2f83fb5e3` |
| Key count | 2435 |
| Placeholder-bearing keys | 266 |
| HTML-sensitive keys | 1 |
| Technical-token keys | 596 |

English is the source product language. Translators and reviewers should treat this snapshot as the
stable source inventory for the first global locale expansion pass after the `GLOC-102` source-copy
normalization. If `app/i18n/en.json` changes before the new catalogs are created, regenerate the JSON
snapshot and review placeholder/identifier changes before translating.

## Coarse Key Groups

The complete ordered key list is stored in `key_order` inside the JSON snapshot.

| Group | Keys |
| --- | ---: |
| `actions_*` | 2 |
| `advanced_*` | 27 |
| `badge_*` | 3 |
| `clone_*` | 15 |
| `compare_*` | 43 |
| `compliance_*` | 8 |
| `confirm_*` | 4 |
| `conflict_*` | 11 |
| `create_*` | 2 |
| `description_*` | 2 |
| `details_*` | 2 |
| `dock_*` | 15 |
| `download_*` | 1 |
| `draft_*` | 1 |
| `editor_*` | 18 |
| `empty_*` | 2 |
| `error_*` | 22 |
| `flow_*` | 2 |
| `footer_*` | 5 |
| `guide_*` | 6 |
| `hard_*` | 2 |
| `helper_*` | 6 |
| `hero_*` | 5 |
| `import_*` | 6 |
| `importing_*` | 1 |
| `library_*` | 49 |
| `lifecycle_*` | 19 |
| `list_*` | 4 |
| `locale_*` | 10 |
| `meta_*` | 1 |
| `mode_*` | 1 |
| `name_*` | 4 |
| `nav_*` | 4 |
| `none_*` | 1 |
| `order_*` | 2 |
| `other profiles.*` | 14 |
| `overview_*` | 8 |
| `owner_*` | 3 |
| `policy_*` | 36 |
| `reset_*` | 2 |
| `resetting_*` | 1 |
| `schema_*` | 107 |
| `search_*` | 1 |
| `select_*` | 1 |
| `selection_*` | 3 |
| `settings_*` | 96 |
| `shell_*` | 39 |
| `shortcut_*` | 1 |
| `show_*` | 1 |
| `sidebar_*` | 2 |
| `signal_*` | 3 |
| `soft_*` | 2 |
| `sort_*` | 5 |
| `status_*` | 16 |
| `theme_*` | 6 |
| `validation_*` | 5 |
| `wizard_*` | 1759 |
| `workflow_*` | 2 |
| `workspace_*` | 16 |

## Placeholder Rules

Placeholders use brace-delimited identifiers such as `{count}`, `{name}`, and `{detail}`.
Target locales must preserve each placeholder token exactly, including braces and spelling. They may
move placeholders within the sentence when grammar requires it.

Unique placeholder tokens are stored in `placeholder_tokens`; complete per-key data is stored in
`placeholder_map` inside the JSON snapshot.

First 40 placeholder-bearing keys:

| Key | Placeholders |
| --- | --- |
| `profiles.settings_context_from_step` | `{step}` |
| `profiles.settings_context_more` | `{count}` |
| `profiles.clone_handoff_active` | `{name}` |
| `profiles.clone_handoff_item_compare` | `{name}` |
| `profiles.clone_meta` | `{name}` |
| `profiles.clone_name_pattern` | `{name}` |
| `profiles.clone_source_value` | `{name}` |
| `profiles.compare_current_draft_copy` | `{schema}` |
| `profiles.compare_current_saved_copy` | `{schema}` |
| `profiles.compare_guided_area_more` | `{items}`, `{remaining}` |
| `profiles.compare_guided_area_preview` | `{items}` |
| `profiles.compare_other_copy` | `{schema}` |
| `profiles.compliance_summary_exceptions` | `{count}` |
| `profiles.compliance_summary_level` | `{level}` |
| `profiles.compliance_summary_manual` | `{count}` |
| `profiles.compliance_summary_raised` | `{count}` |
| `profiles.compliance_summary_version` | `{version}` |
| `profiles.conflict_copy_created` | `{name}` |
| `profiles.conflict_copy_name` | `{name}`, `{revision}`, `{time}` |
| `profiles.conflict_revision_detail` | `{current}`, `{expected}` |
| `profiles.editor_mode_switched` | `{mode}` |
| `profiles.error_clone` | `{detail}` |
| `profiles.error_compare` | `{detail}` |
| `profiles.error_delete` | `{detail}` |
| `profiles.error_format` | `{detail}` |
| `profiles.error_import_firefox_policies` | `{detail}` |
| `profiles.error_import_firefox_policies_parse` | `{detail}` |
| `profiles.error_list` | `{detail}` |
| `profiles.error_load` | `{detail}` |
| `profiles.error_loading` | `{detail}` |
| `profiles.error_reset` | `{detail}` |
| `profiles.error_restore` | `{detail}` |
| `profiles.error_save` | `{detail}` |
| `profiles.error_schema_array` | `{detail}` |
| `profiles.error_schema_dictionary` | `{detail}` |
| `profiles.error_schema_policy` | `{detail}` |
| `profiles.error_validation_failed` | `{detail}` |
| `profiles.error_validation_result` | `{detail}` |
| `profiles.error_wizard_extensions` | `{detail}` |
| `profiles.error_wizard_network` | `{detail}` |

## HTML-Sensitive Fragments

These strings contain literal angle-bracket or entity-like fragments. Reviewers should treat them as
technical literals, not translatable markup.

| Key | Fragment |
| --- | --- |
| `profiles.wizard_proxy_passthrough_placeholder` | `<local>` |

## Technical Allowlist Patterns

The following token families are allowed to remain in English or technical form in localized
catalogs when they are brands, product names, identifiers, policy/preference keys, protocol names,
file formats, or literal values. Complete per-key matches are stored in `technical_token_map` inside
the JSON snapshot.

| Pattern family | Regex | Matching source keys |
| --- | --- | ---: |
| `brand_or_product` | `\b(?:Firefox|Mozilla|BPM|Browser Policy Manager|Microsoft|Windows|Bing|DuckDuckGo|AdGuard|uBlock|HTTPS Everywhere|Pocket)\b` | 283 |
| `file_or_format` | `\b(?:JSON|YAML|policies\.json|CSV)\b` | 65 |
| `schema_or_compliance` | `\b(?:ESR|Release|CIS|Benchmark|Level)\b` | 48 |
| `protocol_or_network` | `\b(?:DNS over HTTPS|HTTPS-Only|DoH|VPN|URL|URI|MIME|SPNEGO|NTLM|SAML|OIDC|IdP|LDAP|HTTP|HTTPS)\b` | 82 |
| `browser_surface` | `\b(?:Firefox Home|Add-ons Manager|Private Browsing|New Tab|Search Bar|Address Bar)\b` | 45 |
| `ai_surface` | `\b(?:AI|GenerativeAI|AIControls|Chatbot|LinkPreviews|TabGroups)\b` | 52 |
| `identifier_shape` | `\b(?:about:[\w-]+|[A-Za-z][\w-]*(?:\.[\w-]+)+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b` | 71 |
| `literal_value` | `\b(?:true|false|null|default|locked|user|clear)\b` | 98 |

## GLOC-102 Normalization Notes

- Replaced parenthetical plural forms such as `item(s)` with count-last wording.
- Aligned high-signal Mozilla terms around `Website translations`, `Private Browsing`, and
  `built-in VPN` while preserving policy/schema context where needed.
- Kept placeholders intact and moved count placeholders where that reduces grammar coupling for
  target locales.

## Review Notes

- Preserve Firefox policy keys, preference keys, schema identifiers, extension IDs, API paths, URLs,
  JSON/YAML values, file names, and protocol names unless a string explains them in prose.
- Keep Mozilla and Firefox product names aligned with Mozilla terminology for each target locale.
- Avoid translating `policies.json`, `JSON`, `YAML`, `ESR`, `Release`, `CIS`, and boolean literals
  when they refer to technical artifacts or values.
