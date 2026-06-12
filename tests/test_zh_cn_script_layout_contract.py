import json
from pathlib import Path

from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
AUDIT_DOC_PATH = doc_path_from_index("zh_cn_script_audit_2026-05-30.md", status="audit")


def _load_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def test_zh_cn_script_audit_document_records_primary_surfaces():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-504`" in audit_doc
    assert "Simplified Chinese (`zh-CN`)" in audit_doc
    for surface in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert surface in audit_doc
    assert "desktop/mobile: clean" in audit_doc
    assert "/tmp/bpm-gloc504-zh-cn-audit-final2" in audit_doc


def test_zh_cn_primary_script_pass_replaces_visible_english_scaffolding():
    zh_catalog = _load_catalog("zh-CN")
    audited_keys = (
        "profiles.sidebar_hint",
        "profiles.wizard_progress_one",
        "profiles.wizard_progress_two",
        "profiles.wizard_progress_three",
        "profiles.wizard_progress_four",
        "profiles.wizard_step_undo",
        "profiles.wizard_step_reset",
        "profiles.wizard_baseline_summary_title",
        "profiles.wizard_baseline_summary_body",
        "profiles.wizard_cis_body",
        "profiles.meta_updated",
        "profiles.wizard_firefox_home_top_sites_label",
        "profiles.wizard_preferences_known_home_topsites_rows_title",
        "profiles.wizard_preferences_known_home_topsites_rows_copy",
        "profiles.wizard_preferences_known_search_quick_actions_title",
        "profiles.wizard_preferences_known_search_quick_actions_copy",
        "profiles.wizard_preferences_known_privacy_notification_default_title",
        "profiles.wizard_preferences_known_privacy_notification_default_copy",
        "profiles.wizard_scenario_corporate_badge",
        "profiles.wizard_scenario_corporate_title",
        "profiles.wizard_scenario_corporate_body",
        "profiles.wizard_scenario_shared_badge",
        "profiles.wizard_scenario_shared_title",
        "profiles.wizard_scenario_shared_body",
        "profiles.wizard_scenario_hardened_badge",
        "profiles.wizard_scenario_hardened_title",
        "profiles.wizard_scenario_hardened_body",
    )
    forbidden_fragments = (
        "an existing",
        "start a new",
        "Step 1 of 6",
        "Browser access",
        "Security & privacy",
        "Users,",
        "Undo this",
        "Reset this",
        "baseline will preconfigure",
        "Select a baseline",
        "Optionally merge",
        "Updated {value}",
        "Top sites",
        "Quick actions",
        "Notification permission default",
        "Most common",
        "Standard managed workstation",
        "Best when most people",
        "Shared access",
        "Shared device or kiosk",
        "Best for labs",
        "Higher trust",
    )
    audited_text = "\n".join(zh_catalog[key] for key in audited_keys)

    for fragment in forbidden_fragments:
        assert fragment not in audited_text


def test_known_preference_cards_have_i18n_keys_for_script_pass():
    catalog = get_wizard_settings_catalog()
    known_preferences = {
        item["pref"]: item
        for section in catalog["sections"]
        for item in section.get("preferences", {}).get("known_preferences", [])
    }

    assert known_preferences["browser.newtabpage.activity-stream.topSitesRows"]["label_key"] == (
        "profiles.wizard_preferences_known_home_topsites_rows_title"
    )
    assert known_preferences["browser.urlbar.suggest.quickactions"]["description_key"] == (
        "profiles.wizard_preferences_known_search_quick_actions_copy"
    )
    assert known_preferences["permissions.default.desktop-notification"]["label_key"] == (
        "profiles.wizard_preferences_known_privacy_notification_default_title"
    )
