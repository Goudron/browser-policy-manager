"""Keep current documentation meaning fail-closed without historical witnesses."""

from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION = ROOT / "documentation"
AUTHORITY_PATH = DOCUMENTATION / "config/documentation-semantic-contracts-0.9.4.json"
DITA_ROOT = DOCUMENTATION / "src/dita"

pytestmark = pytest.mark.docs_contract


class SemanticContractError(ValueError):
    """Raised when a current-source semantic contract loses a required outcome."""


def _text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _authority() -> dict[str, object]:
    return _json(AUTHORITY_PATH)


def _topic_ids(map_path: Path) -> set[str]:
    root = ET.parse(map_path).getroot()
    return {
        element.attrib["keyref"].removeprefix("topic.")
        for element in root.iter("topicref")
        if "keyref" in element.attrib
    }


def _keydefs() -> dict[str, str]:
    root = ET.parse(DOCUMENTATION / "src/dita/en/maps/keys.ditamap").getroot()
    return {
        element.attrib["keys"]: element.attrib["href"]
        for element in root.findall("keydef")
        if element.attrib["keys"].startswith("topic.")
    }


def _require_api_ownership(
    destinations: dict[str, set[str]], keydefs: dict[str, str], record: dict[str, object]
) -> None:
    for map_name, required_topics in record["required_destinations"].items():
        missing = set(required_topics) - destinations[map_name]
        if missing:
            raise SemanticContractError(f"{map_name} is missing {sorted(missing)}")
        for topic_id in required_topics:
            key = f"topic.{topic_id}"
            if key not in keydefs:
                raise SemanticContractError(f"Missing key definition: {key}")


def _target_body(source: str, target: str) -> str:
    match = re.search(
        rf"^{re.escape(target)}:(?:[^\n]*)\n(?P<body>(?:\t.*\n)+)", source, re.MULTILINE
    )
    if not match:
        raise SemanticContractError(f"Missing Makefile target: {target}")
    return match.group("body")


def _require_command_boundary(
    makefile_source: str, fast_runtime_source: str, record: dict[str, object]
) -> None:
    fast_body = _target_body(makefile_source, record["fast_target"])
    release_body = _target_body(makefile_source, record["release_target"])
    if "not a release gate" not in fast_body:
        raise SemanticContractError("Fast command presents release coverage")
    for semantic in record["fast_semantics"]:
        if semantic not in fast_runtime_source:
            raise SemanticContractError(f"Fast command omits {semantic}")
    for command in record["release_chain"]:
        if f"$(MAKE) {command}" not in release_body:
            raise SemanticContractError(f"Release handoff omits {command}")


def _require_localized_reader_semantics(
    terminology: dict[str, object], record: dict[str, object]
) -> None:
    protected = set(record["protected_exactness_classes"])
    available = set(terminology["allowlist"])
    missing = protected - available
    if missing:
        raise SemanticContractError(f"Missing protected localization classes: {sorted(missing)}")
    if not set(terminology["locales"]) >= {"ru", "de", "zh-CN", "fr", "es-ES"}:
        raise SemanticContractError("Localized semantic authority is incomplete")


def _require_runtime_artifact_policy(policy: dict[str, object], record: dict[str, object]) -> None:
    runtime = policy["current_runtime_contract"]
    if runtime["runtime_ready"] is not record["required_runtime_state"]:
        raise SemanticContractError("Runtime readiness does not match the current delivery state")
    prerequisites = set(runtime["required_before_shipping"])
    generated = set(record["generated_non_prerequisites"])
    if generated & prerequisites:
        raise SemanticContractError("Generated state was promoted to a shipping prerequisite")
    if len(prerequisites) < 3:
        raise SemanticContractError(
            "Current shipping boundary lost a required review or delivery step"
        )


