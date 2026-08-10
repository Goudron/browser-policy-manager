from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.core.policy_validation import validate_profile_policies_for_channel

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
INVENTORY_PATH = (
    REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
)
MODEL_PATH = DOCUMENTATION_ROOT / "config/firefox-policy-topic-model-0.9.0.json"
GENERATED_ROOT = DOCUMENTATION_ROOT / "src/generated/firefox"
POLICIES_ROOT = GENERATED_ROOT / "policies"
INDEX_PATH = GENERATED_ROOT / "firefox-policy-skeletons-0.9.0.json"
CHANNEL_DIFFERENCES_PATH = GENERATED_ROOT / "firefox-policy-channel-differences-0.9.0.json"
PROVENANCE_REVIEW_PATH = GENERATED_ROOT / "firefox-policy-provenance-review-0.9.0.json"
MAP_PATH = GENERATED_ROOT / "firefox-policy-skeletons.ditamap"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/generate_firefox_policy_skeletons.py"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SPEC = importlib.util.spec_from_file_location("generate_firefox_policy_skeletons", MODULE_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)

pytestmark = pytest.mark.docs_contract


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _index() -> dict[str, object]:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _provenance_review() -> dict[str, object]:
    return json.loads(PROVENANCE_REVIEW_PATH.read_text(encoding="utf-8"))


def test_generated_policy_skeleton_inventory_covers_every_supported_policy_once() -> None:
    inventory = _inventory()
    index = _index()
    policies = inventory["policies"]
    expected_ids = {policy["policy_id"] for policy in policies}
    generated = index["policies"]

    assert index["schema_version"] == 1
    assert index["backlog_item"] == "BPM090-M5-02"
    assert index["example_backlog_item"] == "BPM090-M5-04"
    assert index["channel_differences_backlog_item"] == "BPM090-M5-05"
    assert index["schema_refresh_runbook_backlog_item"] == "BPM090-M5-08"
    assert index["provenance_review_backlog_item"] == "BPM090-M5-09"
    assert index["target_bpm_version"] == "0.9.0"
    assert index["generated_by"] == "documentation/tools/generate_firefox_policy_skeletons.py"
    assert index["policy_count"] == len(policies) == 121
    assert index["example_count"] == sum(len(policy["channels"]) for policy in policies) == 354
    assert {entry["policy_id"] for entry in generated} == expected_ids
    assert len({entry["doc_id"] for entry in generated}) == len(expected_ids)
    assert len({entry["path"] for entry in generated}) == len(expected_ids)
    for entry in generated:
        policy = next(policy for policy in policies if policy["policy_id"] == entry["policy_id"])
        assert entry["doc_id"] == policy["doc_id"]
        assert entry["channel_scope"] == policy["channel_scope"]
        assert entry["channel_support"]["scope"] == policy["channel_scope"]
        assert entry["channel_support"]["supported_channels"] == sorted(
            policy["channels"], key=generator._channel_sort_key
        )
        assert (REPOSITORY_ROOT / entry["path"]).is_file()
        assert len(entry["examples"]) == len(policy["channels"])


def test_generated_policy_skeleton_map_is_stable_and_keyed() -> None:
    inventory = _inventory()
    root = ET.parse(MAP_PATH).getroot()
    topicrefs = root.findall("topicref")

    assert root.tag == "map"
    assert root.attrib == {"id": "map-generated-firefox-policy-skeletons"}
    assert root.findtext("title") == "Generated Firefox policy skeletons"
    assert len(topicrefs) == len(inventory["policies"])
    assert [topicref.attrib["href"] for topicref in topicrefs] == sorted(
        [f"policies/{policy['doc_id']}.dita" for policy in inventory["policies"]],
        key=str.casefold,
    )
    assert all(
        topicref.attrib["keys"] == f"topic.{Path(topicref.attrib['href']).stem}"
        for topicref in topicrefs
    )


