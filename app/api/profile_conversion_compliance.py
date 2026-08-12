"""CIS-specific conversion evidence adapter at the delivery boundary."""

from __future__ import annotations

import copy
import hashlib
from typing import Any

from app.compliance.firefox.cis.generation import CisLayerUnavailableError, build_cis_layer
from app.compliance.firefox.cis.merge import CisMergeDecision, merge_base_with_cis_layer
from app.compliance.firefox.cis.validation import find_benchmark
from app.core.profile_conversion_json import canonical_json, strict_json_copy
from app.core.profile_conversion_planner import ConversionComplianceReplan
from app.core.schema_channels import SchemaChannel

_CIS_COMPLIANCE_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "framework",
        "benchmark_id",
        "benchmark_version",
        "layer",
        "artifact_id",
        "cis_artifact_digest",
        "base_policies",
        "summary",
        "decisions",
        "current_claims",
    }
)
_CIS_LAYER_LEVELS = {"cis_l1": 1, "cis_l2": 2}


def recompute_pinned_cis_compliance(
    source_compliance: Any,
    source_channel: SchemaChannel,
    target_channel: SchemaChannel,
    source_policies: dict[str, Any],
    target_policies: dict[str, Any],
) -> ConversionComplianceReplan | None:
    """Return target proof only when the whole persisted CIS claim reproduces.

    Existing wizard metadata has no base document or generated-layer digest, so
    it intentionally returns ``None`` and the planner preserves it in the
    truthful invalidated wrapper. A current claim needs the strict v1 shape,
    source and target CIS layer proof, source/target effective policy equality,
    and complete decision/note accounting.
    """
    if (
        not isinstance(source_compliance, dict)
        or set(source_compliance) != _CIS_COMPLIANCE_ENVELOPE_FIELDS
    ):
        return None
    if (
        source_compliance.get("schema_version") != 1
        or source_compliance.get("status") != "current"
        or source_compliance.get("framework") != "cis"
        or source_compliance.get("artifact_id") != source_channel.artifact_id
        or source_compliance.get("current_claims") is not True
    ):
        return None

    benchmark_id = source_compliance.get("benchmark_id")
    benchmark_version = source_compliance.get("benchmark_version")
    layer_key = source_compliance.get("layer")
    base_policies = source_compliance.get("base_policies")
    source_summary = source_compliance.get("summary")
    source_decisions = source_compliance.get("decisions")
    source_layer_digest = source_compliance.get("cis_artifact_digest")
    if (
        not isinstance(benchmark_id, str)
        or not isinstance(benchmark_version, str)
        or layer_key not in _CIS_LAYER_LEVELS
        or not isinstance(base_policies, dict)
        or not isinstance(source_summary, dict)
        or not isinstance(source_decisions, list)
        or not isinstance(source_layer_digest, str)
    ):
        return None

    benchmark = find_benchmark(benchmark_id, upstream_version=benchmark_version)
    if (
        benchmark is None
        or str(benchmark.get("id")) != benchmark_id
        or str(benchmark.get("upstream_version")) != benchmark_version
    ):
        return None

    try:
        level = _CIS_LAYER_LEVELS[layer_key]
        source_layer = build_cis_layer(
            level,
            source_channel.artifact_id,
            benchmark_id=benchmark_id,
            upstream_version=benchmark_version,
        )
        target_layer = build_cis_layer(
            level,
            target_channel.artifact_id,
            benchmark_id=benchmark_id,
            upstream_version=benchmark_version,
        )
        if _cis_layer_digest(source_layer.to_document()) != source_layer_digest:
            return None
        source_merge = merge_base_with_cis_layer(base_policies, source_layer)
        target_merge = merge_base_with_cis_layer(base_policies, target_layer)
    except AttributeError, CisLayerUnavailableError, KeyError, OSError, TypeError, ValueError:
        return None

    if (
        source_merge.effective_policies != source_policies
        or target_merge.effective_policies != target_policies
    ):
        return None
    notes = _validated_source_notes(source_decisions, source_merge.decisions)
    if notes is None or source_summary != source_merge.summary:
        return None

    target_decisions = _target_decision_projection(target_merge.decisions, notes=notes)
    if target_decisions is None:
        return None
    target_layer_digest = _cis_layer_digest(target_layer.to_document())
    candidate = {
        "schema_version": 1,
        "status": "current",
        "framework": "cis",
        "benchmark_id": benchmark_id,
        "benchmark_version": benchmark_version,
        "layer": layer_key,
        "artifact_id": target_channel.artifact_id,
        "cis_artifact_digest": target_layer_digest,
        "base_policies": copy.deepcopy(base_policies),
        "summary": copy.deepcopy(target_merge.summary),
        "decisions": target_decisions,
        "current_claims": True,
    }
    strict_candidate = strict_json_copy(candidate)
    assert isinstance(strict_candidate, dict)
    return ConversionComplianceReplan(strict_candidate, target_layer_digest)


def _cis_layer_digest(document: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(strict_json_copy(document))).hexdigest()


def _decision_core(decision: CisMergeDecision) -> dict[str, Any]:
    return {
        "path": list(decision.path),
        "decision": decision.decision,
        "selected_source": decision.selected_source,
        "recommendation_ids": list(decision.recommendation_ids),
        "review_required": decision.review_required,
        "reason": decision.reason,
    }


def _validated_source_notes(
    stored_decisions: list[Any],
    expected_decisions: tuple[CisMergeDecision, ...],
) -> dict[tuple[str, ...], str] | None:
    if len(stored_decisions) != len(expected_decisions):
        return None
    notes: dict[tuple[str, ...], str] = {}
    for stored, expected in zip(stored_decisions, expected_decisions, strict=True):
        if not isinstance(stored, dict):
            return None
        core = _decision_core(expected)
        if set(stored) - {*core, "exception_note"}:
            return None
        if {key: stored.get(key) for key in core} != core:
            return None
        note = stored.get("exception_note")
        if note is not None:
            if not isinstance(note, str) or not note:
                return None
            path = tuple(expected.path)
            if path in notes:
                return None
            notes[path] = note
    return notes


def _target_decision_projection(
    decisions: tuple[CisMergeDecision, ...],
    *,
    notes: dict[tuple[str, ...], str],
) -> list[dict[str, Any]] | None:
    target_paths = {tuple(decision.path) for decision in decisions}
    if not set(notes) <= target_paths:
        return None
    projected: list[dict[str, Any]] = []
    for decision in decisions:
        value = _decision_core(decision)
        note = notes.get(tuple(decision.path))
        if note is not None:
            value["exception_note"] = note
        projected.append(value)
    return projected