def _require_current_source_installation(
    reconciliation: dict[str, object],
    privileged: dict[str, object],
    wsl: dict[str, object],
    record: dict[str, object],
) -> None:
    current = reconciliation["current_source_contract"]
    targets = {target["id"]: target for target in current["targets"]}
    expected = set(record["required_target_ids"])
    if set(targets) != expected:
        raise SemanticContractError("Current source-install target set drifted")
    required_tokens = current["required_tokens"]
    removed_commands = current["removed_maintainer_commands"]
    for target in targets.values():
        topic = DOCUMENTATION / "src/dita/en/admin" / f"{target['topic_id']}.dita"
        source = topic.read_text(encoding="utf-8")
        root = ET.fromstring(source)
        if root.find("./taskbody/result") is None or root.find("./taskbody/postreq") is None:
            raise SemanticContractError(f"Current topic loses outcome or recovery: {topic.name}")
        if not all(token in source for token in required_tokens):
            raise SemanticContractError(f"Current topic loses install envelope: {topic.name}")
        if any(command in source for command in removed_commands):
            raise SemanticContractError(f"Retired maintainer command returned: {topic.name}")

    forbidden_changes = " ".join(privileged["docker_installation"]["forbidden_host_changes"])
    if "docker group" not in forbidden_changes or "firewall" not in forbidden_changes:
        raise SemanticContractError("Privileged installation lost a host-safety boundary")
    if wsl["actual_host_gate"]["container_substitution_allowed"] is not False:
        raise SemanticContractError("Linux containers became WSL evidence")
    if wsl["actual_host_gate"]["current_linux_host_can_satisfy_gate"] is not False:
        raise SemanticContractError("Current Linux host was promoted to Windows evidence")


def _require_reader_explanation(root: ET.Element, record: dict[str, object]) -> None:
    lead = root.find("shortdesc")
    title = root.find("title")
    lead_text = _text(lead)
    title_text = _text(title)
    lead_contract = record["lead_contract"]

    if len(lead_text) < lead_contract["minimum_meaningful_length"]:
        raise SemanticContractError("Reader explanation lead is empty or too short")
    if lead_contract["forbid_title_restatement"] and lead_text.casefold() == title_text.casefold():
        raise SemanticContractError("Reader explanation lead merely restates the title")
    if lead is None or lead.find(f".//{lead_contract['required_reader_input_markup']}") is None:
        raise SemanticContractError("Reader explanation lead omits the user-visible input")

    sections = {
        section_id: root.find(f".//section[@id='{section_id}']")
        for section_id in record["required_sections"].values()
    }
    missing = [section_id for section_id, section in sections.items() if section is None]
    if missing:
        raise SemanticContractError(f"Reader explanation loses required sections: {missing}")

    topic_text = _text(root)
    missing_identifiers = [
        identifier
        for identifier in record["required_exact_identifiers"]
        if identifier not in topic_text
    ]
    if missing_identifiers:
        raise SemanticContractError(
            f"Reader explanation loses technical decision identifiers: {missing_identifiers}"
        )
    related = {
        link.attrib.get("keyref")
        for link in root.findall(".//related-links/link")
        if link.attrib.get("keyref")
    }
    if record["required_related_action_keyref"] not in related:
        raise SemanticContractError("Reader explanation loses its related language-change action")


def test_authority_records_have_current_sources_and_focused_regressions() -> None:
    contract = _authority()

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM094-M11A-03"
    assert contract["status"] == "accepted-current-source-authority"
    assert set(contract["exactness_policy"]) == {
        "allowed_product_requirements",
        "forbidden_incidental_coupling",
    }
    assert (
        "editorial prose phrases" in contract["exactness_policy"]["forbidden_incidental_coupling"]
    )

    authorities = contract["authorities"]
    for record in authorities.values():
        source_paths = record.get("sources", [record.get("source")])
        assert all(source and (ROOT / source).is_file() for source in source_paths)
        assert record["negative_rule"]
    for replacement in contract["replacements"]:
        assert replacement["authority"] in authorities
        assert replacement["positive_test"].startswith("test_")
        assert replacement["negative_test"].startswith("test_")


def test_current_api_topic_ownership_accepts_current_maps() -> None:
    record = _authority()["authorities"]["api_topic_ownership"]
    destinations = {
        map_name: _topic_ids(DOCUMENTATION / "src/dita/en/maps" / map_name)
        for map_name in record["required_destinations"]
    }

    _require_api_ownership(destinations, _keydefs(), record)


def test_current_api_topic_ownership_rejects_missing_destination() -> None:
    record = _authority()["authorities"]["api_topic_ownership"]
    destinations = {
        map_name: _topic_ids(DOCUMENTATION / "src/dita/en/maps" / map_name)
        for map_name in record["required_destinations"]
    }
    missing_topic = record["required_destinations"]["administrator-guide.ditamap"][0]
    destinations["administrator-guide.ditamap"].remove(missing_topic)

    with pytest.raises(SemanticContractError, match="missing"):
        _require_api_ownership(destinations, _keydefs(), record)


