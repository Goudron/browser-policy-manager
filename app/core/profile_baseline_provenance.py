"""Durable, non-inferential profile starter and CIS provenance helpers.

The profile document and its raw ``compliance`` payload are not proof of how a
profile was created.  This module owns the small persisted envelope introduced
by BPM096-M3-01 and the value-free projection consumed by ``ProfileRead``.
It deliberately knows nothing about the starter or CIS catalogs: resolving a
catalog identity and creating a verified catalog baseline belongs to later
server-owned preparation work.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Final, Literal

type BaselineLineageKind = Literal[
    "prepared",
    "generic-create",
    "firefox-import",
    "legacy-migration",
    "duplicate",
    "conversion",
]

CONTRACT_ID: Final = "bpm096-profile-baseline-provenance"
CONTRACT_VERSION: Final = 1
_LINEAGE_KINDS: Final = {
    "prepared",
    "generic-create",
    "firefox-import",
    "legacy-migration",
    "duplicate",
    "conversion",
}
_STARTER_CATALOG_FIELDS: Final = (
    "catalog_id",
    "catalog_version",
    "definition_sha256",
    "resolved_schema_artifact_id",
)
_STARTER_PRESET_ID_FIELD: Final = "preset_id"
_CIS_CATALOG_FIELDS: Final = (
    "catalog_id",
    "catalog_version",
    "baseline_id",
    "benchmark_id",
    "benchmark_version",
    "layer_sha256",
    "merge_rules_sha256",
    "merge_result_sha256",
    "resolved_schema_artifact_id",
)
_DIGEST_FIELDS: Final = {
    "definition_sha256",
    "layer_sha256",
    "merge_rules_sha256",
    "merge_result_sha256",
    "proof_digest",
    "plan_digest",
}


def custom_imported_baseline_provenance(
    lineage_kind: BaselineLineageKind,
) -> dict[str, Any]:
    """Return a fresh truthful envelope for a non-catalog profile origin."""

    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "lineage": {
            "kind": lineage_kind,
            "source_profile_id": None,
            "source_revision": None,
            "plan_digest": None,
        },
        "starter": {
            "identity_state": "custom-imported",
            "catalog_id": None,
            "catalog_version": None,
            "preset_id": None,
            "definition_sha256": None,
            "resolved_schema_artifact_id": None,
            "disposition": "custom-imported",
        },
        "cis": {
            "identity_state": "custom-imported",
            "catalog_id": None,
            "catalog_version": None,
            "baseline_id": None,
            "benchmark_id": None,
            "benchmark_version": None,
            "layer_sha256": None,
            "merge_rules_sha256": None,
            "merge_result_sha256": None,
            "resolved_schema_artifact_id": None,
            "proof_digest": None,
            "display_status": "manual-review",
            "current_claim": False,
            "reason_code": "cis_provenance_unknown",
        },
    }


def generic_create_baseline_provenance() -> dict[str, Any]:
    """Return the only provenance default permitted for generic CRUD create."""

    return custom_imported_baseline_provenance("generic-create")


def firefox_import_baseline_provenance() -> dict[str, Any]:
    """Return the only provenance default permitted for Firefox document import."""

    return custom_imported_baseline_provenance("firefox-import")


def legacy_migration_baseline_provenance() -> dict[str, Any]:
    """Return the all-row migration default without inspecting stored policy data."""

    return custom_imported_baseline_provenance("legacy-migration")


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _all_null(value: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return all(value.get(field) is None for field in fields)


def _catalog_identity_is_valid(value: dict[str, Any], fields: tuple[str, ...]) -> bool:
    for field in fields:
        candidate = value.get(field)
        if field in _DIGEST_FIELDS:
            if not _is_digest(candidate):
                return False
        elif not _is_nonempty_string(candidate):
            return False
    return True


def is_valid_baseline_provenance(value: object) -> bool:
    """Validate the M2-04 logical envelope without consulting profile payloads.

    This intentionally accepts future catalog-derived identities once their
    shape is complete.  It never compares stored flags or compliance to a
    catalog and therefore cannot promote an old or imported profile.
    """

    if not isinstance(value, dict):
        return False
    if value.get("contract_id") != CONTRACT_ID or value.get("contract_version") != CONTRACT_VERSION:
        return False

    lineage = value.get("lineage")
    starter = value.get("starter")
    cis = value.get("cis")
    if not all(isinstance(part, dict) for part in (lineage, starter, cis)):
        return False
    assert isinstance(lineage, dict)
    assert isinstance(starter, dict)
    assert isinstance(cis, dict)

    if lineage.get("kind") not in _LINEAGE_KINDS:
        return False
    source_id = lineage.get("source_profile_id")
    source_revision = lineage.get("source_revision")
    if source_id is not None and (
        not isinstance(source_id, int) or isinstance(source_id, bool) or source_id < 1
    ):
        return False
    if source_revision is not None and (
        not isinstance(source_revision, int)
        or isinstance(source_revision, bool)
        or source_revision < 1
    ):
        return False
    if source_id is None and source_revision is not None:
        return False
    plan_digest = lineage.get("plan_digest")
    if plan_digest is not None and not _is_digest(plan_digest):
        return False

    starter_state = starter.get("identity_state")
    if starter_state == "custom-imported":
        if (
            _all_null(starter, _STARTER_CATALOG_FIELDS)
            and starter.get(_STARTER_PRESET_ID_FIELD) is None
            and starter.get("disposition") == "custom-imported"
        ):
            pass
        else:
            return False
    elif starter_state == "catalog":
        if not _catalog_identity_is_valid(starter, _STARTER_CATALOG_FIELDS):
            return False
        # M3-02 records created before this additive identity extension do
        # not have ``preset_id``.  They remain historical catalog records but
        # never acquire a guessed ID from flags or the current catalog.
        if _STARTER_PRESET_ID_FIELD in starter and not _is_nonempty_string(
            starter.get(_STARTER_PRESET_ID_FIELD)
        ):
            return False
        if starter.get("disposition") not in {"created", "preserved", "recomposed"}:
            return False
    else:
        return False

    cis_state = cis.get("identity_state")
    display_status = cis.get("display_status")
    current_claim = cis.get("current_claim")
    if not isinstance(current_claim, bool) or (current_claim is True) != (
        display_status == "verified"
    ):
        return False
    if display_status not in {"none", "verified", "manual-review", "invalidated", "unavailable"}:
        return False

    proof_digest = cis.get("proof_digest")
    if cis_state == "none":
        return (
            display_status == "none"
            and current_claim is False
            and _all_null(cis, _CIS_CATALOG_FIELDS)
            and proof_digest is None
        )
    if cis_state == "custom-imported":
        return (
            display_status == "manual-review"
            and current_claim is False
            and _all_null(cis, _CIS_CATALOG_FIELDS)
            and proof_digest is None
            and _is_nonempty_string(cis.get("reason_code"))
        )
    if cis_state != "catalog" or not _catalog_identity_is_valid(cis, _CIS_CATALOG_FIELDS):
        return False
    if not _is_digest(proof_digest):
        return False
    if display_status in {"manual-review", "invalidated", "unavailable"}:
        return _is_nonempty_string(cis.get("reason_code"))
    return display_status == "verified" and cis.get("reason_code") is None


def baseline_display(value: object) -> dict[str, Any]:
    """Project persisted provenance without a flag/compliance or catalog fallback."""

    if not is_valid_baseline_provenance(value):
        return {
            "starter": {
                "identity_state": "unavailable",
                "availability": "unavailable",
            },
            "cis": {
                "identity_state": "unavailable",
                "display_status": "manual-review",
                "current_claim": False,
                "reason_code": "baseline_provenance_unavailable",
            },
        }

    assert isinstance(value, dict)
    starter = value["starter"]
    cis = value["cis"]
    assert isinstance(starter, dict)
    assert isinstance(cis, dict)

    starter_display: dict[str, Any] = {"identity_state": starter["identity_state"]}
    if starter["identity_state"] == "catalog":
        # M3-01 stores catalog identity but does not own catalog resolution.
        # An unresolved exact identity must not be substituted or called current.
        starter_display.update(
            {
                "catalog_id": starter["catalog_id"],
                "catalog_version": starter["catalog_version"],
                "availability": "unavailable",
                "disposition": starter["disposition"],
            }
        )
        preset_id = starter.get(_STARTER_PRESET_ID_FIELD)
        if _is_nonempty_string(preset_id):
            starter_display["preset_id"] = preset_id
        else:
            starter_display["reason_code"] = "starter_preset_identity_unavailable"
    else:
        starter_display["availability"] = "not-applicable"

    cis_display: dict[str, Any] = {
        "identity_state": cis["identity_state"],
        "display_status": cis["display_status"],
        "current_claim": cis["current_claim"],
    }
    if cis["identity_state"] == "catalog":
        cis_display.update(
            {
                "baseline_id": cis["baseline_id"],
                "benchmark_id": cis["benchmark_id"],
                "benchmark_version": cis["benchmark_version"],
            }
        )
    if cis.get("reason_code") is not None:
        cis_display["reason_code"] = cis["reason_code"]
    return {"starter": starter_display, "cis": cis_display}


def downgrade_verified_cis_to_manual_review(
    value: object,
    *,
    reason_code: str = "profile_payload_modified",
) -> dict[str, Any] | None:
    """Return a copied non-current envelope when generic content changes.

    Malformed records stay untouched and serialize through the fail-closed
    projection; attempting to repair them from flags or raw compliance would
    violate the stored-provenance boundary.
    """

    if not is_valid_baseline_provenance(value):
        return None
    assert isinstance(value, dict)
    cis = value.get("cis")
    assert isinstance(cis, dict)
    if cis.get("display_status") != "verified":
        return None
    downgraded = deepcopy(value)
    downgraded_cis = downgraded["cis"]
    assert isinstance(downgraded_cis, dict)
    downgraded_cis["display_status"] = "manual-review"
    downgraded_cis["current_claim"] = False
    downgraded_cis["reason_code"] = reason_code
    return downgraded
