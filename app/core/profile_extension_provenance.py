"""Durable, value-free source attribution for Firefox extension policies.

This is deliberately separate from ``baseline_provenance``.  The latter is
the M2/M3 authority for a selected starter and CIS benchmark proof; an
extension value's editing history must neither manufacture nor weaken that
claim.  The record below answers the narrower UI/review question: where did
each currently persisted extension value come from?
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal

from app.core.profile_conversion_json import pointer

CONTRACT_ID = "bpm096-profile-extension-provenance"
CONTRACT_VERSION = 1
ExtensionValueSource = Literal[
    "converted",
    "preset",
    "cis",
    "manual",
    "amo-assisted-manual",
    "imported",
    "raw",
]
SOURCE_VALUES: frozenset[str] = frozenset(
    {
        "converted",
        "preset",
        "cis",
        "manual",
        "amo-assisted-manual",
        "imported",
        "raw",
    }
)
EXTENSION_POLICY_IDS: frozenset[str] = frozenset(
    {"ExtensionSettings", "ExtensionUpdate", "Extensions", "InstallAddonsPermission"}
)


def empty_extension_provenance() -> dict[str, Any]:
    """Return the canonical empty, backwards-compatible attribution record."""

    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "paths": {},
    }


def extension_value_paths(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return every scalar/empty-container extension value keyed by JSON Pointer.

    The policy document itself is never returned or stored in provenance.  A
    pointer exists only while its value exists in the persisted policy JSON.
    Empty objects/lists are values too: without handling them, a selected
    wildcard rule or empty supported collection would lose its origin on
    reopen.
    """

    if not isinstance(document, Mapping):
        return {}
    paths: dict[str, Any] = {}
    for policy_id in sorted(EXTENSION_POLICY_IDS):
        if policy_id not in document:
            continue
        paths.update(_leaf_values(document[policy_id], (policy_id,)))
    return paths


def is_valid_extension_provenance(value: object) -> bool:
    """Validate attribution shape without looking at policy values or catalogs."""

    if not isinstance(value, dict):
        return False
    if value.get("contract_id") != CONTRACT_ID or value.get("contract_version") != CONTRACT_VERSION:
        return False
    paths = value.get("paths")
    if not isinstance(paths, dict):
        return False
    return all(
        isinstance(path, str)
        and path.startswith("/")
        and isinstance(source, str)
        and source in SOURCE_VALUES
        for path, source in paths.items()
    )


def normalized_extension_provenance(
    value: object,
    document: Mapping[str, Any],
    *,
    fallback_source: ExtensionValueSource,
) -> dict[str, Any]:
    """Return canonical sources for exactly the extension values still present.

    Historic rows have a migration default, but this also makes malformed
    source metadata fail safely to the explicit supplied fallback rather than
    inferring starter/CIS provenance from flags.
    """

    stored_paths: Mapping[str, object] = {}
    if is_valid_extension_provenance(value):
        assert isinstance(value, dict)
        candidate_paths = value.get("paths")
        assert isinstance(candidate_paths, dict)
        stored_paths = candidate_paths
    current_paths = extension_value_paths(document)
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "paths": {
            path: stored_paths.get(path)
            if stored_paths.get(path) in SOURCE_VALUES
            else fallback_source
            for path in sorted(current_paths)
        },
    }


def extension_source_for_path(
    provenance: object,
    path: str,
    *,
    fallback_source: ExtensionValueSource = "manual",
) -> ExtensionValueSource:
    """Resolve an exact or nested source for a rule/review path.

    Rule cards represent a subtree while the stored record is value-level.
    Prefer an exact pointer, then a deterministic descendant source.  A mixed
    subtree deliberately resolves to its first value only for legacy compact
    card copy; the UI obtains the full set through ``extension_sources_for``.
    """

    sources = extension_sources_for(provenance, path, fallback_source=fallback_source)
    return sources[0] if sources else fallback_source


def extension_sources_for(
    provenance: object,
    path: str,
    *,
    fallback_source: ExtensionValueSource = "manual",
) -> tuple[ExtensionValueSource, ...]:
    """Return all deterministic source kinds represented by a path subtree."""

    if not is_valid_extension_provenance(provenance):
        return (fallback_source,)
    assert isinstance(provenance, dict)
    paths = provenance["paths"]
    assert isinstance(paths, dict)
    prefix = path.rstrip("/") + "/"
    matching = {
        source
        for candidate, source in paths.items()
        if candidate == path or candidate.startswith(prefix)
    }
    ordered = tuple(source for source in _SOURCE_ORDER if source in matching)
    return ordered or (fallback_source,)