def test_documentation_command_boundary_accepts_fast_and_release_paths() -> None:
    record = _authority()["authorities"]["documentation_command_boundary"]
    _require_command_boundary(
        (ROOT / record["source"]).read_text(encoding="utf-8"),
        (ROOT / record["fast_runtime_source"]).read_text(encoding="utf-8"),
        record,
    )


def test_documentation_command_boundary_rejects_missing_release_proof() -> None:
    record = _authority()["authorities"]["documentation_command_boundary"]
    source = (ROOT / record["source"]).read_text(encoding="utf-8")
    broken = source.replace("$(MAKE) docs-package-verify", "", 1)

    with pytest.raises(SemanticContractError, match="docs-package-verify"):
        _require_command_boundary(
            broken,
            (ROOT / record["fast_runtime_source"]).read_text(encoding="utf-8"),
            record,
        )


def test_localized_reader_semantics_accepts_protected_technical_classes() -> None:
    record = _authority()["authorities"]["localized_reader_semantics"]
    terminology = _json(ROOT / record["sources"][0])

    _require_localized_reader_semantics(terminology, record)


def test_localized_reader_semantics_rejects_missing_protected_class() -> None:
    record = _authority()["authorities"]["localized_reader_semantics"]
    terminology = _json(ROOT / record["sources"][0])
    broken = copy.deepcopy(terminology)
    del broken["allowlist"]["identifier"]

    with pytest.raises(SemanticContractError, match="identifier"):
        _require_localized_reader_semantics(broken, record)


def test_runtime_artifact_policy_accepts_current_shipping_boundary() -> None:
    record = _authority()["authorities"]["runtime_artifact_policy"]
    policy = _json(ROOT / record["source"])

    _require_runtime_artifact_policy(policy, record)


def test_runtime_artifact_policy_rejects_generated_runtime_prerequisite() -> None:
    record = _authority()["authorities"]["runtime_artifact_policy"]
    policy = _json(ROOT / record["source"])
    broken = copy.deepcopy(policy)
    broken["current_runtime_contract"]["required_before_shipping"].append("manifest.json")

    with pytest.raises(SemanticContractError, match="Generated state"):
        _require_runtime_artifact_policy(broken, record)


def test_current_source_installation_accepts_current_topics_and_safety_boundary() -> None:
    record = _authority()["authorities"]["current_source_installation"]
    reconciliation, privileged, wsl = (_json(ROOT / path) for path in record["sources"][:3])

    _require_current_source_installation(reconciliation, privileged, wsl, record)


def test_current_source_installation_rejects_removed_topic_or_safety_boundary() -> None:
    record = _authority()["authorities"]["current_source_installation"]
    reconciliation, privileged, wsl = (_json(ROOT / path) for path in record["sources"][:3])
    broken_reconciliation = copy.deepcopy(reconciliation)
    broken_reconciliation["current_source_contract"]["targets"].pop()

    with pytest.raises(SemanticContractError, match="target set"):
        _require_current_source_installation(broken_reconciliation, privileged, wsl, record)

    broken_privileged = copy.deepcopy(privileged)
    broken_privileged["docker_installation"]["forbidden_host_changes"] = []
    with pytest.raises(SemanticContractError, match="host-safety"):
        _require_current_source_installation(reconciliation, broken_privileged, wsl, record)


def test_reader_explanations_accept_localized_factual_leads() -> None:
    record = _authority()["authorities"]["reader_explanations"]
    assert record["backlog_item"] == "BPM094-M11A-03A"
    topic = record["topic"]

    for locale in topic["locales"]:
        root = ET.parse(DITA_ROOT / locale / topic["guide"] / f"{topic['topic_id']}.dita").getroot()
        _require_reader_explanation(root, record)


def test_reader_explanations_reject_an_empty_or_title_only_lead() -> None:
    record = _authority()["authorities"]["reader_explanations"]
    topic = record["topic"]
    source_root = ET.parse(
        DITA_ROOT / "en" / topic["guide"] / f"{topic['topic_id']}.dita"
    ).getroot()

    empty_lead = copy.deepcopy(source_root)
    empty_lead.find("shortdesc").clear()
    with pytest.raises(SemanticContractError, match="empty or too short"):
        _require_reader_explanation(empty_lead, record)

    title_only_lead = copy.deepcopy(source_root)
    title_only_lead.find("shortdesc").clear()
    title_only_lead.find("shortdesc").text = _text(title_only_lead.find("title"))
    with pytest.raises(SemanticContractError, match="merely restates"):
        _require_reader_explanation(title_only_lead, record)
