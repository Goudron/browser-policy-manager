"""Fail-closed, read-only planning for Firefox schema lifecycle transitions.

This module compares two explicit catalog snapshots.  It is deliberately not a
runtime channel resolver and never inspects or changes stored profiles.  M6-02
uses its immutable, value-free result as the first input to a retirement proof;
the Alembic-only writer remains outside this module.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass

from app.core import schema_channels
from app.core.schema_channels import SchemaChannel

_ARTIFACT_VERSION = re.compile(r"\d+(?:\.\d+)+\Z")
_VALID_FAMILIES = frozenset({"esr", "release"})
_VALID_SUPPORT_STATES = frozenset({"supported", "retired"})


class LifecycleTransitionPlanError(ValueError):
    """A catalog transition cannot safely become a release migration plan."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True, slots=True)
class LifecycleLineIdentity:
    """Value-free stable-line and exact-artifact identity used by a plan."""

    line_id: str
    artifact_id: str
    channel_id: str
    family: str
    line_number: int
    artifact_version: str
    support_state: str
    selectable: bool

    @classmethod
    def from_channel(cls, channel: SchemaChannel) -> LifecycleLineIdentity:
        return cls(
            line_id=channel.line_id,
            artifact_id=channel.artifact_id,
            channel_id=channel.channel_id,
            family=channel.family,
            line_number=channel.line_number,
            artifact_version=channel.artifact_version,
            support_state=channel.support_state,
            selectable=channel.selectable,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "line_id": self.line_id,
            "artifact_id": self.artifact_id,
            "channel_id": self.channel_id,
            "family": self.family,
            "line_number": self.line_number,
            "artifact_version": self.artifact_version,
            "support_state": self.support_state,
            "selectable": self.selectable,
        }


