"""Read-only latest-ESR recommendation eligibility for persisted profiles.

This module intentionally knows no profile policy data and performs no schema
loading.  It resolves only reviewed runtime lifecycle roles, so list/detail
reads remain safe for legacy rows whose stored artifact no longer exists.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.core import schema_channels
from app.core.schema_channels import SchemaChannel

RECOMMENDATION_ID = "schema-conversion.older-esr-recommendation"
RECOMMENDATION_REASON_CODE = "supported_older_esr_to_latest_esr"
RECOMMENDATION_ACTION = "conversion-preview"


def profile_conversion_recommendation(
    *,
    schema_version: str,
    revision: int,
    is_active: bool,
    channels: Iterable[SchemaChannel] | None = None,
    bundled_artifact_ids: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return a value-free latest-ESR conversion recommendation, or ``None``.

    Every identity comes from catalog roles.  Invalid, ambiguous, inactive,
    unbundled, unknown, non-ESR, latest, and non-older source rows deliberately
    resolve to no recommendation rather than making a legacy profile unreadable.
    Optional inputs make catalog role mutation tests independent of declaration
    order while production defaults always use the runtime catalog.
    """

    if not is_active or revision < 1:
        return None
    catalog = tuple(schema_channels.SCHEMA_CHANNEL_CATALOG if channels is None else channels)
    bundled = (
        schema_channels.SCHEMA_FILENAMES if bundled_artifact_ids is None else bundled_artifact_ids
    )
    if not _has_unambiguous_catalog_identities(catalog):
        return None

    latest_rows = [
        channel
        for channel in catalog
        if channel.is_latest_esr and _is_supported_selectable_bundled_esr(channel, bundled)
    ]
    if len(latest_rows) != 1:
        return None
    latest = latest_rows[0]

    source_rows = [channel for channel in catalog if channel.artifact_id == schema_version]
    if len(source_rows) != 1:
        return None
    source = source_rows[0]
    if not _is_supported_selectable_bundled_esr(source, bundled):
        return None
    if source.line_number >= latest.line_number:
        return None
    # The source role must explicitly name the current latest ESR line.  This
    # prevents a numeric comparison from becoming an implicit migration rule.
    if source.recommendation_target_line_id != latest.line_id:
        return None

    return {
        "recommendation_id": RECOMMENDATION_ID,
        "reason_code": RECOMMENDATION_REASON_CODE,
        "profile_revision": revision,
        "source": {
            "line_id": source.line_id,
            "artifact_id": source.artifact_id,
        },
        "target": {
            "line_id": latest.line_id,
            "artifact_id": latest.artifact_id,
            "label": latest.label,
            "i18n_key": latest.i18n_key,
        },
        "action": {
            "action_id": RECOMMENDATION_ACTION,
            "preview_target_artifact_id": latest.artifact_id,
        },
    }


def _is_supported_selectable_bundled_esr(
    channel: SchemaChannel,
    bundled_artifact_ids: Mapping[str, str],
) -> bool:
    return (
        channel.family == "esr"
        and channel.support_state == "supported"
        and channel.selectable
        and channel.artifact_id in bundled_artifact_ids
    )


def _has_unambiguous_catalog_identities(channels: tuple[SchemaChannel, ...]) -> bool:
    """Reject duplicate/malformed identities before resolving role references."""

    artifact_ids = [channel.artifact_id for channel in channels]
    line_ids = [channel.line_id for channel in channels]
    return (
        bool(channels)
        and all(isinstance(value, str) and value for value in artifact_ids + line_ids)
        and len(artifact_ids) == len(set(artifact_ids))
        and len(line_ids) == len(set(line_ids))
    )
