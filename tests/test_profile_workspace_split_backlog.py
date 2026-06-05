from tests.docs_index import REPO_ROOT, doc_path_from_index, docs_manifest


def _finished_backlog_item(item_id: str) -> dict[str, object]:
    manifest = docs_manifest()
    items = [
        item
        for item in manifest["finished_backlog_items"]
        if item["id"] == item_id
    ]
    assert len(items) == 1
    return items[0]


def test_simplified_wizard_component_contract_is_recorded_in_docs_manifest():
    item = _finished_backlog_item("WS-D01")
    source_doc = doc_path_from_index(
        "profile_workspace_split_simplification_backlog_2026-04-21.md",
        status="backlog",
    )

    assert item["title"] == "Define The Simplified Wizard Component Contract"
    assert item["status"] == "done"
    assert item["source_doc"] == source_doc.relative_to(REPO_ROOT / "docs").as_posix()
    assert item["contract"] == "simplified_wizard_component"
    assert item["default_visible_section_answer"] == "one_admin_question"
    assert item["followup_range"] == "WS-D02..WS-D13"
    assert item["required_components"] == [
        "title",
        "one_line_purpose",
        "primary_choice",
        "active_state",
        "real_warnings",
        "advanced_link",
    ]
    assert item["excluded_default_path"] == [
        "settings_maps",
        "guided_coverage_maps",
        "remaining_n_of_m_coverage_language",
        "schema_shell_inventories",
        "long_policy_reference_copy",
        "raw_policy_fallback_lists",
        "advanced_only_controls",
    ]
