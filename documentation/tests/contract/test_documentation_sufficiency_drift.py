from __future__ import annotations

import glob
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
GUARD = DOCUMENTATION_ROOT / "config/documentation-sufficiency-drift-guard-0.9.1.json"
SEMANTIC_AUTHORITY = DOCUMENTATION_ROOT / "config/documentation-semantic-contracts-0.9.4.json"
SEMANTIC_TEST = DOCUMENTATION_ROOT / "tests/contract/test_documentation_semantic_contracts_0_9_4.py"
TEST_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|js))(?:::(?P<test>test_[A-Za-z0-9_]+))?"
)
TOPIC_TARGET_RE = re.compile(r"^(?:ug|admin|fx|cis)-")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _guard() -> dict:
    return _json(GUARD)


def _review_entries() -> list[tuple[dict, dict]]:
    entries = []
    for source in _guard()["review_sources"]:
        review = _json(REPOSITORY_ROOT / source["path"])
        entries.extend((source, item) for item in review[source["collection"]])
    return entries


def _topic_ids(source: dict, item: dict) -> list[str]:
    value = item[source["topic_field"]]
    return value if isinstance(value, list) else [value]


def _keydefs(locale: str) -> dict[str, Path]:
    key_map = DITA_ROOT / locale / "maps/keys.ditamap"
    root = ET.fromstring(key_map.read_text(encoding="utf-8"))
    return {
        keydef.attrib["keys"]: (key_map.parent / keydef.attrib["href"]).resolve()
        for keydef in root.findall(".//keydef")
        if keydef.attrib.get("keys") and keydef.attrib.get("href")
    }


def _repository_matches(reference: str) -> list[Path]:
    return [Path(path) for path in glob.glob(str(REPOSITORY_ROOT / reference))]


def _retired_witnesses() -> set[str]:
    contract = _json(SEMANTIC_AUTHORITY)
    return {
        path
        for replacement in contract["replacements"]
        for path in replacement.get("retired_witnesses", [])
    }


def test_drift_guard_declares_all_review_sources_and_fail_closed_checks() -> None:
    guard = _guard()

    assert guard["schema_version"] == 1
    assert guard["contract_id"] == "bpm-documentation-sufficiency-drift-guard-0.9.1"
    assert guard["backlog_item"] == "BPM091-M6-07"
    assert guard["target_bpm_version"] == "0.9.1"
    assert guard["status"] == "accepted"
    assert [source["guide_ids"] for source in guard["review_sources"]] == [
        ["user-guide"],
        ["firefox-policy-guide", "cis-settings-guide"],
        ["administrator-guide"],
    ]
    assert len(guard["drift_checks"]) == 5


def test_every_review_entry_retains_protocol_fields_results_and_verification() -> None:
    guard = _guard()
    protocol = _json(REPOSITORY_ROOT / guard["protocol"])
    required = set(protocol["review_item_template"]["required_fields"])
    grouped_derived = {"topic_id", "locale_scope"}

    for source, item in _review_entries():
        missing = required - set(item)
        if isinstance(item[source["topic_field"]], list):
            missing -= grouped_derived
        assert not missing, (item["review_id"], sorted(missing))
        assert _topic_ids(source, item), (item["review_id"], "topic_id")
        for field in (
            "task_or_claim",
            "prerequisites",
            "exact_steps",
            "expected_result",
            "recovery_path",
            "drift_source",
            "focused_verification",
            "evidence_type",
            "evidence_artifact",
            "review_disposition",
        ):
            assert item[field], (item["review_id"], field)


