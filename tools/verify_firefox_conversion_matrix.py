#!/usr/bin/env python3
"""Run the offline BPM095-M4-06 directed Firefox conversion matrix gate.

The gate deliberately keeps its profile writes inside one in-memory SQLite
fixture.  Its retained report is value-free: it contains only artifact and
pair identities, counts, stable codes, and canonical digests.  Production
recipes remain empty; the reversible recipe check below is an isolated
synthetic registry-mechanism proof rather than a Firefox policy conversion.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import socket
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any, NoReturn
from unittest.mock import patch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import policy_validation
from app.core import profile_conversion_planner as planner
from app.core import profile_conversion_recipes as recipes
from app.core.profile_conversion_json import JsonValue, canonical_json
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.main import create_app
from tests.support import make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_ID = "bpm095-firefox-directed-conversion-matrix"
REPORT_VERSION = 1
EXPECTED_CHANNELS = (
    "release-153",
    "esr-153.0",
    "esr-140.13",
    "esr-115.38",
)
EXPECTED_PAIR_COUNT = len(EXPECTED_CHANNELS) * (len(EXPECTED_CHANNELS) - 1)
MAX_SCHEMA_LOADER_MISSES = len(EXPECTED_CHANNELS)
MAX_VALIDATOR_CACHE_ENTRIES = len(EXPECTED_CHANNELS)

type JsonObject = dict[str, JsonValue]

_SHAPE_KEYS = (
    "type",
    "enum",
    "minimum",
    "maximum",
    "pattern",
    "additionalProperties",
    "required",
    "oneOf",
)
_SOURCE_ONLY_VECTORS: dict[str, Any] = {
    "AIControls": {"Default": {"Value": "blocked", "Locked": True}},
    "BrowserDataBackup": {"AllowBackup": True},
    "AutofillAddressEnabled": True,
    "HttpAllowlist": ["https://matrix.example.invalid"],
}
_SHARED_DOCUMENT: dict[str, Any] = {
    "policies": {
        "DisableTelemetry": True,
        "ExtensionSettings": {
            "*": {
                "installation_mode": "blocked",
                "allowed_types": ["extension", "theme"],
            }
        },
        "Preferences": {
            "browser.tabs.warnOnClose": {
                "Value": True,
                "Status": "locked",
                "Type": "boolean",
            }
        },
        "Bookmarks": [],
    }
}


class FirefoxConversionMatrixGateError(RuntimeError):
    """Raised when the M4-06 runtime contract cannot be proven."""


def _default_emit(message: str) -> None:
    print(message, flush=True)


def _fail(message: str) -> NoReturn:
    raise FirefoxConversionMatrixGateError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _json_object(value: object, message: str) -> JsonObject:
    if not isinstance(value, dict):
        _fail(message)
    return value


def _json_array(value: object, message: str) -> list[JsonValue]:
    if not isinstance(value, list):
        _fail(message)
    return value


def _required_object(container: Mapping[str, JsonValue], key: str, message: str) -> JsonObject:
    return _json_object(container.get(key), message)


def _required_array(container: Mapping[str, JsonValue], key: str, message: str) -> list[JsonValue]:
    return _json_array(container.get(key), message)


def _required_string(container: Mapping[str, JsonValue], key: str, message: str) -> str:
    value = container.get(key)
    if not isinstance(value, str):
        _fail(message)
    return value


def _schema_object(container: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    return value if isinstance(value, dict) else {}


def _schema_array(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    return value if isinstance(value, list) else []


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _progress(
    emit: Callable[[str], None],
    *,
    phase: str,
    pair: str,
    completed: int,
    detail: str = "",
) -> None:
    suffix = f" {detail}" if detail else ""
    emit(f"phase={phase} pair={pair} [{completed}/{EXPECTED_PAIR_COUNT}]{suffix}")


def _pairs() -> tuple[tuple[str, str], ...]:
    _require(SUPPORTED_SCHEMA_CHANNELS == EXPECTED_CHANNELS, "runtime catalog order drift")
    pairs = tuple(
        (source, target)
        for source in SUPPORTED_SCHEMA_CHANNELS
        for target in SUPPORTED_SCHEMA_CHANNELS
        if source != target
    )
    _require(len(pairs) == EXPECTED_PAIR_COUNT, "directed pair count drift")
    return pairs


def _pair_id(source: str, target: str) -> str:
    return f"{source}--to--{target}"


def _context(*, lifecycle_state: str = "active") -> planner.ConversionPlanningContext:
    """Use fixed non-enterprise metadata so retained plan digests are stable."""

    return planner.ConversionPlanningContext(
        profile_id=9506,
        revision=6,
        lifecycle_state=lifecycle_state,
        metadata={
            "name": "BPM095-M4-06 matrix fixture",
            "description": None,
            "created_at": "2026-08-11T00:00:00+00:00",
            "updated_at": "2026-08-11T00:00:00+00:00",
            "deleted_at": None,
        },
    )


def _plan(
    document: Mapping[str, Any],
    *,
    source: str,
    target: str,
    context: planner.ConversionPlanningContext | None = None,
) -> planner.ConversionPlanningResult:
    return planner.plan_profile_conversion(
        document,
        source_artifact_id=source,
        target_artifact_id=target,
        context=context or _context(),
    )


def _shape(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    result: dict[str, Any] = {key: value[key] for key in _SHAPE_KEYS if key in value}
    if isinstance(value.get("properties"), dict):
        result["properties"] = {key: _shape(child) for key, child in value["properties"].items()}
    if isinstance(value.get("items"), dict):
        result["items"] = _shape(value["items"])
    if isinstance(value.get("additionalProperties"), dict):
        result["additionalProperties"] = _shape(value["additionalProperties"])
    if isinstance(value.get("oneOf"), list):
        result["oneOf"] = [_shape(child) for child in value["oneOf"]]
    return result


def _changed_paths(source: Any, target: Any, path: str = "") -> set[str]:
    if source == target:
        return set()
    if isinstance(source, dict) and isinstance(target, dict):
        return {
            changed
            for key in source.keys() | target.keys()
            for changed in _changed_paths(
                source.get(key, "__missing__"), target.get(key, "__missing__"), f"{path}/{key}"
            )
        }
    return {path or "/"}


def _schema_difference(source: str, target: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    source_properties = policy_validation.load_policy_schema_for_channel(source).get("properties")
    target_properties = policy_validation.load_policy_schema_for_channel(target).get("properties")
    if not isinstance(source_properties, dict):
        _fail(f"source schema properties missing: {source}")
    if not isinstance(target_properties, dict):
        _fail(f"target schema properties missing: {target}")
    source_only = tuple(sorted(set(source_properties) - set(target_properties)))
    changed = tuple(
        sorted(
            {
                path
                for policy in set(source_properties) & set(target_properties)
                for path in _changed_paths(
                    _shape(source_properties[policy]),
                    _shape(target_properties[policy]),
                    f"/policies/{policy}",
                )
            }
        )
    )
    return source_only, changed


def _source_only_document(source_only: tuple[str, ...]) -> tuple[str, dict[str, Any]]:
    for policy_id in _SOURCE_ONLY_VECTORS:
        if policy_id in source_only:
            return policy_id, {
                "policies": {policy_id: copy.deepcopy(_SOURCE_ONLY_VECTORS[policy_id])}
            }
    _fail(f"no approved source-only blocker vector for {source_only!r}")


def _changed_enum_document(source: str, target: str) -> dict[str, Any] | None:
    source_properties = _schema_object(
        policy_validation.load_policy_schema_for_channel(source), "properties"
    )
    target_properties = _schema_object(
        policy_validation.load_policy_schema_for_channel(target), "properties"
    )
    source_cookies = _schema_object(source_properties, "Cookies")
    target_cookies = _schema_object(target_properties, "Cookies")
    source_behavior = _schema_object(_schema_object(source_cookies, "properties"), "Behavior")
    target_behavior = _schema_object(_schema_object(target_cookies, "properties"), "Behavior")
    source_values = _schema_array(source_behavior, "enum")
    target_values = _schema_array(target_behavior, "enum")
    if "partition-foreign" not in source_values or "partition-foreign" in target_values:
        return None
    return {"policies": {"Cookies": {"Behavior": "partition-foreign"}}}


def _assert_plan_target_validation(plan: Mapping[str, JsonValue], *, expected_status: str) -> None:
    target_validation = _required_object(
        plan, "target_validation", "target validation omitted from valid-source plan"
    )
    target = _required_object(plan, "target", "target identity omitted from valid-source plan")
    _require(
        target_validation.get("status") == expected_status,
        f"target validation status drift: expected {expected_status}",
    )
    _require(
        target_validation.get("validated_document_digest")
        == target.get("candidate_document_digest"),
        "target validation was not bound to candidate digest",
    )
    artifact = _required_object(target, "artifact", "target artifact omitted")
    _require(
        target_validation.get("validation_schema_sha256")
        == artifact.get("validation_schema_sha256"),
        "target validation schema identity drift",
    )


def _assert_source_immutable(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    _require(before == after, "source document mutated during conversion planning")


def _positive_evidence(
    document: dict[str, Any],
    *,
    source: str,
    target: str,
    scenario: str,
) -> dict[str, Any]:
    before = copy.deepcopy(document)
    first = _plan(document, source=source, target=target).plan
    second = _plan(document, source=source, target=target).plan
    _assert_source_immutable(before, document)
    _require(first == second, f"nondeterministic positive plan for {source}->{target}:{scenario}")
    compatibility = _required_object(first, "compatibility", "positive plan compatibility omitted")
    _require(compatibility.get("applicable") is True, "positive plan is not applicable")
    _assert_plan_target_validation(first, expected_status="valid")
    source_identity = _required_object(first, "source", "positive plan source omitted")
    target_identity = _required_object(first, "target", "positive plan target omitted")
    target_validation = _required_object(
        first, "target_validation", "positive plan target validation omitted"
    )
    return {
        "scenario": scenario,
        "source_document_digest": _required_string(
            source_identity, "document_digest", "positive plan source digest omitted"
        ),
        "candidate_document_digest": _required_string(
            target_identity, "candidate_document_digest", "positive plan candidate digest omitted"
        ),
        "validated_document_digest": _required_string(
            target_validation,
            "validated_document_digest",
            "positive plan validation digest omitted",
        ),
        "target_validation_schema_sha256": _required_string(
            target_validation, "validation_schema_sha256", "positive plan validation schema omitted"
        ),
        "plan_digest": _required_string(first, "plan_digest", "positive plan digest omitted"),
        "target_validation_status": "valid",
        "applicable": True,
        "counts": _required_object(compatibility, "counts", "positive plan counts omitted"),
    }


def _source_invalid_evidence(source: str, target: str) -> dict[str, Any]:
    try:
        _plan({"policies": {"M4_06_Invalid_Policy": True}}, source=source, target=target)
    except planner.ConversionPlanningError as error:
        _require(error.code == "conversion_source_invalid", "invalid source code drift")
        return {"scenario": "invalid-source", "code": error.code}
    _fail("invalid source unexpectedly produced a conversion plan")


def _precondition_evidence(source: str, target: str) -> dict[str, Any]:
    try:
        _plan(
            {"policies": {}},
            source=source,
            target=target,
            context=_context(lifecycle_state="deleted"),
        )
    except planner.ConversionPlanningError as error:
        _require(error.code == "conversion_source_not_active", "pair precondition code drift")
        return {"scenario": "pair-bound-precondition", "code": error.code}
    _fail("inactive pair source unexpectedly produced a conversion plan")


def _blocker_evidence(source: str, target: str, source_only: tuple[str, ...]) -> dict[str, Any]:
    policy_id, document = _source_only_document(source_only)
    before = copy.deepcopy(document)
    result = _plan(document, source=source, target=target)
    plan = result.plan
    _assert_source_immutable(before, document)
    compatibility = _required_object(plan, "compatibility", "source-only compatibility omitted")
    _require(compatibility.get("applicable") is False, "source-only plan was applicable")
    _assert_plan_target_validation(plan, expected_status="invalid")
    blockers = _required_array(plan, "blockers", "source-only blocker diagnostics omitted")
    blocker_codes = tuple(
        sorted(
            {
                _required_string(
                    _json_object(entry, "source-only blocker is malformed"),
                    "code",
                    "source-only blocker code omitted",
                )
                for entry in blockers
            }
        )
    )
    _require(bool(blocker_codes), "source-only blocker omitted diagnostics")
    source_identity = _required_object(plan, "source", "source-only source identity omitted")
    target_identity = _required_object(plan, "target", "source-only target identity omitted")
    target_validation = _required_object(
        plan, "target_validation", "source-only target validation omitted"
    )
    return {
        "scenario": "source-only-policy",
        "policy_id": policy_id,
        "source_document_digest": _required_string(
            source_identity, "document_digest", "source-only source digest omitted"
        ),
        "candidate_document_digest": _required_string(
            target_identity, "candidate_document_digest", "source-only candidate digest omitted"
        ),
        "validated_document_digest": _required_string(
            target_validation, "validated_document_digest", "source-only validation digest omitted"
        ),
        "target_validation_schema_sha256": _required_string(
            target_validation, "validation_schema_sha256", "source-only validation schema omitted"
        ),
        "target_validation_status": "invalid",
        "applicable": False,
        "blocker_codes": list(blocker_codes),
        "counts": _required_object(compatibility, "counts", "source-only counts omitted"),
    }


def _changed_enum_evidence(source: str, target: str) -> dict[str, Any] | None:
    document = _changed_enum_document(source, target)
    if document is None:
        return None
    before = copy.deepcopy(document)
    result = _plan(document, source=source, target=target)
    plan = result.plan
    _assert_source_immutable(before, document)
    compatibility = _required_object(plan, "compatibility", "enum-drift compatibility omitted")
    _require(compatibility.get("applicable") is False, "enum-drift plan was applicable")
    _assert_plan_target_validation(plan, expected_status="invalid")
    blockers = _required_array(plan, "blockers", "enum-drift blocker diagnostics omitted")
    blocker_codes = tuple(
        sorted(
            {
                _required_string(
                    _json_object(entry, "enum-drift blocker is malformed"),
                    "code",
                    "enum-drift blocker code omitted",
                )
                for entry in blockers
            }
        )
    )
    _require(bool(blocker_codes), "enum-drift blocker omitted diagnostics")
    source_identity = _required_object(plan, "source", "enum-drift source identity omitted")
    target_identity = _required_object(plan, "target", "enum-drift target identity omitted")
    target_validation = _required_object(
        plan, "target_validation", "enum-drift target validation omitted"
    )
    return {
        "scenario": "changed-enum",
        "field_path": "/policies/Cookies/Behavior",
        "source_document_digest": _required_string(
            source_identity, "document_digest", "enum-drift source digest omitted"
        ),
        "candidate_document_digest": _required_string(
            target_identity, "candidate_document_digest", "enum-drift candidate digest omitted"
        ),
        "validated_document_digest": _required_string(
            target_validation, "validated_document_digest", "enum-drift validation digest omitted"
        ),
        "target_validation_schema_sha256": _required_string(
            target_validation, "validation_schema_sha256", "enum-drift validation schema omitted"
        ),
        "target_validation_status": "invalid",
        "applicable": False,
        "blocker_codes": list(blocker_codes),
        "counts": _required_object(compatibility, "counts", "enum-drift counts omitted"),
    }


def _create_profile(
    client: Any, *, source: str, document: Mapping[str, Any], name: str
) -> dict[str, Any]:
    response = client.post(
        "/api/profiles",
        json={"name": name, "schema_version": source, "flags": document["policies"]},
    )
    _require(response.status_code == 201, "disposable matrix profile creation failed")
    body = response.json()
    _require(isinstance(body, dict), "disposable matrix profile response is invalid")
    return body


def _api_preview(client: Any, *, profile: Mapping[str, Any], target: str) -> dict[str, Any]:
    response = client.post(
        f"/api/profiles/{profile['id']}/conversion-preview",
        json={"target_artifact_id": target},
    )
    _require(response.status_code == 200, "conversion preview API did not return an available plan")
    body = response.json()
    _require(isinstance(body, dict) and body.get("available") is True, "API availability drift")
    return body


def _profile_unchanged(client: Any, profile_id: int, before: Mapping[str, Any]) -> None:
    after_response = client.get(f"/api/profiles/{profile_id}")
    _require(after_response.status_code == 200, "disposable source profile became unreadable")
    _require(after_response.json() == before, "preview mutated disposable source profile")


def _api_preview_matrix(
    client: Any, pairs: tuple[tuple[str, str], ...]
) -> tuple[dict[str, Any], ...]:
    evidence: list[dict[str, Any]] = []
    for position, (source, target) in enumerate(pairs, start=1):
        pair_id = _pair_id(source, target)
        empty_profile = _create_profile(
            client,
            source=source,
            document={"policies": {}},
            name=f"m4-06-{position}-empty",
        )
        empty_before = client.get(f"/api/profiles/{empty_profile['id']}").json()
        empty_preview = _api_preview(client, profile=empty_profile, target=target)
        _require(empty_preview["compatibility"]["applicable"] is True, "empty API plan blocked")
        _assert_plan_target_validation(empty_preview, expected_status="valid")
        _profile_unchanged(client, int(empty_profile["id"]), empty_before)

        shared_profile = _create_profile(
            client,
            source=source,
            document=_SHARED_DOCUMENT,
            name=f"m4-06-{position}-shared",
        )
        shared_before = client.get(f"/api/profiles/{shared_profile['id']}").json()
        first = _api_preview(client, profile=shared_profile, target=target)
        second = _api_preview(client, profile=shared_profile, target=target)
        _require(first == second, "API preview is not repeatable")
        _require(first["compatibility"]["applicable"] is True, "shared API plan blocked")
        _assert_plan_target_validation(first, expected_status="valid")
        _profile_unchanged(client, int(shared_profile["id"]), shared_before)
        evidence.append(
            {
                "pair_id": pair_id,
                "available": True,
                "positive_preview_count": 2,
                "repeatable": True,
                "source_immutable": True,
                "target_validation_statuses": ["valid", "valid"],
            }
        )
    return tuple(evidence)


def _apply_payload(preview: Mapping[str, Any]) -> dict[str, Any]:
    source_artifact = preview["source"]["artifact"]
    target_artifact = preview["target"]["artifact"]
    return {
        "kind": "profile-conversion-apply-request",
        "contract_version": 1,
        "profile_id": preview["profile"]["id"],
        "expected_revision": preview["profile"]["revision"],
        "source": {
            "line_id": source_artifact["line_id"],
            "artifact_id": source_artifact["artifact_id"],
        },
        "target": {
            "line_id": target_artifact["line_id"],
            "artifact_id": target_artifact["artifact_id"],
        },
        "target_artifact_id": target_artifact["artifact_id"],
        "plan_digest": preview["plan_digest"],
        "source_document_digest": preview["source"]["document_digest"],
        "source_compliance_digest": preview["source"]["compliance_digest"],
        "source_metadata_digest": preview["profile"]["metadata_digest"],
        "source_validation_schema_sha256": source_artifact["validation_schema_sha256"],
        "target_validation_schema_sha256": target_artifact["validation_schema_sha256"],
        "recipe_registry_version": preview["recipe_registry"]["registry_version"],
        "recipe_registry_digest": preview["recipe_registry"]["registry_digest"],
    }


def _api_error_code(response: Any, *, expected: str) -> None:
    _require(response.status_code == 409, f"expected stale response for {expected}")
    body = response.json()
    _require(body.get("detail", {}).get("code") == expected, f"stale code drift for {expected}")
    _require(body["detail"].get("mutation") == "none", "failed apply reported a mutation")


def _apply_identity_proof(client: Any) -> dict[str, Any]:
    source = "esr-115.38"
    target = "esr-140.13"
    profile = _create_profile(
        client,
        source=source,
        document=_SHARED_DOCUMENT,
        name="m4-06-apply-identity",
    )
    before = client.get(f"/api/profiles/{profile['id']}").json()
    preview = _api_preview(client, profile=profile, target=target)
    _require(preview["compatibility"]["applicable"] is True, "apply fixture preview blocked")
    _assert_plan_target_validation(preview, expected_status="valid")
    payload = _apply_payload(preview)

    stale_plan = copy.deepcopy(payload)
    stale_plan["plan_digest"] = "f" * 64
    _api_error_code(
        client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=stale_plan),
        expected="conversion_plan_stale",
    )
    _profile_unchanged(client, int(profile["id"]), before)

    stale_registry = copy.deepcopy(payload)
    stale_registry["recipe_registry_digest"] = "e" * 64
    _api_error_code(
        client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=stale_registry),
        expected="conversion_recipe_registry_stale",
    )
    _profile_unchanged(client, int(profile["id"]), before)

    stale_source_digest = copy.deepcopy(payload)
    stale_source_digest["source_document_digest"] = "d" * 64
    _api_error_code(
        client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=stale_source_digest),
        expected="conversion_source_identity_stale",
    )
    _profile_unchanged(client, int(profile["id"]), before)

    applied_response = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
    _require(applied_response.status_code == 200, "current conversion apply failed")
    applied = applied_response.json()
    _require(applied["source_revision"] == before["revision"], "apply source revision drift")
    _require(applied["result_revision"] == before["revision"] + 1, "apply revision is not one step")
    _require(
        applied["target_validation"].get("status") == "valid",
        "apply result target validation drift",
    )
    _require(
        applied["target_validation"].get("validated_document_digest")
        == applied.get("result_document_digest"),
        "apply result was not bound to validated candidate digest",
    )
    after = client.get(f"/api/profiles/{profile['id']}").json()
    _require(after["schema_version"] == target, "apply target channel drift")
    _require(after["flags"] == _SHARED_DOCUMENT["policies"], "apply did not use server candidate")

    replay = client.post(f"/api/profiles/{profile['id']}/conversion-apply", json=payload)
    _api_error_code(replay, expected="conversion_revision_stale")
    _require(
        replay.json()["detail"].get("retry_preview_required") is True, "replay retry flag drift"
    )
    _profile_unchanged(client, int(profile["id"]), after)
    return {
        "pair_id": _pair_id(source, target),
        "server_rederived": True,
        "source_revision_increment": 1,
        "replay_code": "conversion_revision_stale",
        "identity_error_codes": [
            "conversion_plan_stale",
            "conversion_recipe_registry_stale",
            "conversion_source_identity_stale",
        ],
    }


def _synthetic_registry_proof() -> dict[str, Any]:
    """Exercise the registry mechanism without fabricating a production recipe."""

    recipe = recipes.ConversionRecipe(
        recipe_id="bpm095.m4-06.synthetic-mode",
        recipe_version=1,
        source_artifact_id="release-153",
        target_artifact_id="esr-153.0",
        source_validation_schema_sha256="a" * 64,
        target_validation_schema_sha256="b" * 64,
        source_path="/policies/Synthetic/mode",
        target_path="/policies/Synthetic/mode",
        input_predicate_id="legacy-only",
        target_constraint_id="modern-only",
        evidence_digest="c" * 64,
        predicate=lambda value: value == "legacy",
        transform=lambda value: "modern",
        inverse=lambda value: "legacy",
        target_constraint=lambda value: value == "modern",
    )
    registry = recipes.ConversionRecipeRegistry(recipes=(recipe,))
    document = {"policies": {"Synthetic": {"mode": "legacy"}}}
    before = copy.deepcopy(document)
    validation_calls: list[dict[str, Any]] = []

    def load_artifact(channel: Any, *, source: bool) -> tuple[dict[str, Any], dict[str, Any]]:
        return (
            {
                "line_id": channel.line_id,
                "artifact_id": channel.artifact_id,
                "channel_id": channel.channel_id,
                "artifact_version": channel.artifact_version,
                "source_tag": channel.source_tag,
                "schema_bundle_sha256": "d" * 64,
                "validation_schema_sha256": "a" * 64 if source else "b" * 64,
            },
            {"expected": "legacy" if source else "modern"},
        )

    def validate(
        policies: dict[str, Any], schema: dict[str, Any]
    ) -> list[policy_validation.PolicyValidationIssue]:
        validation_calls.append(copy.deepcopy(policies))
        if policies.get("Synthetic", {}).get("mode") == schema["expected"]:
            return []
        return [
            policy_validation.PolicyValidationIssue(
                policy="Synthetic", path=["Synthetic", "mode"], message="synthetic invalid"
            )
        ]

    with (
        patch.object(planner, "_load_artifact", load_artifact),
        patch.object(planner, "validate_profile_policies", validate),
    ):
        result = _plan(
            document,
            source="release-153",
            target="esr-153.0",
            context=replace(_context(), recipe_registry=registry),
        )
    plan = result.plan
    _assert_source_immutable(before, document)
    _require(len(validation_calls) == 2, "synthetic recipe skipped source or target validation")
    _require(
        result.candidate_document == {"policies": {"Synthetic": {"mode": "modern"}}},
        "synthetic recipe output drift",
    )
    compatibility = _required_object(
        plan, "compatibility", "synthetic recipe compatibility omitted"
    )
    _require(compatibility.get("applicable") is True, "synthetic recipe plan blocked")
    _assert_plan_target_validation(plan, expected_status="valid")
    counts = _required_object(compatibility, "counts", "synthetic recipe counts omitted")
    _require(counts.get("transformed") == 1, "synthetic transform count drift")
    return {
        "scenario": "synthetic-reversible-registry-mechanism",
        "production_recipe_count": len(recipes.EMPTY_CONVERSION_RECIPE_REGISTRY.recipes),
        "synthetic_recipe_id": recipe.recipe_id,
        "synthetic_registry_digest": registry.as_identity()["registry_digest"],
        "target_validation_status": "valid",
        "source_immutable": True,
        "validation_call_count": len(validation_calls),
    }


@contextmanager
def _offline_network_guard() -> Iterator[None]:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden during conversion matrix gate")

    with (
        patch.object(socket, "create_connection", blocked),
        patch.object(socket.socket, "connect", blocked),
    ):
        yield


def _validate_report(report: Mapping[str, JsonValue]) -> None:
    _require(report.get("report_version") == REPORT_VERSION, "report version drift")
    _require(report.get("gate_id") == GATE_ID, "report gate identity drift")
    _require(report.get("offline") is True, "matrix report must be offline")
    _require(report.get("status") == "passed", "matrix report status drift")
    _require(report.get("pair_count") == EXPECTED_PAIR_COUNT, "report pair count drift")
    _require(report.get("completed_pairs") == EXPECTED_PAIR_COUNT, "report completion drift")
    _require(
        report.get("production_registry") == recipes.EMPTY_CONVERSION_RECIPE_REGISTRY.as_identity(),
        "production registry digest drift",
    )
    production_registry = _required_object(
        report, "production_registry", "production registry identity omitted"
    )
    _require(production_registry.get("recipes") == [], "production recipe is forbidden")

    pairs = _required_array(report, "pairs", "missing directed pair")
    _require(len(pairs) == EXPECTED_PAIR_COUNT, "missing directed pair")
    pair_records = [_json_object(pair, "directed pair is malformed") for pair in pairs]
    expected_ids = [_pair_id(source, target) for source, target in _pairs()]
    _require(
        [pair.get("pair_id") for pair in pair_records] == expected_ids,
        "pair order or coverage drift",
    )
    for pair in pair_records:
        _require(pair.get("available") is True, "pair availability drift")
        positive = _required_array(pair, "positive", "missing positive scenarios")
        positive_records = [
            _json_object(item, "positive scenario is malformed") for item in positive
        ]
        _require(
            [item.get("scenario") for item in positive_records]
            == ["empty", "shared-nested-dynamic-array"],
            "positive scenario coverage drift",
        )
        for item in positive_records:
            _require(item.get("applicable") is True, "positive plan applicability drift")
            _require(item.get("target_validation_status") == "valid", "target validation skipped")
            _require(
                item.get("candidate_document_digest") == item.get("validated_document_digest"),
                "positive validation digest drift",
            )
        negative = _required_array(pair, "negative", "missing negative scenarios")
        negative_records = [
            _json_object(item, "negative scenario is malformed") for item in negative
        ]
        scenario_names = {item.get("scenario") for item in negative_records}
        _require("invalid-source" in scenario_names, "invalid source scenario omitted")
        difference = _required_object(
            pair, "schema_difference", "schema difference evidence omitted"
        )
        source_only_policy_ids = _required_array(
            difference, "source_only_policy_ids", "source-only difference evidence omitted"
        )
        if source_only_policy_ids:
            _require("source-only-policy" in scenario_names, "source-only blocker scenario omitted")
        else:
            _require(
                "pair-bound-precondition" in scenario_names, "pair precondition scenario omitted"
            )
        changed_paths = _required_array(
            difference, "changed_shape_paths", "changed shape path evidence omitted"
        )
        _require(
            difference.get("changed_shape_path_count") == len(changed_paths),
            "changed shape count drift",
        )
        _require(
            difference.get("changed_shape_digest") == _sha256({"paths": changed_paths}),
            "changed shape digest drift",
        )
        for item in negative_records:
            if item.get("scenario") in {"source-only-policy", "changed-enum"}:
                _require(
                    item.get("target_validation_status") == "invalid",
                    "blocked target validation skipped",
                )
                _require(
                    item.get("candidate_document_digest") == item.get("validated_document_digest"),
                    "blocked validation digest drift",
                )

    api_pairs = _required_array(report, "api_preview_pairs", "API pair coverage drift")
    _require(len(api_pairs) == EXPECTED_PAIR_COUNT, "API pair coverage drift")
    api_pair_records = [_json_object(item, "API pair evidence is malformed") for item in api_pairs]
    _require(
        [item.get("pair_id") for item in api_pair_records] == expected_ids, "API pair order drift"
    )
    for item in api_pair_records:
        _require(item.get("available") is True, "API pair unavailable")
        _require(item.get("source_immutable") is True, "API preview mutated source")
        _require(item.get("repeatable") is True, "API preview nondeterministic")
        _require(
            item.get("target_validation_statuses") == ["valid", "valid"],
            "API target validation drift",
        )

    runtime = _required_object(report, "runtime_budget", "runtime budget missing")
    _require(
        runtime.get("schema_loader_misses") == MAX_SCHEMA_LOADER_MISSES, "schema load reuse drift"
    )
    validator_cache_entries = runtime.get("validator_cache_entries")
    _require(
        isinstance(validator_cache_entries, int)
        and validator_cache_entries <= MAX_VALIDATOR_CACHE_ENTRIES,
        "validator reuse budget drift",
    )
    _require(runtime.get("disposable_database_setups") == 1, "matrix opened extra databases")
    _require(runtime.get("wall_clock_budget") == "not-used", "wall-clock gate is forbidden")


def _must_fail(label: str, callback: Callable[[], Any]) -> str:
    try:
        callback()
    except FirefoxConversionMatrixGateError:
        return label
    _fail(f"fail-closed mutation unexpectedly succeeded: {label}")


def run_fail_closed_mutation_checks(report: Mapping[str, Any]) -> tuple[str, ...]:
    """Prove the owner gate rejects the M4-06 safety regressions explicitly."""

    checks: list[str] = []
    missing_pair = copy.deepcopy(report)
    missing_pair["pairs"].pop()
    checks.append(_must_fail("missing_pair_rejected", lambda: _validate_report(missing_pair)))

    missing_scenario = copy.deepcopy(report)
    missing_scenario["pairs"][0]["positive"].pop()
    checks.append(
        _must_fail("missing_scenario_rejected", lambda: _validate_report(missing_scenario))
    )

    skipped_validation = copy.deepcopy(report)
    skipped_validation["pairs"][0]["positive"][0]["target_validation_status"] = "not-run"
    checks.append(
        _must_fail("target_validation_skip_rejected", lambda: _validate_report(skipped_validation))
    )

    checks.append(
        _must_fail(
            "source_mutation_rejected",
            lambda: _assert_source_immutable({"policies": {}}, {"policies": {"x": True}}),
        )
    )
    checks.append(
        _must_fail(
            "nondeterminism_rejected",
            lambda: _require({"plan": "one"} == {"plan": "two"}, "nondeterministic plan"),
        )
    )

    digest_drift = copy.deepcopy(report)
    digest_drift["pairs"][0]["positive"][0]["validated_document_digest"] = "0" * 64
    checks.append(_must_fail("digest_drift_rejected", lambda: _validate_report(digest_drift)))

    registry_drift = copy.deepcopy(report)
    registry_drift["production_registry"]["registry_digest"] = "0" * 64
    checks.append(_must_fail("registry_drift_rejected", lambda: _validate_report(registry_drift)))

    accidental_recipe = copy.deepcopy(report)
    accidental_recipe["production_registry"]["recipes"] = [{"recipe_id": "forbidden"}]
    checks.append(
        _must_fail("production_recipe_rejected", lambda: _validate_report(accidental_recipe))
    )
    return tuple(checks)


def _assert_value_free(report: Mapping[str, Any]) -> None:
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "matrix.example.invalid",
        "partition-foreign",
        "BPM095-M4-06 matrix fixture",
        "m4-06-apply-identity",
    ):
        _require(forbidden not in serialized, "matrix report exposed a raw fixture value")


def run_gate(
    *,
    report_path: Path | None = None,
    emit: Callable[[str], None] = _default_emit,
) -> dict[str, Any]:
    """Run all deterministic planner and API matrix checks without network access."""

    pairs = _pairs()
    policy_validation.clear_policy_validation_caches()
    _require(
        recipes.EMPTY_CONVERSION_RECIPE_REGISTRY.recipes == (), "production registry not empty"
    )

    pair_reports: list[dict[str, Any]] = []
    with _offline_network_guard():
        for completed, (source, target) in enumerate(pairs, start=1):
            pair_id = _pair_id(source, target)
            _progress(emit, phase="planner", pair=f"{source}->{target}", completed=completed)
            source_only, changed_paths = _schema_difference(source, target)
            positive = [
                _positive_evidence(
                    {"policies": {}}, source=source, target=target, scenario="empty"
                ),
                _positive_evidence(
                    copy.deepcopy(_SHARED_DOCUMENT),
                    source=source,
                    target=target,
                    scenario="shared-nested-dynamic-array",
                ),
            ]
            negative: list[dict[str, Any]] = [_source_invalid_evidence(source, target)]
            if source_only:
                negative.append(_blocker_evidence(source, target, source_only))
            else:
                negative.append(_precondition_evidence(source, target))
            changed_enum = _changed_enum_evidence(source, target)
            if changed_enum is not None:
                negative.append(changed_enum)
            difference_projection = {
                "source_only_policy_ids": list(source_only),
                "changed_shape_path_count": len(changed_paths),
                "changed_shape_paths": list(changed_paths),
                "changed_shape_digest": _sha256({"paths": list(changed_paths)}),
            }
            pair_reports.append(
                {
                    "pair_id": pair_id,
                    "source_artifact_id": source,
                    "target_artifact_id": target,
                    "available": True,
                    "schema_difference": difference_projection,
                    "positive": positive,
                    "negative": negative,
                }
            )

        _progress(emit, phase="api-preview", pair="matrix", completed=EXPECTED_PAIR_COUNT)
        with make_test_client(create_app()) as client:
            api_preview_pairs = _api_preview_matrix(client, pairs)
            apply_identity = _apply_identity_proof(client)
        synthetic_recipe = _synthetic_registry_proof()

    cache_stats = policy_validation.policy_validation_cache_stats()
    _require(
        cache_stats["schema_loader_misses"] == MAX_SCHEMA_LOADER_MISSES,
        "schema loader was not bounded to one parse per channel: "
        f"{cache_stats['schema_loader_misses']}",
    )
    validator_entries = cache_stats["validator_cache_entries"]
    _require(
        validator_entries <= MAX_VALIDATOR_CACHE_ENTRIES,
        f"validator cache exceeded channel budget: {validator_entries}",
    )
    report: dict[str, Any] = {
        "report_version": REPORT_VERSION,
        "gate_id": GATE_ID,
        "offline": True,
        "status": "passed",
        "channels": list(EXPECTED_CHANNELS),
        "pair_count": EXPECTED_PAIR_COUNT,
        "completed_pairs": EXPECTED_PAIR_COUNT,
        "production_transformations": {
            "count": 0,
            "disposition": "no-production-recipe-after-four-channel-diff-audit",
        },
        "production_registry": recipes.EMPTY_CONVERSION_RECIPE_REGISTRY.as_identity(),
        "pairs": pair_reports,
        "api_preview_pairs": list(api_preview_pairs),
        "apply_identity": apply_identity,
        "synthetic_registry_mechanism": synthetic_recipe,
        "runtime_budget": {
            "schema_loader_misses": cache_stats["schema_loader_misses"],
            "schema_loader_miss_budget": MAX_SCHEMA_LOADER_MISSES,
            "validator_cache_entries": validator_entries,
            "validator_cache_entry_budget": MAX_VALIDATOR_CACHE_ENTRIES,
            "disposable_database_setups": 1,
            "wall_clock_budget": "not-used",
        },
    }
    _validate_report(report)
    _assert_value_free(report)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    emit(f"phase=complete pair=matrix [{EXPECTED_PAIR_COUNT}/{EXPECTED_PAIR_COUNT}] status=passed")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="write the deterministic JSON report here")
    args = parser.parse_args(argv)
    try:
        run_gate(report_path=args.report)
    except (FirefoxConversionMatrixGateError, AssertionError) as error:
        print(
            f"phase=complete pair=matrix [0/{EXPECTED_PAIR_COUNT}] status=failed code={type(error).__name__}",
            flush=True,
        )
        print(str(error), file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
