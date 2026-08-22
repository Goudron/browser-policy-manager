from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "docs/architecture/profile-guided-ownership-matrix-contract-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-guided-ownership-matrix-contract-v1 -->"
TEMPLATE_DIR = REPO_ROOT / "app/templates/profiles"


def _fixture() -> dict[str, Any]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "guided ownership matrix fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _template_source() -> str:
    paths = [
        *sorted(TEMPLATE_DIR.glob("_page_wizard_step_*.html")),
        TEMPLATE_DIR / "_page_wizard_support.html",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _owned_items(owner_map: dict[str, list[str]], allowed: set[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for owner, items in owner_map.items():
        assert owner in allowed
        for item in items:
            assert item not in resolved, f"duplicate ownership for {item}"
            resolved[item] = owner
    return resolved


def _template_form_control_ids(source: str) -> set[str]:
    ids: set[str] = set()
    for element in re.findall(r"<(?:input|select|textarea)\b[^>]*>", source):
        match = re.search(r'\bid="([^"]+)"', element)
        if match:
            ids.add(match.group(1))
    return ids


def _current_schema_policy_ids() -> dict[str, set[str]]:
    return {
        channel: {
            policy_id
            for policy_id, definition in load_policy_schema(channel).policies.items()
            if definition.ui is not None
        }
        for channel in SUPPORTED_SCHEMA_CHANNELS
    }


def _policy_owner(matrix: dict[str, Any], policy_id: str) -> str:
    rules = matrix["policy_owner_rules"]
    owners = {
        rules["overrides"].get(policy_id, rules["by_current_ui_section"].get(definition.ui.section))
        for channel in SUPPORTED_SCHEMA_CHANNELS
        if (definition := load_policy_schema(channel).policies.get(policy_id)) is not None
        and definition.ui is not None
    }
    assert len(owners) == 1, policy_id
    owner = owners.pop()
    assert isinstance(owner, str)
    return owner


def test_guided_ownership_matrix_is_active_and_backlog_linked() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-guided-ownership-matrix-contract-0.9.6.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-07`" in source
    assert "active runtime ownership contract" in source
    assert "m7-05 materialized the extensions owner" in source

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M2-07 — Guided ownership matrix contract" in backlog
    assert "profile-guided-ownership-matrix-contract-0.9.6.md" in backlog


def test_eight_approved_steps_and_all_settings_only_are_the_only_setting_owners() -> None:
    matrix = _fixture()
    expected_steps = [
        (1, "browser-network-search", "Browser, network, and search"),
        (2, "urls-sites-navigation", "URLs, sites, and navigation"),
        (3, "security-privacy", "Security and privacy"),
        (4, "certificates-trust", "Certificates and trust"),
        (5, "users-language-sync", "Users, language, and sync"),
        (6, "extensions", "Extensions"),
        (7, "ai-smart-features", "AI and smart features"),
        (8, "review-export", "Review and export"),
    ]
    assert matrix["contract_id"] == "bpm096-guided-ownership-matrix"
    assert matrix["contract_version"] == 1
    assert matrix["status"] == "runtime-materialized-through-BPM096-M9-04"
    assert [
        (step["number"], step["id"], step["label"]) for step in matrix["steps"]
    ] == expected_steps
    assert matrix["allowed_owners"] == [
        *(step_id for _, step_id, _ in expected_steps),
        "all-settings-only",
    ]


def test_every_current_schema_policy_and_raw_fallback_resolves_once() -> None:
    matrix = _fixture()
    allowed = set(matrix["allowed_owners"])
    policy_rules = matrix["policy_owner_rules"]
    by_section = policy_rules["by_current_ui_section"]
    overrides = policy_rules["overrides"]
    assert set(by_section.values()) <= allowed
    assert set(overrides.values()) <= allowed

    current_by_channel = _current_schema_policy_ids()
    all_current_ids = set().union(*current_by_channel.values())
    assert set(overrides) <= all_current_ids

    observed_raw: set[tuple[str, str]] = set()
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        schema = load_policy_schema(channel)
        for policy_id, definition in schema.policies.items():
            if definition.ui is None:
                continue
            owner = overrides.get(policy_id, by_section.get(definition.ui.section))
            assert owner in allowed, f"orphan policy {channel}:{policy_id}"
            if definition.ui.support_level == "fallback":
                observed_raw.add((channel, policy_id))

    assert observed_raw
    assert matrix["raw_fallback"] == {
        "policy_owner": "policy_owner_rules",
        "final_review_reporting_owner": "review-export",
        "raw_deprecated_unknown_jump_targets": ["raw", "deprecated", "unknown"],
        "raw_value_is_not_a_second_guided_editor": True,
        "unmapped_or_unknown_policy": "all-settings-only",
    }


def test_schema_specific_controls_have_exact_current_channel_coverage() -> None:
    matrix = _fixture()
    current_by_channel = _current_schema_policy_ids()
    all_current_ids = set().union(*current_by_channel.values())
    actual_variants = {
        policy_id: [
            channel
            for channel in SUPPORTED_SCHEMA_CHANNELS
            if policy_id in current_by_channel[channel]
        ]
        for policy_id in sorted(all_current_ids)
        if sum(policy_id in current_by_channel[channel] for channel in SUPPORTED_SCHEMA_CHANNELS)
        != len(SUPPORTED_SCHEMA_CHANNELS)
    }
    assert matrix["schema_variants"] == actual_variants


def test_extensions_urls_and_certificates_are_each_complete_single_owner_families() -> None:
    matrix = _fixture()
    current_ids = set().union(*_current_schema_policy_ids().values())

    for owner, policy_ids in matrix["focused_domain_policy_ids"].items():
        assert set(policy_ids) <= current_ids
        for policy_id in policy_ids:
            assert _policy_owner(matrix, policy_id) == owner

    preference_rules = matrix["preference_owner_rules"]
    for owner, preference_ids in matrix["focused_domain_preference_ids"].items():
        for preference_id in preference_ids:
            assert preference_rules["overrides"][preference_id] == owner


def test_every_current_preference_preset_and_manual_control_resolves_once() -> None:
    matrix = _fixture()
    allowed = set(matrix["allowed_owners"])
    preference_rules = matrix["preference_owner_rules"]
    by_section = preference_rules["by_current_section"]
    overrides = preference_rules["overrides"]
    assert set(by_section.values()) <= allowed
    assert set(overrides.values()) <= allowed
    assert preference_rules["unregistered_manual_preference"] == "all-settings-only"

    for section in get_wizard_settings_catalog()["sections"]:
        preference_section = section["preferences"]
        section_id = preference_section["id"]
        for item in [*preference_section["presets"], *preference_section["known_preferences"]]:
            preference_id = f"{section_id}:{item['pref']}"
            owner = overrides.get(preference_id, by_section.get(section_id))
            assert owner in allowed, f"orphan preference {preference_id}"

    manual_catalog = get_manual_policy_controls_catalog()
    observed_groups = {group["id"] for group in manual_catalog["groups"]}
    assert observed_groups == set(matrix["manual_policy_group_owners"])
    for group in manual_catalog["groups"]:
        owner = matrix["manual_policy_group_owners"][group["id"]]
        assert owner in allowed
        assert group["items"], group["id"]


def test_current_template_controls_search_targets_presets_jumps_and_summaries_have_one_owner() -> (
    None
):
    matrix = _fixture()
    allowed = set(matrix["allowed_owners"])
    inventory = matrix["template_inventory"]
    source = _template_source()

    field_ids = _owned_items(inventory["field_control_ids"], allowed)
    handoff = matrix["preparation_handoff"]
    assert handoff["not_all_settings_controls"] is True
    assert set(handoff["id_selectors"]).isdisjoint(field_ids)
    # Preparation owns this lifecycle state after M5-05.  It must no longer be
    # reintroduced into any Guided template as a hidden draft control.
    assert _template_form_control_ids(source) == set(field_ids)
    assert not (set(handoff["id_selectors"]) & _template_form_control_ids(source))

    expected_search_targets = _owned_items(inventory["search_targets"], allowed)
    actual_search_targets = set(re.findall(r'data-settings-target="([^"]+)"', source))
    assert actual_search_targets == set(expected_search_targets)

    expected_presets = _owned_items(inventory["preset_selectors"], allowed)
    actual_presets = {
        f"{attribute}:{value}"
        for attribute, value in re.findall(r'(data-[a-z-]+)="([^"]+)"', source)
        if attribute.endswith("preset")
        or attribute in {"data-website-access-posture", "data-website-access-handlers"}
    }
    assert actual_presets == set(expected_presets)

    expected_data_controls = _owned_items(inventory["field_data_selectors"], allowed)
    actual_data_controls = {
        f"data-{attribute}:{value}"
        for attribute, value in re.findall(
            r'data-(firefox-home-key|firefox-suggest-key|search-engine-field|preference-field)="([^"]+)"',
            source,
        )
    }
    actual_data_controls.update(
        f"data-extension-profile:{profile_id}:{field}"
        for profile_id, field in re.findall(
            r'data-extension-profile="([^"]+)"[^>]*data-extension-field="([^"]+)"',
            source,
        )
    )
    assert actual_data_controls == set(expected_data_controls)

    expected_links = _owned_items(inventory["deep_links_and_jumps"], allowed)
    actual_links = set(re.findall(r'href="(#[^"]+)"', source))
    actual_links.update(
        f"{attribute}:{value}"
        for attribute, value in re.findall(r'(data-[a-z-]+-jump)="([^"]+)"', source)
    )
    assert actual_links == set(expected_links)

    expected_summaries = _owned_items(inventory["summary_ids"], allowed)
    handoff_summaries = set(handoff["summary_ids"])
    assert handoff_summaries.isdisjoint(expected_summaries)
    actual_summaries = {
        summary_id
        for summary_id in re.findall(r'id="(wizard-[^"]*summary[^"]*)"', source)
        if not summary_id.endswith("-jump")
    }
    # M5-05 owns preparation lifecycle summaries.  They must not reappear in
    # a Guided template after the preparation handoff.
    assert actual_summaries == set(expected_summaries)
    assert not (handoff_summaries & actual_summaries)

    for attribute, values in handoff["data_selector_values"].items():
        assert not re.findall(rf'{re.escape(attribute)}="([^"]+)"', source), values