def test_reviewed_localized_procedures_retain_commands_results_recovery_and_links() -> None:
    guard = _guard()
    procedure = guard["procedure_contract"]

    for source, item in _review_entries():
        topic_directory = source.get("topic_directory")
        if not topic_directory:
            continue
        for locale in procedure["locales"]:
            for topic_id in _topic_ids(source, item):
                path = DITA_ROOT / locale / topic_directory / f"{topic_id}.dita"
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                related = root.findall("./related-links/link")
                assert related and all(link.attrib.get("keyref") for link in related), (
                    locale,
                    topic_id,
                    "related-links/link",
                )
                if root.tag != "task":
                    continue
                taskbody = root.find("taskbody")
                assert taskbody is not None, (locale, topic_id, "taskbody")
                prereq = taskbody.find("prereq")
                result = taskbody.find("result")
                postreq = taskbody.find("postreq")
                commands = taskbody.findall("./steps/step/cmd")
                assert prereq is not None and "".join(prereq.itertext()).strip(), (
                    locale,
                    topic_id,
                    "prereq",
                )
                assert len(commands) >= procedure["minimum_step_count"], (
                    locale,
                    topic_id,
                    "steps/step/cmd",
                )
                assert all("".join(command.itertext()).strip() for command in commands)
                assert result is not None and "".join(result.itertext()).strip(), (
                    locale,
                    topic_id,
                    "result",
                )
                assert postreq is not None and "".join(postreq.itertext()).strip(), (
                    locale,
                    topic_id,
                    "postreq",
                )


def test_linux_source_install_topics_retain_executable_command_blocks() -> None:
    guard = _guard()
    procedure = guard["procedure_contract"]
    command_contract = _json(REPOSITORY_ROOT / procedure["linux_command_contract"])

    for target in command_contract["targets"]:
        for locale in procedure["locales"]:
            path = DITA_ROOT / locale / "admin" / f"{target['topic_id']}.dita"
            root = ET.fromstring(path.read_text(encoding="utf-8"))
            blocks = root.findall("./taskbody/steps/step/info/codeblock")
            assert len(blocks) >= procedure["minimum_linux_codeblock_count"], (
                locale,
                target["topic_id"],
                "codeblock",
            )
            assert all(
                "".join(block.itertext()).strip() or block.attrib.get("conref") for block in blocks
            ), (locale, target["topic_id"], "codeblock content or conref")


def test_review_drift_sources_evidence_and_pytest_nodes_still_exist() -> None:
    for _, item in _review_entries():
        for reference in item["drift_source"]:
            assert _repository_matches(reference), (item["review_id"], "drift_source", reference)
        for reference in item["evidence_artifact"]:
            assert (REPOSITORY_ROOT / reference).exists(), (
                item["review_id"],
                "evidence_artifact",
                reference,
            )
        for command in item["focused_verification"]:
            matches = list(TEST_PATH_RE.finditer(command))
            assert matches, (item["review_id"], "focused_verification", command)
            for match in matches:
                path = REPOSITORY_ROOT / match["path"]
                if not path.is_file() and match["path"] in _retired_witnesses():
                    assert SEMANTIC_TEST.is_file()
                    continue
                assert path.is_file(), (item["review_id"], match.group(0))
                if match["test"]:
                    assert f"def {match['test']}(" in path.read_text(encoding="utf-8"), (
                        item["review_id"],
                        match.group(0),
                    )


def test_reviewed_guide_links_resolve_in_every_locale() -> None:
    guard = _guard()
    keydefs_by_locale = {
        locale: _keydefs(locale) for locale in guard["procedure_contract"]["locales"]
    }

    for locale, keydefs in keydefs_by_locale.items():
        for key, target in keydefs.items():
            assert target.is_file(), (locale, key, target)

    for source, item in _review_entries():
        recovery_targets = [
            target for target in item["recovery_path"] if TOPIC_TARGET_RE.match(target)
        ]
        for locale, keydefs in keydefs_by_locale.items():
            for target in recovery_targets:
                assert f"topic.{target}" in keydefs, (locale, item["review_id"], target)
        topic_directory = source.get("topic_directory")
        if not topic_directory:
            continue
        for locale, keydefs in keydefs_by_locale.items():
            for topic_id in _topic_ids(source, item):
                path = DITA_ROOT / locale / topic_directory / f"{topic_id}.dita"
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                for link in root.findall("./related-links/link"):
                    assert link.attrib["keyref"] in keydefs, (
                        locale,
                        topic_id,
                        link.attrib["keyref"],
                    )