def test_each_generated_policy_topic_matches_the_model_sections_and_metadata() -> None:
    model = _model()
    inventory = _inventory()
    required_sections = [section["id"] for section in model["required_sections"]]
    conditional_props = model["topic"]["conditional_props"]

    for policy in inventory["policies"]:
        path = POLICIES_ROOT / f"{policy['doc_id']}.dita"
        root = ET.parse(path).getroot()
        expected_props = " ".join(
            prop
            for channel_prefix, prop in (
                ("release-", conditional_props["release"]),
                ("esr-", conditional_props["esr"]),
            )
            if any(channel.startswith(channel_prefix) for channel in policy["channels"])
        )

        assert root.tag == "reference"
        assert root.attrib == {
            "id": policy["doc_id"],
            "audience": "user",
            "product": "bpm-0-9-0",
            "platform": "web",
            "props": expected_props,
            "otherprops": f"policy({policy['policy_id']})",
        }
        assert root.findtext("title") == policy["policy_id"]
        sections = root.findall("./refbody/section")
        assert [section.attrib["id"] for section in sections] == required_sections
        assert all(section.findtext("title") for section in sections)
        assert all("BPM-HAND-REGION-START" in path.read_text(encoding="utf-8") for path in [path])


def test_channel_differences_artifact_records_release_esr_support_and_filter_fields() -> None:
    differences = json.loads(CHANNEL_DIFFERENCES_PATH.read_text(encoding="utf-8"))
    inventory = _inventory()
    policies_by_scope = {
        scope: [
            policy["policy_id"]
            for policy in inventory["policies"]
            if policy["channel_scope"] == scope
        ]
        for scope in ("both", "partial", "release-only", "esr-only")
    }
    changed = [
        policy["policy_id"]
        for policy in inventory["policies"]
        if policy["definition_changed_across_channels"]
    ]

    assert differences["schema_version"] == 1
    assert differences["backlog_item"] == "BPM090-M5-05"
    assert differences["schema_refresh_runbook_backlog_item"] == "BPM090-M5-08"
    assert differences["provenance_review_backlog_item"] == "BPM090-M5-09"
    assert differences["summary"] == {
        "both_channels": len(policies_by_scope["both"]),
        "changed_definitions": len(changed),
        "esr_only": len(policies_by_scope["esr-only"]),
        "partial": len(policies_by_scope["partial"]),
        "release_only": len(policies_by_scope["release-only"]),
    }
    assert differences["policy_ids"] == {
        "both_channels": policies_by_scope["both"],
        "partial": policies_by_scope["partial"],
        "release_only": policies_by_scope["release-only"],
        "esr_only": policies_by_scope["esr-only"],
        "changed_definitions": changed,
    }
    assert {
        "channel_support.scope",
        "channel_support.release_supported",
        "channel_support.esr_supported",
        "channel_support.supported_channels",
    } <= set(differences["search_and_navigation_contract"]["filter_fields"])
    assert differences["search_and_navigation_contract"]["display_badge_outputclass"] == (
        "channel-support-badge"
    )


