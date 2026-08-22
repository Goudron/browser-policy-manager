"""Runtime topology guard consumed from the BPM 0.9.6 ownership fixture."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from bs4 import BeautifulSoup

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_wizard_shell.catalog import (
    CERTIFICATE_TRUST_GUIDED_POLICY_IDS,
    WIZARD_SHELL_STEPS,
    get_wizard_schema_shell_catalog,
)
from app.web.firefox_wizard_steps import get_wizard_steps
from tests.web_profiles_page_helpers import REPO_ROOT, _profiles_page_response

CONTRACT_PATH = REPO_ROOT / "docs/architecture/profile-guided-ownership-matrix-contract-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-guided-ownership-matrix-contract-v1 -->"
SCHEMA_SHELL_SECTIONS_PATH = REPO_ROOT / "app/static/profiles_schema_shell_sections.js"
SEARCH_CATALOG_PATH = REPO_ROOT / "app/static/profiles_catalogs.js"


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


def _owned_items(owner_map: dict[str, list[str]], allowed: set[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for owner, items in owner_map.items():
        assert owner in allowed
        for item in items:
            assert item not in resolved, f"duplicate ownership for {item}"
            resolved[item] = owner
    return resolved


def _runtime(matrix: dict[str, Any]) -> dict[str, Any]:
    runtime = matrix["runtime_materialization"]
    assert runtime["guard_owner"] == "BPM096-M6-04"
    assert runtime["phase"] == "after-BPM096-M9-02-before-BPM096-M9-03"
    return runtime


def _owner_to_step_number(matrix: dict[str, Any], panel_step_id: str) -> int:
    runtime = _runtime(matrix)
    for owner, catalog_step_id in runtime["guided_step_catalog_ids"].items():
        if catalog_step_id == panel_step_id:
            return int(runtime["owner_steps"][owner])
    raise AssertionError(f"unknown wizard panel step id: {panel_step_id}")


def _panel_step_number(matrix: dict[str, Any], element: Any) -> int:
    panel = element.find_parent("section", class_="wizard-panel")
    assert panel is not None, f"selector {element!r} is outside a Guided panel"
    panel_step_id = panel.get("data-wizard-step-id")
    assert isinstance(panel_step_id, str) and panel_step_id
    return _owner_to_step_number(matrix, panel_step_id)


def _assert_current_host(
    matrix: dict[str, Any], owner: str, step_number: int, *, host_kind: str
) -> None:
    allowed_hosts = _runtime(matrix)[host_kind]
    assert step_number in allowed_hosts[owner], (
        f"{owner} is rendered at stale or unrecorded step {step_number}; "
        f"allowed: {allowed_hosts[owner]}"
    )


def _target_owners(matrix: dict[str, Any]) -> dict[str, str]:
    allowed = set(matrix["allowed_owners"])
    targets = _owned_items(matrix["template_inventory"]["search_targets"], allowed)
    manual_catalog = get_manual_policy_controls_catalog()
    manual_group_owners = matrix["manual_policy_group_owners"]

    rendered_groups = _runtime(matrix)["rendered_manual_policy_groups"]
    template_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / "app/templates/profiles").glob("_page_wizard_step_*.html"))
    )
    actual_group_ids = set(re.findall(r'wizard_manual_policy_groups\["([^"]+)"\]', template_source))
    assert actual_group_ids == set(rendered_groups)
    assert actual_group_ids <= set(manual_group_owners)

    for group in manual_catalog["groups"]:
        if group["id"] not in rendered_groups:
            continue
        owner = manual_group_owners[group["id"]]
        spec = rendered_groups[group["id"]]
        assert owner in allowed
        assert spec["owner"] == owner
        _assert_current_host(
            matrix,
            owner,
            int(spec["host_step"]),
            host_kind="allowed_current_template_host_steps",
        )
        for item in group["items"]:
            target = item["target"]
            policy_id = item["policy_id"]
            assert _policy_owner(matrix, policy_id) == owner
            existing = targets.setdefault(target, owner)
            assert existing == owner, f"manual target owner mismatch for {target}"
    return targets


def _attribute_selector_elements(soup: BeautifulSoup, selector: str) -> list[Any]:
    attribute, value = selector.split(":", 1)
    if attribute == "data-extension-profile":
        profile_id, field = value.rsplit(":", 1)
        return soup.find_all(
            attrs={"data-extension-profile": profile_id, "data-extension-field": field}
        )
    return soup.find_all(attrs={attribute: value})


def _current_mounted_policy_controls() -> dict[str, int]:
    source = SCHEMA_SHELL_SECTIONS_PATH.read_text(encoding="utf-8")
    entries = re.findall(r'\{ el: \w+, policyId: "([^"]+)", step: (\d+) \}', source)
    resolved = {policy_id: int(step) for policy_id, step in entries}
    assert len(resolved) == len(entries), "duplicate mounted policy control"
    return resolved


def _current_search_section_hosts() -> dict[str, tuple[int, str, str]]:
    source = SEARCH_CATALOG_PATH.read_text(encoding="utf-8")
    block_match = re.search(
        r"wizardSearchSectionSteps:\s*\{(?P<body>.*?)\n\s*\},\n\s*searchEnginePresetCatalog:",
        source,
        flags=re.DOTALL,
    )
    assert block_match, "wizard search step metadata is missing"
    return {
        section_id: (int(step), key, fallback)
        for section_id, step, key, fallback in re.findall(
            r'(\w+): \{ step: (\d+), key: "([^"]+)", fallback: "([^"]+)" \}',
            block_match.group("body"),
        )
    }


def test_step_catalog_and_schema_shell_consume_the_same_eight_step_matrix() -> None:
    matrix = _fixture()
    runtime = _runtime(matrix)
    expected_steps = [(int(step["number"]), step["id"]) for step in matrix["steps"]]

    expected_catalog_steps = [
        (number, runtime["guided_step_catalog_ids"][owner]) for number, owner in expected_steps
    ]
    assert [(step["step"], step["id"]) for step in get_wizard_steps()] == expected_catalog_steps
    assert [(step["step"], step["id"]) for step in WIZARD_SHELL_STEPS] == expected_catalog_steps
    assert runtime["owner_steps"] == {
        **{owner: number for number, owner in expected_steps},
        "all-settings-only": 8,
    }


def test_every_schema_policy_and_preference_has_one_current_host_with_a_recorded_owner() -> None:
    matrix = _fixture()
    shell_catalog = get_wizard_schema_shell_catalog(
        get_wizard_preferences_catalog(get_wizard_settings_catalog())
    )
    expected_by_channel = _current_schema_policy_ids()

    for channel, expected_policy_ids in expected_by_channel.items():
        observed_hosts: dict[str, int] = {}
        for step_meta in shell_catalog["steps"]:
            step_number = int(step_meta["step"])
            buckets = shell_catalog["channels"][channel]["steps"][str(step_number)]
            for bucket_name in ("recommended", "additional", "raw_fallback"):
                for item in buckets[bucket_name]:
                    policy_id = item["id"]
                    assert policy_id not in observed_hosts, (
                        f"duplicate schema-shell policy {channel}:{policy_id}"
                    )
                    observed_hosts[policy_id] = step_number

        certificate_trust_policy_ids = expected_policy_ids & CERTIFICATE_TRUST_GUIDED_POLICY_IDS
        assert set(observed_hosts) == expected_policy_ids - certificate_trust_policy_ids
        for policy_id, host_step in observed_hosts.items():
            _assert_current_host(
                matrix,
                _policy_owner(matrix, policy_id),
                host_step,
                host_kind="allowed_schema_shell_host_steps",
            )
        for policy_id in certificate_trust_policy_ids:
            _assert_current_host(
                matrix,
                _policy_owner(matrix, policy_id),
                4,
                host_kind="allowed_schema_shell_host_steps",
            )

    preference_hosts: dict[str, int] = {}
    for step_meta in WIZARD_SHELL_STEPS:
        for section_id in step_meta["preference_sections"]:
            assert section_id not in preference_hosts, (
                f"duplicate preference shell section {section_id}"
            )
            preference_hosts[section_id] = int(step_meta["step"])

    preference_catalog = get_wizard_preferences_catalog(get_wizard_settings_catalog())
    assert set(preference_hosts) == {section["id"] for section in preference_catalog["sections"]}
    rules = matrix["preference_owner_rules"]
    for section in preference_catalog["sections"]:
        section_id = section["id"]
        for item in [*section["presets"], *section["known_preferences"]]:
            preference_id = f"{section_id}:{item['pref']}"
            owner = rules["overrides"].get(
                preference_id, rules["by_current_section"].get(section_id)
            )
            assert isinstance(owner, str), f"orphan preference {preference_id}"
            _assert_current_host(
                matrix,
                owner,
                preference_hosts[section_id],
                host_kind="allowed_preference_shell_host_steps",
            )


def test_rendered_template_targets_fields_presets_and_summaries_have_exactly_one_owner() -> None:
    matrix = _fixture()
    response = _profiles_page_response()
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    inventory = matrix["template_inventory"]
    allowed = set(matrix["allowed_owners"])

    target_owners = _target_owners(matrix)
    actual_targets = [
        element.get("data-settings-target") for element in soup.select("[data-settings-target]")
    ]
    assert set(actual_targets) == set(target_owners)
    for target, count in Counter(actual_targets).items():
        assert count == 1, f"duplicate rendered target {target}"
        element = soup.select_one(f'[data-settings-target="{target}"]')
        assert element is not None
        _assert_current_host(
            matrix,
            target_owners[target],
            _panel_step_number(matrix, element),
            host_kind="allowed_current_template_host_steps",
        )

    for owner, control_ids in inventory["field_control_ids"].items():
        assert owner in allowed
        for control_id in control_ids:
            elements = soup.find_all(id=control_id)
            assert len(elements) == 1, f"stale or duplicate field control {control_id}"
            _assert_current_host(
                matrix,
                owner,
                _panel_step_number(matrix, elements[0]),
                host_kind="allowed_current_template_host_steps",
            )

    for owner, selectors in inventory["field_data_selectors"].items():
        assert owner in allowed
        for selector in selectors:
            elements = _attribute_selector_elements(soup, selector)
            expected_count = int(_runtime(matrix)["field_data_selector_counts"].get(selector, 1))
            assert len(elements) == expected_count, (
                f"stale or duplicate data selector {selector}; "
                f"expected {expected_count}, got {len(elements)}"
            )
            if owner != "all-settings-only":
                _assert_current_host(
                    matrix,
                    owner,
                    _panel_step_number(matrix, elements[0]),
                    host_kind="allowed_current_template_host_steps",
                )

    for owner, selectors in inventory["preset_selectors"].items():
        assert owner in allowed
        for selector in selectors:
            elements = _attribute_selector_elements(soup, selector)
            assert len(elements) == 1, f"stale or duplicate preset selector {selector}"
            _assert_current_host(
                matrix,
                owner,
                _panel_step_number(matrix, elements[0]),
                host_kind="allowed_current_template_host_steps",
            )

    summary_owners = _owned_items(inventory["summary_ids"], allowed)
    actual_summary_ids = {
        element["id"]
        for element in soup.select("[id]")
        if element["id"].startswith("wizard-")
        and "summary" in element["id"]
        and not element["id"].endswith("-jump")
    }
    assert actual_summary_ids == set(summary_owners)
    for summary_id, owner in summary_owners.items():
        element = soup.find(id=summary_id)
        assert element is not None
        _assert_current_host(
            matrix,
            owner,
            _panel_step_number(matrix, element),
            host_kind="allowed_current_template_host_steps",
        )


def test_mounted_widgets_and_search_metadata_match_the_recorded_current_hosts() -> None:
    matrix = _fixture()
    runtime = _runtime(matrix)
    expected_widgets = runtime["mounted_policy_controls"]
    actual_widgets = _current_mounted_policy_controls()
    assert actual_widgets == {
        policy_id: int(spec["host_step"]) for policy_id, spec in expected_widgets.items()
    }

    response = _profiles_page_response()
    soup = BeautifulSoup(response.text, "html.parser")
    deferred = runtime["deferred_domain_materialization"]
    for policy_id, spec in expected_widgets.items():
        owner = spec["owner"]
        assert _policy_owner(matrix, policy_id) == owner
        _assert_current_host(
            matrix,
            owner,
            int(spec["host_step"]),
            host_kind="allowed_current_template_host_steps",
        )
        owner_deferred = deferred.get(owner, {})
        expected_deferred = (
            None
            if int(spec["host_step"]) == int(owner_deferred.get("required_owner_step", -1))
            else owner_deferred.get("delivery_milestone")
        )
        assert spec.get("deferred_until") == expected_deferred
        holders = soup.select(f'[data-settings-target="policy:{policy_id}"]')
        assert len(holders) == 1, f"stale or duplicate mounted holder for {policy_id}"
        assert _panel_step_number(matrix, holders[0]) == int(spec["host_step"])

    expected_search_sections = runtime["search_section_hosts"]
    actual_search_sections = _current_search_section_hosts()
    assert set(actual_search_sections) == set(expected_search_sections)
    settings_catalog_sections = {
        section["id"] for section in get_wizard_settings_catalog()["sections"]
    }
    assert settings_catalog_sections == set(actual_search_sections) - {"ai", "review"}
    step_metadata = {int(step["step"]): step for step in get_wizard_steps()}
    for section_id, spec in expected_search_sections.items():
        host_step, key, fallback = actual_search_sections[section_id]
        assert host_step == int(spec["host_step"])
        assert key == step_metadata[host_step]["label_key"]
        assert fallback == step_metadata[host_step]["label_fallback"]
        _assert_current_host(
            matrix,
            spec["owner"],
            host_step,
            host_kind="allowed_current_template_host_steps",
        )
        owner_deferred = deferred.get(spec["owner"], {})
        expected_deferred = (
            None
            if host_step == int(owner_deferred.get("required_owner_step", -1))
            else owner_deferred.get("delivery_milestone")
        )
        assert spec.get("deferred_until") == expected_deferred
