"""Durable, value-free source attribution for certificate and trust values.

``baseline_provenance`` remains the only authority for a selected starter and
CIS benchmark proof.  This narrower ledger answers a different UI and review
question: where did a currently persisted certificate/trust value originate?
It never reads a certificate, module, or filesystem path and never promotes a
value into a CIS claim.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal

from app.core.profile_conversion_json import pointer

CONTRACT_ID = "bpm096-profile-certificate-provenance"
CONTRACT_VERSION = 1
CertificateValueSource = Literal[
    "baseline",
    "cis",
    "manual",
    "converted",
    "imported",
    "raw",
]
SOURCE_VALUES: frozenset[str] = frozenset(
    {"baseline", "cis", "manual", "converted", "imported", "raw"}
)
CERTIFICATE_POLICY_IDS: frozenset[str] = frozenset(
    {
        "Authentication",
        "Certificates",
        "DisableSecurityBypass",
        "MicrosoftEntraSSO",
        "SecurityDevices",
        "WindowsSSO",
    }
)
ENTERPRISE_ROOTS_PREFERENCE = "security.enterprise_roots.enabled"
_PREFERENCE_PATH = pointer(("Preferences", ENTERPRISE_ROOTS_PREFERENCE))


def empty_certificate_provenance() -> dict[str, Any]:
    """Return the canonical empty, backwards-compatible attribution record."""

    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "paths": {},
    }


def certificate_value_paths(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return certificate/trust leaves keyed by RFC 6901 pointers only.

    Values stay in the profile policy document.  This durable record contains
    only pointers and a source label, so it cannot disclose a certificate
    reference or alter export semantics.
    """

    if not isinstance(document, Mapping):
        return {}
    paths: dict[str, Any] = {}
    for policy_id in sorted(CERTIFICATE_POLICY_IDS):
        if policy_id in document:
            paths.update(_leaf_values(document[policy_id], (policy_id,)))
    preferences = document.get("Preferences")
    if isinstance(preferences, Mapping) and ENTERPRISE_ROOTS_PREFERENCE in preferences:
        paths.update(
            _leaf_values(
                preferences[ENTERPRISE_ROOTS_PREFERENCE],
                ("Preferences", ENTERPRISE_ROOTS_PREFERENCE),
            )
        )
    return paths


def is_valid_certificate_provenance(value: object) -> bool:
    """Validate attribution shape without reading values or catalogs."""

    if not isinstance(value, dict):
        return False
    if value.get("contract_id") != CONTRACT_ID or value.get("contract_version") != CONTRACT_VERSION:
        return False
    paths = value.get("paths")
    if not isinstance(paths, dict):
        return False
    return all(
        isinstance(path, str)
        and _is_certificate_path(path)
        and isinstance(source, str)
        and source in SOURCE_VALUES
        for path, source in paths.items()
    )


def normalized_certificate_provenance(
    value: object,
    document: Mapping[str, Any],
    *,
    fallback_source: CertificateValueSource,
) -> dict[str, Any]:
    """Retain sources for exactly the certificate values still persisted."""

    stored_paths: Mapping[str, object] = {}
    if is_valid_certificate_provenance(value):
        assert isinstance(value, dict)
        candidate_paths = value.get("paths")
        assert isinstance(candidate_paths, dict)
        stored_paths = candidate_paths
    current_paths = certificate_value_paths(document)
    paths: dict[str, str] = {}
    for path in sorted(current_paths):
        source = stored_paths.get(path)
        paths[path] = (
            source if isinstance(source, str) and source in SOURCE_VALUES else fallback_source
        )
    return _record(paths)


def certificate_sources_for(
    provenance: object,
    path: str,
    *,
    fallback_source: CertificateValueSource = "manual",
) -> tuple[CertificateValueSource, ...]:
    """Return all deterministic sources represented by one policy subtree."""

    if not is_valid_certificate_provenance(provenance):
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