def test_policy_provenance_review_records_approved_sources_and_forbidden_claims() -> None:
    provenance = _provenance_review()
    index = _index()
    matrix = json.loads(
        (
            REPOSITORY_ROOT / "docs/architecture/product-documentation-provenance-matrix-0.9.0.json"
        ).read_text(encoding="utf-8")
    )
    source_family = next(
        family
        for family in matrix["source_families"]
        if family["id"] == "mozilla-policy-schema-facts"
    )

    assert provenance["schema_version"] == 1
    assert provenance["backlog_item"] == "BPM090-M5-09"
    assert provenance["source_family_id"] == source_family["id"]
    assert provenance["license_id"] == source_family["license_id"] == "MPL-2.0"
    assert provenance["reuse_mode"] == "generated-facts"
    assert provenance["allowed_publication_policy"] == source_family["publication_policy"]
    assert {record["source_version_or_revision"] for record in provenance["source_records"]} == {
        "mozilla-policy-templates-v7.12",
        "mozilla-policy-templates-v8.0",
    }
    assert provenance["summary"] == {
        "both_channels": 112,
        "changed_definitions": 3,
        "esr_only": 0,
        "example_count": 354,
        "partial": 9,
        "policy_count": 121,
        "release_only": 0,
    }
    assert {entry["policy_id"] for entry in provenance["policies"]} == {
        entry["policy_id"] for entry in index["policies"]
    }
    assert {
        "copied-mozilla-prose-without-explicit-source-region",
        "live-browser-verification",
        "stale-channel-support",
        "missing-schema-fingerprint",
        "mozilla-affiliation-or-endorsement",
    } <= set(provenance["forbidden_claims"])

    for entry in provenance["policies"]:
        assert entry["source_family_id"] == "mozilla-policy-schema-facts"
        assert entry["license_id"] == "MPL-2.0"
        assert entry["reuse_mode"] == "generated-facts"
        assert {record["source_version_or_revision"] for record in entry["source_records"]} == {
            inventory_channel["schema_source"]
            for inventory_channel in (
                _inventory()["channels"][channel_id] for channel_id in entry["supported_channels"]
            )
        }
        assert entry["copied_mozilla_prose"] is False
        assert entry["live_browser_verification_claim"] is False
        assert (
            entry["no_affiliation_notice"] == "BPM is not affiliated with or endorsed by Mozilla."
        )
        assert set(entry["source_content_sha256_when_snapshotted"]) == set(
            entry["supported_channels"]
        )
        for channel in entry["channels"]:
            assert channel["source_version_or_revision"] == channel["schema_source"]
            assert len(channel["schema_sha256"]) == 64
            assert (
                channel["schema_sha256"]
                == entry["source_content_sha256_when_snapshotted"][channel["channel"]]
            )
            assert channel["topic_section_id"] == "a-provenance"


def test_each_generated_policy_topic_carries_source_version_and_license_metadata() -> None:
    inventory = _inventory()
    policies_by_id = {policy["policy_id"]: policy for policy in inventory["policies"]}

    for entry in _provenance_review()["policies"]:
        policy = policies_by_id[entry["policy_id"]]
        topic_text = (POLICIES_ROOT / f"{entry['doc_id']}.dita").read_text(encoding="utf-8")
        root = ET.fromstring(topic_text)
        provenance_text = " ".join(root.find("./refbody/section[@id='a-provenance']").itertext())

        for required in (
            "mozilla-policy-schema-facts",
            "generated-facts",
            "MPL-2.0",
            "BPM is not affiliated with or endorsed by Mozilla.",
            "BPM090-M2-03",
            "0.9.0",
        ):
            assert required in provenance_text

        for channel_id, channel in policy["channels"].items():
            channel_meta = inventory["channels"][channel_id]
            assert channel_id in provenance_text
            assert channel_meta["mozilla_version"] in provenance_text
            assert channel_meta["schema_source"] in provenance_text
            assert channel["schema_sha256"] in provenance_text
            source = channel_meta["schema_source"]
            assert generator._source_metadata(source)["source_locator"] in provenance_text
            assert generator._source_metadata(source)["source_retrieved_on"] in provenance_text


def test_generated_policy_topics_reject_unreviewed_mozilla_prose_and_unsupported_claims() -> None:
    forbidden_claim_patterns = (
        "Mozilla endorses BPM",
        "approved by Mozilla",
        "certified by Mozilla",
        "live-browser verified",
        "verified against a running Firefox",
        "copied from Mozilla",
    )

    for path in sorted(POLICIES_ROOT.glob("fx-policy-*.dita")):
        topic_text = path.read_text(encoding="utf-8")
        assert "BPM-MOZILLA-PROSE-REGION" not in topic_text
        assert "Mozilla Contributors" not in topic_text
        assert "verbatim Mozilla" not in topic_text
        for forbidden in forbidden_claim_patterns:
            assert forbidden.casefold() not in topic_text.casefold()


