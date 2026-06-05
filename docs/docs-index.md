# BPM 0.8.5 Documentation Index

Updated: 2026-06-03

This index classifies every maintained documentation file under `docs/` so
refactoring work can separate active contracts from historical audits and
cleanup candidates.

Statuses:

- `active` - current contract, architecture note, or maintained reference.
- `runbook` - repeatable operating procedure.
- `audit` - point-in-time analysis kept for traceability.
- `backlog` - planned or proposed work.
- `archive` - historical material that should not steer new implementation
  without a fresh review.

Ignored local artifact groups:

- `docs/screenshots/` - local QA captures and HTML dumps; intentionally not
  tracked in the maintained documentation index.

| File | Status | Purpose |
| --- | --- | --- |
| [docs/docs-index.md](docs-index.md) | active | Maintained map of documentation ownership and cleanup state. |
| [docs/docs-manifest.json](docs-manifest.json) | active | Machine-readable documentation contracts for finished backlog items. |
| [docs/architecture/current-system-map.md](architecture/current-system-map.md) | active | Current backend, frontend, data, schema, and test-system map for refactoring. |
| [docs/architecture/pytest-xdist-isolation-audit.md](architecture/pytest-xdist-isolation-audit.md) | audit | Current pytest-xdist isolation blocker map for BPM 0.8.5. |
| [docs/architecture/pytest-xdist-readiness.md](architecture/pytest-xdist-readiness.md) | active | Maintained decision record for pytest-xdist readiness and adoption gates. |
| [docs/architecture/refactoring-acceptance-rules.md](architecture/refactoring-acceptance-rules.md) | active | Shared acceptance contract for behavior-preserving refactors. |
| [docs/archive/2026-q2/all_settings_search_filter_i18n_audit_2026-05-30.md](archive/2026-q2/all_settings_search_filter_i18n_audit_2026-05-30.md) | audit | Point-in-time i18n audit for all-settings search and filter UI. |
| [docs/archive/2026-q2/browser_datetime_i18n_audit_2026-05-30.md](archive/2026-q2/browser_datetime_i18n_audit_2026-05-30.md) | audit | Point-in-time datetime localization audit. |
| [docs/bpm_0_8_5_refactoring_backlog_2026-06-01.md](bpm_0_8_5_refactoring_backlog_2026-06-01.md) | backlog | Approved BPM 0.8.5 refactoring and optimization backlog. |
| [docs/archive/2026-q2/chromium_locale_smoke_matrix_audit_2026-05-30.md](archive/2026-q2/chromium_locale_smoke_matrix_audit_2026-05-30.md) | audit | Point-in-time Chromium locale smoke matrix. |
| [docs/archive/2026-q2/cis_firefox_benchmark_feature_analysis_2026-04-12.md](archive/2026-q2/cis_firefox_benchmark_feature_analysis_2026-04-12.md) | audit | Point-in-time CIS Firefox benchmark feature analysis. |
| [docs/archive/2026-q2/cis_firefox_implementation_roadmap_2026-04-12.md](archive/2026-q2/cis_firefox_implementation_roadmap_2026-04-12.md) | backlog | CIS Firefox implementation roadmap. |
| [docs/archive/2026-q2/cis_firefox_milestone_1_backlog_2026-04-12.md](archive/2026-q2/cis_firefox_milestone_1_backlog_2026-04-12.md) | backlog | CIS Firefox milestone 1 task list. |
| [docs/archive/2026-q2/cis_firefox_milestone_2_backlog_2026-04-12.md](archive/2026-q2/cis_firefox_milestone_2_backlog_2026-04-12.md) | backlog | CIS Firefox milestone 2 task list. |
| [docs/archive/2026-q2/cis_firefox_milestone_3_backlog_2026-04-12.md](archive/2026-q2/cis_firefox_milestone_3_backlog_2026-04-12.md) | backlog | CIS Firefox milestone 3 task list. |
| [docs/archive/2026-q2/cis_firefox_milestone_4_backlog_2026-04-12.md](archive/2026-q2/cis_firefox_milestone_4_backlog_2026-04-12.md) | backlog | CIS Firefox milestone 4 task list. |
| [docs/archive/2026-q2/cis_firefox_milestone_6_backlog_2026-04-13.md](archive/2026-q2/cis_firefox_milestone_6_backlog_2026-04-13.md) | backlog | CIS Firefox milestone 6 task list. |
| [docs/cis_firefox_update_runbook_2026-04-13.md](cis_firefox_update_runbook_2026-04-13.md) | runbook | CIS Firefox update procedure. |
| [docs/archive/2026-q2/cjk_font_fallback_audit_2026-05-30.md](archive/2026-q2/cjk_font_fallback_audit_2026-05-30.md) | audit | Point-in-time CJK font fallback audit. |
| [docs/archive/2026-q2/de_locale_catalog_notes_2026-05-29.md](archive/2026-q2/de_locale_catalog_notes_2026-05-29.md) | audit | German locale catalog notes. |
| [docs/archive/2026-q2/de_mozilla_terminology_audit_2026-05-29.md](archive/2026-q2/de_mozilla_terminology_audit_2026-05-29.md) | audit | German Mozilla terminology audit. |
| [docs/archive/2026-q2/de_overflow_audit_2026-05-30.md](archive/2026-q2/de_overflow_audit_2026-05-30.md) | audit | German locale overflow audit. |
| [docs/archive/2026-q2/dependency_refresh_backlog_2026-04-29.md](archive/2026-q2/dependency_refresh_backlog_2026-04-29.md) | backlog | Dependency refresh task list. |
| [docs/archive/2026-q2/documentation_portal_roadmap_2026-05-21.md](archive/2026-q2/documentation_portal_roadmap_2026-05-21.md) | backlog | Documentation portal roadmap. |
| [docs/archive/2026-q2/en_locale_mozilla_terminology_check_2026-05-21.md](archive/2026-q2/en_locale_mozilla_terminology_check_2026-05-21.md) | audit | English Mozilla terminology check. |
| [docs/archive/2026-q2/es_es_locale_catalog_notes_2026-05-29.md](archive/2026-q2/es_es_locale_catalog_notes_2026-05-29.md) | audit | Spanish locale catalog notes. |
| [docs/archive/2026-q2/es_es_mozilla_terminology_audit_2026-05-30.md](archive/2026-q2/es_es_mozilla_terminology_audit_2026-05-30.md) | audit | Spanish Mozilla terminology audit. |
| [docs/archive/2026-q2/es_es_overflow_audit_2026-05-30.md](archive/2026-q2/es_es_overflow_audit_2026-05-30.md) | audit | Spanish locale overflow audit. |
| [docs/epic-backlog-creation-runbook.md](epic-backlog-creation-runbook.md) | runbook | Required procedure for creating new target-version BPM epic backlogs. |
| [docs/firefox-live-testing.md](firefox-live-testing.md) | runbook | Firefox live testing procedure. |
| [docs/firefox-schema-update-runbook.md](firefox-schema-update-runbook.md) | runbook | Firefox schema refresh procedure. |
| [docs/archive/2026-q2/firefox_policies_json_import_export_backlog_2026-04-13.md](archive/2026-q2/firefox_policies_json_import_export_backlog_2026-04-13.md) | backlog | `policies.json` import/export task list. |
| [docs/firefox_policies_json_migration_notes_2026-04-14.md](firefox_policies_json_migration_notes_2026-04-14.md) | active | Maintained notes for `policies.json` migration behavior. |
| [docs/archive/2026-q2/fr_locale_catalog_notes_2026-05-29.md](archive/2026-q2/fr_locale_catalog_notes_2026-05-29.md) | audit | French locale catalog notes. |
| [docs/archive/2026-q2/fr_mozilla_terminology_audit_2026-05-29.md](archive/2026-q2/fr_mozilla_terminology_audit_2026-05-29.md) | audit | French Mozilla terminology audit. |
| [docs/archive/2026-q2/fr_overflow_audit_2026-05-30.md](archive/2026-q2/fr_overflow_audit_2026-05-30.md) | audit | French locale overflow audit. |
| [docs/frontend_self_hosting_backlog.md](frontend_self_hosting_backlog.md) | backlog | Frontend self-hosting task list. |
| [docs/archive/2026-q2/global_locale_expansion_backlog_2026-05-21.md](archive/2026-q2/global_locale_expansion_backlog_2026-05-21.md) | backlog | Global locale expansion task list. |
| [docs/archive/2026-q2/global_locale_loading_assumptions_audit_2026-05-21.md](archive/2026-q2/global_locale_loading_assumptions_audit_2026-05-21.md) | audit | Locale loading assumptions audit. |
| [docs/archive/2026-q2/guided_editor_six_step_mapping_2026-05-16.md](archive/2026-q2/guided_editor_six_step_mapping_2026-05-16.md) | backlog | Guided editor six-step mapping work. |
| [docs/locale_ownership_2026-06-01.md](locale_ownership_2026-06-01.md) | active | Maintained locale ownership and update boundary document. |
| [docs/archive/2026-q2/locale_picker_layout_audit_2026-05-30.md](archive/2026-q2/locale_picker_layout_audit_2026-05-30.md) | audit | Locale picker layout audit. |
| [docs/locale_placeholder_identifier_rules_2026-05-29.md](locale_placeholder_identifier_rules_2026-05-29.md) | active | Maintained placeholder and identifier localization rules. |
| [docs/archive/2026-q2/locale_screenshot_pack_audit_2026-05-30.md](archive/2026-q2/locale_screenshot_pack_audit_2026-05-30.md) | audit | Locale screenshot pack audit. |
| [docs/archive/2026-q2/locale_switching_regression_audit_2026-05-31.md](archive/2026-q2/locale_switching_regression_audit_2026-05-31.md) | audit | Locale switching regression audit. |
| [docs/locale_update_runbook_2026-06-01.md](locale_update_runbook_2026-06-01.md) | runbook | Locale update procedure. |
| [docs/archive/2026-q2/locale_viewport_overflow_assertions_audit_2026-05-30.md](archive/2026-q2/locale_viewport_overflow_assertions_audit_2026-05-30.md) | audit | Locale viewport overflow assertion audit. |
| [docs/locale_visible_english_allowlists_2026-05-30.md](locale_visible_english_allowlists_2026-05-30.md) | active | Maintained visible English allowlists for localization checks. |
| [docs/archive/2026-q2/localized_import_edit_export_workflow_audit_2026-05-31.md](archive/2026-q2/localized_import_edit_export_workflow_audit_2026-05-31.md) | audit | Localized import/edit/export workflow audit. |
| [docs/mozilla_terminology_verification_workflow_2026-05-29.md](mozilla_terminology_verification_workflow_2026-05-29.md) | runbook | Mozilla terminology verification procedure. |
| [docs/archive/2026-q2/profile_window_mode_separation_backlog_2026-04-29.md](archive/2026-q2/profile_window_mode_separation_backlog_2026-04-29.md) | backlog | Profile/window mode separation task list. |
| [docs/archive/2026-q2/profile_wizard_cognitive_load_backlog_2026-04-14.md](archive/2026-q2/profile_wizard_cognitive_load_backlog_2026-04-14.md) | backlog | Profile wizard cognitive-load task list. |
| [docs/archive/2026-q2/profile_wizard_coverage_priority_register_2026-04-04.md](archive/2026-q2/profile_wizard_coverage_priority_register_2026-04-04.md) | archive | Historical profile wizard coverage priority register. |
| [docs/archive/2026-q2/profile_wizard_ux_roadmap_2026-04-03.md](archive/2026-q2/profile_wizard_ux_roadmap_2026-04-03.md) | backlog | Profile wizard UX roadmap. |
| [docs/archive/2026-q2/profile_workspace_split_simplification_backlog_2026-04-21.md](archive/2026-q2/profile_workspace_split_simplification_backlog_2026-04-21.md) | backlog | Profile/workspace split simplification task list. |
| [docs/archive/2026-q2/responsive_long_label_css_audit_2026-05-30.md](archive/2026-q2/responsive_long_label_css_audit_2026-05-30.md) | audit | Responsive long-label CSS audit. |
| [docs/archive/2026-q2/ru_locale_accidental_english_audit_2026-05-15.md](archive/2026-q2/ru_locale_accidental_english_audit_2026-05-15.md) | audit | Russian accidental English audit. |
| [docs/archive/2026-q2/runtime_count_i18n_audit_2026-05-30.md](archive/2026-q2/runtime_count_i18n_audit_2026-05-30.md) | audit | Runtime count i18n audit. |
| [docs/source_copy_normalization_en_2026-05-21.md](source_copy_normalization_en_2026-05-21.md) | active | Maintained source-copy normalization notes. |
| [docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json](archive/2026-q2/source_string_inventory_en_2026-05-21.json) | archive | Large source-string inventory snapshot; use the active summary unless raw data is needed. |
| [docs/source_string_inventory_en_2026-05-21.md](source_string_inventory_en_2026-05-21.md) | active | Human-readable source-string inventory summary. |
| [docs/archive/2026-q2/ui_locale_glossary_en_ru_2026-05-15.md](archive/2026-q2/ui_locale_glossary_en_ru_2026-05-15.md) | archive | Superseded EN/RU glossary kept for historical reference. |
| [docs/ui_locale_glossary_global_2026-05-29.md](ui_locale_glossary_global_2026-05-29.md) | active | Maintained global UI locale glossary. |
| [docs/archive/2026-q2/ui_ux_product_backlog_2026-05-14.md](archive/2026-q2/ui_ux_product_backlog_2026-05-14.md) | backlog | UI/UX product task list. |
| [docs/archive/2026-q2/validation_error_i18n_audit_2026-05-30.md](archive/2026-q2/validation_error_i18n_audit_2026-05-30.md) | audit | Validation error i18n audit. |
| [docs/archive/2026-q2/wizard_ai_export_bugfix_backlog_2026-04-21.md](archive/2026-q2/wizard_ai_export_bugfix_backlog_2026-04-21.md) | backlog | Wizard AI export bugfix task list. |
| [docs/wizard_final_cleanup_backlog.md](wizard_final_cleanup_backlog.md) | backlog | Wizard final cleanup task list. |
| [docs/wizard_redesign_backlog.md](wizard_redesign_backlog.md) | backlog | Wizard redesign task list. |
| [docs/archive/2026-q2/wizard_viewport_qa_2026-03-31.md](archive/2026-q2/wizard_viewport_qa_2026-03-31.md) | audit | Historical wizard viewport QA notes. |
| [docs/archive/2026-q2/zh_cn_locale_catalog_notes_2026-05-29.md](archive/2026-q2/zh_cn_locale_catalog_notes_2026-05-29.md) | audit | Simplified Chinese locale catalog notes. |
| [docs/archive/2026-q2/zh_cn_mozilla_terminology_audit_2026-05-29.md](archive/2026-q2/zh_cn_mozilla_terminology_audit_2026-05-29.md) | audit | Simplified Chinese Mozilla terminology audit. |
| [docs/archive/2026-q2/zh_cn_script_audit_2026-05-30.md](archive/2026-q2/zh_cn_script_audit_2026-05-30.md) | audit | Simplified Chinese script audit. |
