from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from app.core.lifecycle_transition_plan import build_lifecycle_transition_plan
from app.core.profile_conversion_json import canonical_json
from app.core.retirement_convertibility_preflight import (
    RetirementConvertibilityPreflightError,
    SchemaArtifactBinding,
    load_exact_schema_containment_evidence,
    prove_retirement_total_convertibility,
)
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG

REPO_ROOT = Path(__file__).resolve().parents[4]
PROOF_PATH = (
    REPO_ROOT
    / "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "docs/architecture/schemas/firefox-retirement-exact-schema-containment-proof-v1.schema.json"
)
_EXACT_PROOF_ARTIFACT_DOMAIN = b"bpm-retired-esr-exact-proof-artifact:v1\n"


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    assert isinstance(value, dict)
    return value


def _exact_retirement_plan():
    candidate = tuple(
        replace(channel, support_state="retired", selectable=False)
        if channel.line_id == "esr-140"
        else replace(channel, retirement_successor_line_id="esr-153")
        if channel.line_id == "esr-115"
        else channel
        for channel in SCHEMA_CHANNEL_CATALOG
    )
    return build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        candidate,
        bundled_artifact_ids={channel.artifact_id for channel in candidate},
    )


def test_exact_esr140_to_esr153_artifact_is_schema_valid_bound_and_promotable() -> None:
    artifact = _load(PROOF_PATH)
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(artifact)

    projection = {key: value for key, value in artifact.items() if key != "proof_artifact_digest"}
    assert (
        artifact["proof_artifact_digest"]
        == hashlib.sha256(_EXACT_PROOF_ARTIFACT_DOMAIN + canonical_json(projection)).hexdigest()
    )
    semantic = artifact["semantic_attestation"]
    assert artifact["containment_evidence"] == [
        {
            "evidence_id": "bpm095-esr140.13-to-esr153.0-root-semantic-containment-v1",
            "evidence_digest": hashlib.sha256(canonical_json(semantic)).hexdigest(),
            "source_schema_pointer": "",
            "target_schema_pointer": "",
        }
    ]

    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    source = SchemaArtifactBinding.from_channel(channels["esr-140"])
    target = SchemaArtifactBinding.from_channel(channels["esr-153"])
    assert artifact["source"] == source.as_identity()
    assert artifact["target"] == target.as_identity()
    source_policy_ids = sorted(source.normalized_schema["properties"])
    assert semantic["source_policy_ids"] == source_policy_ids
    assert (
        semantic["source_policy_ids_sha256"]
        == hashlib.sha256(canonical_json(source_policy_ids)).hexdigest()
    )
    for document in semantic["reviewed_upstream_documents"]:
        assert (
            hashlib.sha256((REPO_ROOT / document["path"]).read_bytes()).hexdigest()
            == document["sha256"]
        )

    evidence = load_exact_schema_containment_evidence(
        PROOF_PATH,
        source=source,
        target=target,
    )
    report = prove_retirement_total_convertibility(
        _exact_retirement_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        containment_evidence=evidence,
    )
    assert report.promotable is True
    assert report.results[0].proof_artifact_digest == artifact["proof_artifact_digest"]


def test_exact_proof_loader_rejects_rehashed_stale_identity(tmp_path: Path) -> None:
    artifact = copy.deepcopy(_load(PROOF_PATH))
    artifact["source"]["artifact_id"] = "esr-140.stale"
    projection = {key: value for key, value in artifact.items() if key != "proof_artifact_digest"}
    artifact["proof_artifact_digest"] = hashlib.sha256(
        _EXACT_PROOF_ARTIFACT_DOMAIN + canonical_json(projection)
    ).hexdigest()
    stale_path = tmp_path / "stale-proof.json"
    stale_path.write_text(json.dumps(artifact), encoding="utf-8")
    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}

    with pytest.raises(
        RetirementConvertibilityPreflightError,
        match="retirement_proof_artifact_identity_mismatch",
    ):
        load_exact_schema_containment_evidence(
            stale_path,
            source=SchemaArtifactBinding.from_channel(channels["esr-140"]),
            target=SchemaArtifactBinding.from_channel(channels["esr-153"]),
        )