def initialization_certificate_provenance(
    document: Mapping[str, Any],
    *,
    preset_decisions: Iterable[Mapping[str, Any]],
    cis_decisions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build prepared attribution from the existing server composition ledgers."""

    preset_paths = _decision_paths(preset_decisions)
    cis_sources = _decision_sources(cis_decisions)
    result: dict[str, str] = {}
    for path in certificate_value_paths(document):
        if _nearest_decision(cis_sources, path) == "cis":
            result[path] = "cis"
        elif _nearest_path(preset_paths, path) is not None:
            result[path] = "baseline"
        else:
            # Any composer output not evidenced by a starter or CIS decision
            # stays a visible manual exception; never infer benchmark proof.
            result[path] = "manual"
    return _record(result)


def imported_certificate_provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Attribute historical Firefox-imported values without catalog inference."""

    return _record({path: "imported" for path in certificate_value_paths(document)})


def manual_certificate_provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Attribute generic caller-authored values as manual."""

    return _record({path: "manual" for path in certificate_value_paths(document)})


def duplicate_certificate_provenance(
    source_document: Mapping[str, Any],
    source_provenance: object,
    candidate_document: Mapping[str, Any],
    *,
    cross_schema: bool,
    preset_decisions: Iterable[Mapping[str, Any]] = (),
    cis_decisions: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Carry provenance across duplicate composition without changing baseline proof.

    A cross-schema duplicate reaches this function only after the pairwise
    planner accepts every target value.  Unsupported certificate values remain
    conversion blockers before persistence and therefore receive no invented
    target attribution.
    """

    source_paths = certificate_value_paths(source_document)
    source_sources = normalized_certificate_provenance(
        source_provenance,
        source_document,
        fallback_source="imported",
    )["paths"]
    assert isinstance(source_sources, dict)
    candidate_paths = certificate_value_paths(candidate_document)
    result: dict[str, str] = {}
    for path, value in candidate_paths.items():
        if cross_schema:
            result[path] = "converted"
        elif path in source_paths and source_paths[path] == value:
            result[path] = str(source_sources.get(path, "imported"))
        else:
            result[path] = "manual"

    cis_sources = _decision_sources(cis_decisions)
    for path in candidate_paths:
        if _nearest_decision_code(preset_decisions, path) == "filled-absent":
            result[path] = "baseline"
        if _nearest_decision(cis_sources, path) == "cis":
            result[path] = "cis"
    return _record(result)


def converted_certificate_provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    """Mark surviving values after a successfully applied conversion."""

    return _record({path: "converted" for path in certificate_value_paths(document)})


def reconcile_certificate_provenance(
    previous_document: Mapping[str, Any],
    previous_provenance: object,
    next_document: Mapping[str, Any],
    submitted_provenance: object,
) -> dict[str, Any]:
    """Preserve untouched sources and mark real editor changes manually.

    A client may retain ``raw`` only for a value it changed in the same write.
    It cannot relabel an untouched baseline, CIS, imported, or converted value.
    This is attribution metadata only; it neither repairs nor downgrades the
    server-owned benchmark envelope.
    """

    before_paths = certificate_value_paths(previous_document)
    after_paths = certificate_value_paths(next_document)
    current = normalized_certificate_provenance(
        previous_provenance,
        previous_document,
        fallback_source="imported",
    )["paths"]
    submitted = normalized_certificate_provenance(
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
        else:
            result[path] = "raw" if submitted.get(path) == "raw" else "manual"
    return _record(result)


_SOURCE_ORDER: tuple[CertificateValueSource, ...] = (
    "converted",
    "baseline",
    "cis",
    "manual",
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
                str(decision["path"])
                for decision in decisions
                if isinstance(decision, Mapping)
                and isinstance(decision.get("path"), str)
                and _is_certificate_path(str(decision["path"]))
            }
        )
    )


def _decision_sources(decisions: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue
        path = decision.get("path")
        if not isinstance(path, str) or not _is_certificate_path(path):
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
        if isinstance(path, str) and isinstance(code, str) and _is_certificate_path(path):
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


def _is_certificate_path(path: str) -> bool:
    return path == _PREFERENCE_PATH or any(
        path == f"/{policy}" or path.startswith(f"/{policy}/") for policy in CERTIFICATE_POLICY_IDS
    )
