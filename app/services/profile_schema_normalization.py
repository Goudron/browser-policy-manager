from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy_validation import (
    PolicyValidationError,
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)
from app.models.profile import Profile

logger = logging.getLogger(__name__)

LEGACY_ESR_140_9 = f"esr-140.{9}"
LEGACY_RELEASE_149 = f"release-{149}"

LEGACY_SCHEMA_VERSION_MAP: dict[str, str] = {
    LEGACY_ESR_140_9: "esr-140.10",
    LEGACY_RELEASE_149: "release-150",
}


@dataclass(slots=True)
class ProfileSchemaNormalizationResult:
    scanned: int = 0
    normalized: int = 0
    skipped_invalid: int = 0


async def normalize_legacy_profile_schema_versions(
    session: AsyncSession,
) -> ProfileSchemaNormalizationResult:
    """
    Normalize selected legacy schema channel strings to the current supported ones.

    We only update a profile when its existing flags are valid against the
    target schema. Invalid profiles are left untouched for later manual review.
    """

    stmt = select(Profile).where(Profile.schema_version.in_(tuple(LEGACY_SCHEMA_VERSION_MAP.keys())))
    result = await session.scalars(stmt)
    profiles = list(result)
    summary = ProfileSchemaNormalizationResult(scanned=len(profiles))

    if not profiles:
        return summary

    schema_cache: dict[str, dict] = {}

    for profile in profiles:
        source_schema = profile.schema_version
        target_schema = LEGACY_SCHEMA_VERSION_MAP[source_schema]

        target_policy_schema = schema_cache.get(target_schema)
        if target_policy_schema is None:
            target_policy_schema = load_policy_schema_for_channel(target_schema)
            schema_cache[target_schema] = target_policy_schema

        try:
            validate_profile_policies_or_raise(profile.flags or {}, target_policy_schema)
        except PolicyValidationError:
            summary.skipped_invalid += 1
            logger.warning(
                "Skipping legacy schema normalization for profile id=%s name=%r from %s to %s because flags are invalid for the target schema.",
                profile.id,
                profile.name,
                source_schema,
                target_schema,
            )
            continue

        profile.schema_version = target_schema
        profile.revision += 1
        summary.normalized += 1

    await session.flush()
    return summary