@dataclass(frozen=True, slots=True)
class SameLinePatchRefresh:
    """An exact-artifact replacement that retains one stable lifecycle line."""

    previous: LifecycleLineIdentity
    candidate: LifecycleLineIdentity

    @property
    def line_id(self) -> str:
        return self.candidate.line_id

    def as_dict(self) -> dict[str, object]:
        return {
            "line_id": self.line_id,
            "previous": self.previous.as_dict(),
            "candidate": self.candidate.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class RetiredLine:
    """A supported ESR line which the candidate catalog marks retired."""

    previous: LifecycleLineIdentity
    candidate: LifecycleLineIdentity

    @property
    def line_id(self) -> str:
        return self.candidate.line_id

    def as_dict(self) -> dict[str, object]:
        return {
            "line_id": self.line_id,
            "previous": self.previous.as_dict(),
            "candidate": self.candidate.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class RetirementSuccessorMapping:
    """One frozen source/target exact-artifact mapping for a retirement."""

    source: LifecycleLineIdentity
    target: LifecycleLineIdentity
    declared_successor_line_id: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source.as_dict(),
            "target": self.target.as_dict(),
            "declared_successor_line_id": self.declared_successor_line_id,
        }


@dataclass(frozen=True, slots=True)
class LifecycleTransitionPlan:
    """Deterministic, non-mutating diff of reviewed lifecycle catalogs."""

    added_lines: tuple[LifecycleLineIdentity, ...]
    retained_lines: tuple[LifecycleLineIdentity, ...]
    refreshed_lines: tuple[LifecycleLineIdentity, ...]
    retired_lines: tuple[RetiredLine, ...]
    same_line_patch_refreshes: tuple[SameLinePatchRefresh, ...]
    retirement_successor_mappings: tuple[RetirementSuccessorMapping, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a stable value-free projection suitable for review evidence."""
        return {
            "added_lines": [line.as_dict() for line in self.added_lines],
            "retained_lines": [line.as_dict() for line in self.retained_lines],
            "refreshed_lines": [line.as_dict() for line in self.refreshed_lines],
            "retired_lines": [line.as_dict() for line in self.retired_lines],
            "same_line_patch_refreshes": [
                refresh.as_dict() for refresh in self.same_line_patch_refreshes
            ],
            "retirement_successor_mappings": [
                mapping.as_dict() for mapping in self.retirement_successor_mappings
            ],
        }


def build_lifecycle_transition_plan(
    previous_catalog: Iterable[SchemaChannel],
    candidate_catalog: Iterable[SchemaChannel],
    *,
    bundled_artifact_ids: Collection[str] | Mapping[str, object] | None = None,
) -> LifecycleTransitionPlan:
    """Validate and diff two catalog snapshots without deriving any lifecycle role.

    ``bundled_artifact_ids`` is an explicit exact-artifact availability boundary.
    When omitted, the active runtime bundle mapping is used.  A caller proving a
    future catalog must pass its reviewed bundle mapping rather than treating a
    catalog row or its label as evidence that its target is available.
    """
    previous = _catalog_by_line(previous_catalog, catalog_name="previous")
    candidate = _catalog_by_line(candidate_catalog, catalog_name="candidate")
    bundled = frozenset(
        schema_channels.SCHEMA_FILENAMES if bundled_artifact_ids is None else bundled_artifact_ids
    )

    _validate_catalog(
        previous,
        catalog_name="previous",
        bundled_artifact_ids=bundled,
        require_bundled_successors=False,
    )
    _validate_catalog(
        candidate,
        catalog_name="candidate",
        bundled_artifact_ids=bundled,
        require_bundled_successors=True,
    )
    _validate_transition_shape(previous, candidate)

    added: list[LifecycleLineIdentity] = []
    retained: list[LifecycleLineIdentity] = []
    refreshed: list[LifecycleLineIdentity] = []
    retired: list[RetiredLine] = []
    refreshes: list[SameLinePatchRefresh] = []

    for line_id in _ordered_line_ids(candidate):
        candidate_channel = candidate[line_id]
        previous_channel = previous.get(line_id)
        candidate_identity = LifecycleLineIdentity.from_channel(candidate_channel)
        if previous_channel is None:
            added.append(candidate_identity)
            continue

        previous_identity = LifecycleLineIdentity.from_channel(previous_channel)
        if (
            previous_channel.support_state == "supported"
            and candidate_channel.support_state == "retired"
        ):
            retired.append(RetiredLine(previous=previous_identity, candidate=candidate_identity))
        elif previous_channel.artifact_id != candidate_channel.artifact_id:
            refreshed.append(candidate_identity)
            refreshes.append(
                SameLinePatchRefresh(previous=previous_identity, candidate=candidate_identity)
            )
        else:
            retained.append(candidate_identity)

    successor_mappings = tuple(
        RetirementSuccessorMapping(
            source=retirement.candidate,
            target=LifecycleLineIdentity.from_channel(
                candidate[_successor_for(candidate, retirement.candidate.line_id)]
            ),
            declared_successor_line_id=_successor_for(candidate, retirement.candidate.line_id),
        )
        for retirement in _sort_retired_lines(retired)
    )

    return LifecycleTransitionPlan(
        added_lines=tuple(_sort_identities(added)),
        retained_lines=tuple(_sort_identities(retained)),
        refreshed_lines=tuple(_sort_identities(refreshed)),
        retired_lines=tuple(_sort_retired_lines(retired)),
        same_line_patch_refreshes=tuple(_sort_refreshes(refreshes)),
        retirement_successor_mappings=successor_mappings,
    )


def _catalog_by_line(
    catalog: Iterable[SchemaChannel],
    *,
    catalog_name: str,
) -> dict[str, SchemaChannel]:
    rows = tuple(catalog)
    if not rows:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_empty", f"{catalog_name} catalog has no rows"
        )

    by_line: dict[str, SchemaChannel] = {}
    artifact_ids: set[str] = set()
    channel_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, SchemaChannel):
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_malformed_identity",
                f"{catalog_name} catalog contains a non-SchemaChannel row",
            )
        _validate_identity(row, catalog_name=catalog_name)
        if row.line_id in by_line:
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_ambiguous_line", f"{catalog_name} repeats line '{row.line_id}'"
            )
        if row.artifact_id in artifact_ids or row.channel_id in channel_ids:
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_ambiguous_artifact",
                f"{catalog_name} repeats exact artifact/channel identity for line '{row.line_id}'",
            )
        by_line[row.line_id] = row
        artifact_ids.add(row.artifact_id)
        channel_ids.add(row.channel_id)
    return by_line


def _validate_identity(channel: SchemaChannel, *, catalog_name: str) -> None:
    text_fields = (
        channel.line_id,
        channel.artifact_id,
        channel.channel_id,
        channel.family,
        channel.artifact_version,
    )
    if any(not isinstance(value, str) or not value for value in text_fields):
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_malformed_identity",
            f"{catalog_name} has an empty or non-string identity",
        )
    if channel.channel_id != channel.artifact_id:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_malformed_identity",
            f"{catalog_name} line '{channel.line_id}' diverges channel_id from artifact_id",
        )
    if channel.family not in _VALID_FAMILIES:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_malformed_identity",
            f"{catalog_name} line '{channel.line_id}' has unsupported family '{channel.family}'",
        )
    if (
        isinstance(channel.line_number, bool)
        or not isinstance(channel.line_number, int)
        or channel.line_number <= 0
    ):
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_malformed_identity",
            f"{catalog_name} line '{channel.line_id}' has invalid numeric line",
        )
    if not _ARTIFACT_VERSION.fullmatch(channel.artifact_version):
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_malformed_identity",
            f"{catalog_name} line '{channel.line_id}' has invalid artifact version",
        )


def _validate_catalog(
    by_line: Mapping[str, SchemaChannel],
    *,
    catalog_name: str,
    bundled_artifact_ids: frozenset[str],
    require_bundled_successors: bool,
) -> None:
    _validate_roles(by_line, catalog_name=catalog_name)
    _validate_recommendation_references(by_line, catalog_name=catalog_name)
    _validate_retirement_graph(
        by_line,
        catalog_name=catalog_name,
        bundled_artifact_ids=bundled_artifact_ids,
        require_bundled_successors=require_bundled_successors,
    )


def _validate_roles(by_line: Mapping[str, SchemaChannel], *, catalog_name: str) -> None:
    for channel in by_line.values():
        if channel.support_state not in _VALID_SUPPORT_STATES:
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_malformed_identity",
                f"{catalog_name} line '{channel.line_id}' has invalid support state",
            )
        if not isinstance(channel.selectable, bool) or channel.selectable != (
            channel.support_state == "supported"
        ):
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_unselectable_state_mismatch",
                f"{catalog_name} line '{channel.line_id}' does not match selectable to support state",
            )
        for role in (
            channel.is_latest_esr,
            channel.is_product_default,
            channel.is_default_release,
        ):
            if not isinstance(role, bool):
                raise LifecycleTransitionPlanError(
                    "lifecycle_catalog_malformed_identity",
                    f"{catalog_name} line '{channel.line_id}' has non-boolean lifecycle role",
                )

    supported_esr = [
        channel
        for channel in by_line.values()
        if channel.family == "esr" and channel.support_state == "supported" and channel.selectable
    ]
    latest_rows = [channel for channel in supported_esr if channel.is_latest_esr]
    if len(latest_rows) != 1:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_ambiguous_latest_esr",
            f"{catalog_name} catalog must have exactly one supported latest ESR",
        )
    default_rows = [
        channel
        for channel in by_line.values()
        if channel.support_state == "supported"
        and channel.selectable
        and channel.is_product_default
    ]
    if len(default_rows) != 1 or default_rows[0] != latest_rows[0]:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_invalid_default_role",
            f"{catalog_name} product default must be the supported latest ESR",
        )
    release_defaults = [
        channel
        for channel in by_line.values()
        if channel.family == "release"
        and channel.support_state == "supported"
        and channel.selectable
        and channel.is_default_release
    ]
    if len(release_defaults) != 1:
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_invalid_default_release",
            f"{catalog_name} catalog must have exactly one supported default Release",
        )
    if any(
        channel.family != "release" and channel.is_default_release for channel in by_line.values()
    ):
        raise LifecycleTransitionPlanError(
            "lifecycle_catalog_invalid_default_release",
            f"{catalog_name} assigns the Release default role outside the Release family",
        )


def _validate_recommendation_references(
    by_line: Mapping[str, SchemaChannel], *, catalog_name: str
) -> None:
    for channel in by_line.values():
        target_line_id = channel.recommendation_target_line_id
        if target_line_id is None:
            continue
        target = by_line.get(target_line_id)
        if (
            channel.family != "esr"
            or target is None
            or target.family != "esr"
            or target.support_state != "supported"
            or not target.selectable
            or not target.is_latest_esr
        ):
            raise LifecycleTransitionPlanError(
                "lifecycle_catalog_invalid_recommendation_target",
                f"{catalog_name} line '{channel.line_id}' has an invalid recommendation target",
            )


def _validate_retirement_graph(
    by_line: Mapping[str, SchemaChannel],
    *,
    catalog_name: str,
    bundled_artifact_ids: frozenset[str],
    require_bundled_successors: bool,
) -> None:
    esr_rows = [channel for channel in by_line.values() if channel.family == "esr"]
    line_numbers = [channel.line_number for channel in esr_rows]
    if len(line_numbers) != len(set(line_numbers)):
        raise LifecycleTransitionPlanError(
            "retirement_successor_ambiguous",
            f"{catalog_name} catalog repeats an ESR numeric line",
        )

    _reject_successor_cycles(esr_rows, catalog_name=catalog_name)

    successors: dict[str, str] = {}
    for channel in by_line.values():
        declared = channel.retirement_successor_line_id
        if channel.family != "esr":
            if declared is not None:
                raise LifecycleTransitionPlanError(
                    "retirement_successor_family_mismatch",
                    f"{catalog_name} non-ESR line '{channel.line_id}' declares an ESR successor",
                )
            continue

        target = by_line.get(declared) if declared is not None else None
        supported_newer = sorted(
            (
                candidate
                for candidate in esr_rows
                if candidate.support_state == "supported"
                and candidate.selectable
                and candidate.line_number > channel.line_number
            ),
            key=lambda candidate: (candidate.line_number, candidate.line_id),
        )
        if not supported_newer:
            if declared is not None:
                raise LifecycleTransitionPlanError(
                    "retirement_successor_not_immediate",
                    f"{catalog_name} line '{channel.line_id}' has no newer supported ESR",
                )
            continue
        if declared is None:
            raise LifecycleTransitionPlanError(
                "retirement_successor_missing",
                f"{catalog_name} line '{channel.line_id}' lacks an immediate newer ESR successor",
            )
        if target is None:
            raise LifecycleTransitionPlanError(
                "retirement_successor_ambiguous",
                f"{catalog_name} line '{channel.line_id}' references unknown successor '{declared}'",
            )
        if target.family != "esr":
            raise LifecycleTransitionPlanError(
                "retirement_successor_family_mismatch",
                f"{catalog_name} line '{channel.line_id}' targets non-ESR '{declared}'",
            )
        if target.support_state != "supported" or not target.selectable:
            raise LifecycleTransitionPlanError(
                "retirement_successor_unsupported_target",
                f"{catalog_name} line '{channel.line_id}' targets unsupported or unselectable '{declared}'",
            )
        if require_bundled_successors and target.artifact_id not in bundled_artifact_ids:
            raise LifecycleTransitionPlanError(
                "retirement_successor_unbundled_target",
                f"{catalog_name} line '{channel.line_id}' targets unbundled '{declared}'",
            )
        if target.line_number <= channel.line_number:
            raise LifecycleTransitionPlanError(
                "retirement_successor_not_newer",
                f"{catalog_name} line '{channel.line_id}' targets same or older ESR '{declared}'",
            )
        immediate = supported_newer[0]
        if target.line_id != immediate.line_id:
            raise LifecycleTransitionPlanError(
                "retirement_successor_skips_supported_intermediate",
                f"{catalog_name} line '{channel.line_id}' skips immediate ESR '{immediate.line_id}'",
            )
        successors[channel.line_id] = target.line_id

    for line_id in successors:
        seen: set[str] = set()
        cursor = line_id
        while cursor in successors:
            if cursor in seen:
                raise LifecycleTransitionPlanError(
                    "retirement_successor_cycle",
                    f"{catalog_name} retirement successor graph contains a cycle at '{cursor}'",
                )
            seen.add(cursor)
            cursor = successors[cursor]


def _reject_successor_cycles(esr_rows: Iterable[SchemaChannel], *, catalog_name: str) -> None:
    """Detect a declared cycle before reporting a secondary edge defect."""
    declared = {
        channel.line_id: channel.retirement_successor_line_id
        for channel in esr_rows
        if channel.retirement_successor_line_id is not None
    }
    for line_id in declared:
        seen: set[str] = set()
        cursor = line_id
        while cursor in declared:
            if cursor in seen:
                raise LifecycleTransitionPlanError(
                    "retirement_successor_cycle",
                    f"{catalog_name} retirement successor graph contains a cycle at '{cursor}'",
                )
            seen.add(cursor)
            cursor = declared[cursor]


def _validate_transition_shape(
    previous: Mapping[str, SchemaChannel], candidate: Mapping[str, SchemaChannel]
) -> None:
    missing_lines = sorted(set(previous) - set(candidate))
    if missing_lines:
        raise LifecycleTransitionPlanError(
            "lifecycle_transition_line_removed",
            "candidate removes existing lifecycle line(s): " + ", ".join(missing_lines),
        )

    for line_id, candidate_channel in candidate.items():
        previous_channel = previous.get(line_id)
        if previous_channel is None:
            if candidate_channel.support_state == "retired":
                raise LifecycleTransitionPlanError(
                    "lifecycle_transition_retired_line_added",
                    f"candidate adds already-retired line '{line_id}'",
                )
            continue
        if (
            previous_channel.family != candidate_channel.family
            or previous_channel.line_number != candidate_channel.line_number
        ):
            raise LifecycleTransitionPlanError(
                "lifecycle_transition_line_identity_changed",
                f"line '{line_id}' changes family or numeric line identity",
            )
        if (
            previous_channel.support_state == "retired"
            and candidate_channel.support_state != "retired"
        ):
            raise LifecycleTransitionPlanError(
                "lifecycle_transition_unretire_forbidden",
                f"candidate reactivates retired line '{line_id}'",
            )
        if (
            previous_channel.support_state == "supported"
            and candidate_channel.support_state == "retired"
        ):
            if candidate_channel.family != "esr":
                raise LifecycleTransitionPlanError(
                    "lifecycle_transition_non_esr_retirement",
                    f"candidate retires non-ESR line '{line_id}'",
                )
            if previous_channel.artifact_id != candidate_channel.artifact_id:
                raise LifecycleTransitionPlanError(
                    "lifecycle_transition_refresh_and_retire",
                    f"line '{line_id}' cannot refresh and retire in one transition",
                )
        elif previous_channel.support_state == "retired" and (
            previous_channel.artifact_id != candidate_channel.artifact_id
        ):
            raise LifecycleTransitionPlanError(
                "lifecycle_transition_retired_refresh",
                f"candidate refreshes already-retired line '{line_id}'",
            )


def _successor_for(candidate: Mapping[str, SchemaChannel], line_id: str) -> str:
    successor = candidate[line_id].retirement_successor_line_id
    if successor is None:  # Defensive: _validate_retirement_graph guarantees this cannot occur.
        raise LifecycleTransitionPlanError(
            "retirement_successor_missing", f"retired line '{line_id}' has no successor"
        )
    return successor


def _line_sort_key(identity: LifecycleLineIdentity) -> tuple[str, int, str, str]:
    return (identity.family, identity.line_number, identity.line_id, identity.artifact_id)


def _sort_identities(
    identities: Iterable[LifecycleLineIdentity],
) -> list[LifecycleLineIdentity]:
    return sorted(identities, key=_line_sort_key)


def _sort_retired_lines(lines: Iterable[RetiredLine]) -> list[RetiredLine]:
    return sorted(lines, key=lambda line: _line_sort_key(line.candidate))


def _sort_refreshes(refreshes: Iterable[SameLinePatchRefresh]) -> list[SameLinePatchRefresh]:
    return sorted(refreshes, key=lambda refresh: _line_sort_key(refresh.candidate))


def _ordered_line_ids(catalog: Mapping[str, SchemaChannel]) -> list[str]:
    return [
        identity.line_id
        for identity in _sort_identities(
            LifecycleLineIdentity.from_channel(channel) for channel in catalog.values()
        )
    ]