def initialization_extension_provenance(
    document: Mapping[str, Any],
    *,
    preset_decisions: Iterable[Mapping[str, Any]],
    cis_decisions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build prepared-profile attribution from the server composition ledgers."""

    paths = extension_value_paths(document)
    preset_paths = _decision_paths(preset_decisions)
    cis_by_path = _decision_sources(cis_decisions)
    result: dict[str, str] = {}
    for path in paths:
        selected_cis = _nearest_decision(cis_by_path, path)
        if selected_cis == "cis":
            result[path] = "cis"
        elif _nearest_path(preset_paths, path) is not None:
            result[path] = "preset"
        else:
            # A prepared candidate contains only its selected starter/CIS
            # layers.  If a future composer emits an unledgered extension
            # value, make it a visible manual exception rather than inventing
            # a benchmark or preset claim.
            result[path] = "manual"
    return _record(result)


def imported_extension_provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Attribute Firefox-imported extension values without inspecting catalog state."""

    return _record({path: "imported" for path in extension_value_paths(document)})


def manual_extension_provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Attribute generic caller-authored extension values as manual."""

    return _record({path: "manual" for path in extension_value_paths(document)})


def duplicate_extension_provenance(
    source_document: Mapping[str, Any],
    source_provenance: object,
    candidate_document: Mapping[str, Any],
    *,
    cross_schema: bool,
    preset_decisions: Iterable[Mapping[str, Any]] = (),
    cis_decisions: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Carry source facts across a duplicate and overlay reviewed composition.

    Cross-schema candidates may exist only after the existing pairwise
    converter proves every source atom.  Those supported target values are
    therefore visibly ``converted``; unsupported values never reach this
    function because the duplicate remains blocked before persistence.
    """

    source_paths = extension_value_paths(source_document)
    source_record = normalized_extension_provenance(
        source_provenance,
        source_document,
        fallback_source="imported",
    )
    source_sources = source_record["paths"]
    assert isinstance(source_sources, dict)
    candidate_paths = extension_value_paths(candidate_document)
    result: dict[str, str] = {}
    for path, value in candidate_paths.items():
        if cross_schema:
            result[path] = "converted"
        elif path in source_paths and source_paths[path] == value:
            result[path] = str(source_sources.get(path, "imported"))
        else:
            result[path] = "manual"

    for path in candidate_paths:
        preset_decision = _nearest_decision_code(preset_decisions, path)
        if preset_decision == "filled-absent":
            result[path] = "preset"
        if _nearest_decision(_decision_sources(cis_decisions), path) == "cis":
            result[path] = "cis"
    return _record(result)


def converted_extension_provenance(
    candidate_document: Mapping[str, Any],
) -> dict[str, Any]:
    """Mark an explicitly applied cross-schema conversion's surviving values."""

    return _record({path: "converted" for path in extension_value_paths(candidate_document)})


def reconcile_extension_provenance(
    previous_document: Mapping[str, Any],
    previous_provenance: object,
    next_document: Mapping[str, Any],
    submitted_provenance: object,
) -> dict[str, Any]:
    """Preserve untouched values and record only real editor changes as manual.

    The accepted client refinements are ``amo-assisted-manual`` and ``raw``
    for a newly changed value.  They convey local user interaction only, not
    an AMO safety or policy claim; clients cannot relabel an
    untouched/preset/CIS/imported value.  All other changed values are
    server-derived ``manual`` facts.
    """

    before_paths = extension_value_paths(previous_document)
    after_paths = extension_value_paths(next_document)
    current = normalized_extension_provenance(
        previous_provenance,
        previous_document,
        fallback_source="imported",
    )["paths"]
    submitted = normalized_extension_provenance(
        submitted_provenance,
        next_document,
        fallback_source="manual",
    )["paths"]
    assert isinstance(current, dict)
    assert isinstance(submitted, dict)

    result: dict[str, str] = {}
    for path, value in after_paths.items():
        if path in before_paths and before_paths[path] == value:
            result[path] = str(current.get(path, "imported"))
            continue
        claimed = submitted.get(path)
        result[path] = claimed if claimed in {"amo-assisted-manual", "raw"} else "manual"
    return _record(result)


_SOURCE_ORDER: tuple[ExtensionValueSource, ...] = (
    "converted",
    "preset",
    "cis",
    "manual",
    "amo-assisted-manual",
    "imported",
    "raw",
)


def _record(paths: Mapping[str, str]) -> dict[str, Any]:
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "paths": {path: paths[path] for path in sorted(paths)},
    }


def _leaf_values(value: Any, path: tuple[str | int, ...]) -> dict[str, Any]:
    if isinstance(value, dict):
        if not value:
            return {pointer(path): {}}
        result: dict[str, Any] = {}
        for key in sorted(value):
            result.update(_leaf_values(value[key], (*path, str(key))))
        return result
    if isinstance(value, list):
        if not value:
            return {pointer(path): []}
        result = {}
        for index, item in enumerate(value):
            result.update(_leaf_values(item, (*path, index)))
        return result
    return {pointer(path): value}


def _decision_paths(decisions: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(decision.get("path"))
                for decision in decisions
                if isinstance(decision, Mapping)
                and isinstance(decision.get("path"), str)
                and _is_extension_path(str(decision["path"]))
            }
        )
    )


def _decision_sources(decisions: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue
        path = decision.get("path")
        if not isinstance(path, str) or not _is_extension_path(path):
            continue
        selected = decision.get("selected_source")
        if isinstance(selected, str):
            result[path] = "cis" if selected in {"cis", "cis-catalog"} else selected
    return result


def _nearest_decision(paths: Mapping[str, str], value_path: str) -> str | None:
    nearest = _nearest_path(paths, value_path)
    return paths.get(nearest) if nearest is not None else None


def _nearest_decision_code(decisions: Iterable[Mapping[str, Any]], value_path: str) -> str | None:
    candidates: dict[str, str] = {}
    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue
        path = decision.get("path")
        code = decision.get("decision")
        if isinstance(path, str) and isinstance(code, str) and _is_extension_path(path):
            candidates[path] = code
    nearest = _nearest_path(candidates, value_path)
    return candidates.get(nearest) if nearest is not None else None


def _nearest_path(paths: Mapping[str, Any] | Iterable[str], value_path: str) -> str | None:
    candidates = paths.keys() if isinstance(paths, Mapping) else paths
    matches = [
        candidate
        for candidate in candidates
        if isinstance(candidate, str)
        and (value_path == candidate or value_path.startswith(candidate.rstrip("/") + "/"))
    ]
    return max(matches, key=len) if matches else None


def _is_extension_path(path: str) -> bool:
    return any(
        path == f"/{policy}" or path.startswith(f"/{policy}/") for policy in EXTENSION_POLICY_IDS
    )