def test_partial_policy_topics_retain_esr_140_13_absence() -> None:
    index = _index()
    partial = [
        entry for entry in index["policies"] if entry["channel_support"]["scope"] == "partial"
    ]
    assert len(partial) == 9
    for entry in partial:
        assert entry["channel_support"]["release_supported"] is True
        assert entry["channel_support"]["esr_supported"] is True
        topic_text = (POLICIES_ROOT / f"{entry['doc_id']}.dita").read_text(encoding="utf-8")
        assert 'outputclass="channel-support-badge channel-scope-partial"' in topic_text
        assert "absent from Firefox ESR 140.13" in topic_text


def test_each_generated_policy_example_validates_against_its_declared_channel() -> None:
    inventory = _inventory()
    index = _index()
    policies_by_id = {policy["policy_id"]: policy for policy in inventory["policies"]}

    for entry in index["policies"]:
        policy = policies_by_id[entry["policy_id"]]
        channels = set(policy["channels"])
        assert {example["channel"] for example in entry["examples"]} == channels
        for example in entry["examples"]:
            assert example["validates"] is True
            assert example["document"]["policies"].keys() == {entry["policy_id"]}
            issues = validate_profile_policies_for_channel(
                example["document"]["policies"],
                example["channel"],
            )
            assert issues == []


def test_each_generated_policy_topic_embeds_one_schema_valid_example_per_supported_channel() -> (
    None
):
    index = _index()
    examples_by_policy = {
        entry["policy_id"]: {example["channel"]: example for example in entry["examples"]}
        for entry in index["policies"]
    }

    for policy_id, examples in examples_by_policy.items():
        doc_id = next(
            entry["doc_id"] for entry in index["policies"] if entry["policy_id"] == policy_id
        )
        root = ET.parse(POLICIES_ROOT / f"{doc_id}.dita").getroot()
        example_divs = root.findall("./refbody/section[@id='a-examples']/sectiondiv")
        assert len(example_divs) == len(examples)
        for div in example_divs:
            assert div.attrib == {"outputclass": "schema-valid-example"}
            channel = div.findtext("p/codeph")
            codeblock = div.findtext("codeblock")
            assert channel in examples
            assert json.loads(codeblock) == examples[channel]["document"]


def test_policy_skeleton_generation_matches_checked_in_output() -> None:
    expected = {
        generated.path.relative_to(GENERATED_ROOT).as_posix(): generated.content
        for generated in generator.build_generated_files(INVENTORY_PATH, MODEL_PATH, GENERATED_ROOT)
    }
    actual = {
        path.relative_to(GENERATED_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(GENERATED_ROOT.rglob("*"))
        if path.is_file()
    }

    assert actual == expected


def test_policy_skeleton_generation_is_deterministic_in_temp_output(tmp_path: Path) -> None:
    output = tmp_path / "firefox"
    generator.generate(INVENTORY_PATH, MODEL_PATH, output)
    before = {
        path.relative_to(output).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    generator.generate(INVENTORY_PATH, MODEL_PATH, output)
    after = {
        path.relative_to(output).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }

    assert after == before


def test_policy_skeleton_regeneration_preserves_reviewed_regions(tmp_path: Path) -> None:
    output = tmp_path / "firefox"
    generator.generate(INVENTORY_PATH, MODEL_PATH, output)
    topic = output / "policies/fx-policy-DisableTelemetry.dita"
    reviewed = "      <p>Reviewed purpose survives regeneration.</p>"
    original = topic.read_text(encoding="utf-8")
    topic.write_text(
        original.replace(
            "      <p><codeph>DisableTelemetry</codeph> has a generated schema skeleton. "
            "Reviewed runtime guidance is added in the authored Firefox Policy Guide tasks.</p>",
            reviewed,
        ),
        encoding="utf-8",
    )

    generator.generate(INVENTORY_PATH, MODEL_PATH, output)

    assert reviewed in topic.read_text(encoding="utf-8")
