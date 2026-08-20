from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
POLICY_CONTEXT_TARGETS = DOCUMENTATION_ROOT / "config/firefox-policy-context-targets-0.9.0.json"
SEMANTIC_AUTHORITY = DOCUMENTATION_ROOT / "config/documentation-semantic-contracts-0.9.4.json"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def test_manifest_generator_uses_accepted_schema_files_and_exact_locale_matrix() -> None:
    for schema_path in (build_docs.MANIFEST_SCHEMA, build_docs.UI_TARGET_SCHEMA):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema_path.is_file()

    assert build_docs.LOCALES == ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def test_guide_landing_topics_are_manifest_ready_without_product_topics() -> None:
    guide_ids = [guide_id for guide_id, _filename, _anchor, _url_root in build_docs.GUIDE_MAPS]
    anchors = [anchor for _guide_id, _filename, anchor, _url_root in build_docs.GUIDE_MAPS]

    assert guide_ids == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]
    assert all(anchor.startswith("a-") for anchor in anchors)
    assert len(set(anchors)) == len(anchors)


def _runtime_artifact_policy_errors(policy: dict, authority: dict) -> list[str]:
    runtime = policy["current_runtime_contract"]
    errors: list[str] = []
    if runtime["runtime_ready"] is not authority["required_runtime_state"]:
        errors.append("runtime readiness no longer reflects the current delivery boundary")
    if set(authority["generated_non_prerequisites"]) & set(runtime["required_before_shipping"]):
        errors.append("generated state became a runtime shipping prerequisite")
    if len(runtime["required_before_shipping"]) < 3:
        errors.append("shipping boundary lost a delivery or review prerequisite")
    return errors


def test_manifest_artifact_policy_uses_current_shipping_semantics() -> None:
    policy = json.loads(
        (DOCUMENTATION_ROOT / "config/artifact-policy.json").read_text(encoding="utf-8")
    )
    authority = json.loads(SEMANTIC_AUTHORITY.read_text(encoding="utf-8"))["authorities"][
        "runtime_artifact_policy"
    ]

    assert _runtime_artifact_policy_errors(policy, authority) == []

    stale_policy = copy.deepcopy(policy)
    stale_policy["current_runtime_contract"]["required_before_shipping"].append("manifest.json")
    assert _runtime_artifact_policy_errors(stale_policy, authority) == [
        "generated state became a runtime shipping prerequisite"
    ]


def test_policy_context_targets_are_inventory_backed_and_unambiguous() -> None:
    context = json.loads(POLICY_CONTEXT_TARGETS.read_text(encoding="utf-8"))
    assignments = build_docs._policy_context_assignments(context)

    assert context["backlog_item"] == "BPM090-M5-07"
    assert len(build_docs._policy_ids()) == 123
    assert len(build_docs._cis_recommendation_ids()) == 55
    assert len(build_docs._api_operation_topic_ids()) == 17
    assert len(build_docs._capability_topic_ids()) == 106
    assert set(assignments) < build_docs._policy_ids()
    assert assignments["AIControls"]["family_id"] == "privacy-ai"
    assert assignments["ExtensionSettings"]["family_id"] == "extensions"
    assert assignments["Preferences"]["family_id"] == "managed-preferences"
    assert context["default_policy_target"]["topic_id"] == "fx-concept-policy-selection"
    assert (
        context["default_policy_target"]["validation_topic_id"]
        == "ug-troubleshoot-policy-validation"
    )


def test_policy_context_targets_reject_orphaned_and_ambiguous_policy_links() -> None:
    context = json.loads(POLICY_CONTEXT_TARGETS.read_text(encoding="utf-8"))

    orphaned = json.loads(json.dumps(context))
    orphaned["family_targets"][0]["policy_ids"].append("NotARealFirefoxPolicy")
    with pytest.raises(build_docs.BuildError, match="unknown policy"):
        build_docs._policy_context_assignments(orphaned)

    ambiguous = json.loads(json.dumps(context))
    ambiguous["family_targets"][1]["policy_ids"].append("ExtensionSettings")
    with pytest.raises(build_docs.BuildError, match="more than once"):
        build_docs._policy_context_assignments(ambiguous)


def test_target_map_semantics_reject_unknown_policy_sources() -> None:
    manifest = {
        "topics": {
            "fx-concept-policy-selection": {
                "guide_id": "firefox-policy-guide",
                "dita_key": "topic.fx-concept-policy-selection",
                "source_slug": "fx-concept-policy-selection",
                "url_path": "fx-concept-policy-selection",
                "kind": "concept",
                "title": {locale: "Policy selection" for locale in build_docs.LOCALES},
                "anchors": {
                    "a-review-value-shape": {
                        "title": {locale: "Value shape" for locale in build_docs.LOCALES},
                        "aliases": [],
                    }
                },
                "output": {
                    locale: f"{locale}/firefox/fx-concept-policy-selection.html"
                    for locale in build_docs.LOCALES
                },
            }
        }
    }
    target_map = {
        "targets": {
            "policy:NotARealFirefoxPolicy": {
                "kind": "policy",
                "source_id": "NotARealFirefoxPolicy",
                "source_inventory": (
                    "documentation/config/firefox-policy-context-targets-0.9.0.json"
                ),
                "topic_id": "fx-concept-policy-selection",
                "anchor_id": "a-review-value-shape",
            }
        }
    }

    with pytest.raises(build_docs.BuildError, match="unknown policy source"):
        build_docs._validate_target_map_semantics(target_map, manifest)
