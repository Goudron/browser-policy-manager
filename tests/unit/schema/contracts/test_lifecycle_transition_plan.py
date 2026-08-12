from __future__ import annotations

from dataclasses import replace

import pytest

from app.core.lifecycle_transition_plan import (
    LifecycleTransitionPlanError,
    build_lifecycle_transition_plan,
)
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG, SchemaChannel


def _by_line(
    channels: tuple[SchemaChannel, ...] = SCHEMA_CHANNEL_CATALOG,
) -> dict[str, SchemaChannel]:
    return {channel.line_id: channel for channel in channels}


def _replace_line(
    channels: tuple[SchemaChannel, ...], line_id: str, **changes: object
) -> tuple[SchemaChannel, ...]:
    return tuple(
        replace(channel, **changes) if channel.line_id == line_id else channel
        for channel in channels
    )


def _bundled(channels: tuple[SchemaChannel, ...]) -> set[str]:
    return {channel.artifact_id for channel in channels}


def test_current_catalog_diff_is_empty_and_ignores_declaration_order() -> None:
    plan = build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        tuple(reversed(SCHEMA_CHANNEL_CATALOG)),
        bundled_artifact_ids=_bundled(SCHEMA_CHANNEL_CATALOG),
    )

    assert plan.as_dict() == {
        "added_lines": [],
        "retained_lines": [
            {
                "line_id": "esr-115",
                "artifact_id": "esr-115.38",
                "channel_id": "esr-115.38",
                "family": "esr",
                "line_number": 115,
                "artifact_version": "115.38",
                "support_state": "supported",
                "selectable": True,
            },
            {
                "line_id": "esr-140",
                "artifact_id": "esr-140.13",
                "channel_id": "esr-140.13",
                "family": "esr",
                "line_number": 140,
                "artifact_version": "140.13",
                "support_state": "supported",
                "selectable": True,
            },
            {
                "line_id": "esr-153",
                "artifact_id": "esr-153.0",
                "channel_id": "esr-153.0",
                "family": "esr",
                "line_number": 153,
                "artifact_version": "153.0",
                "support_state": "supported",
                "selectable": True,
            },
            {
                "line_id": "release-153",
                "artifact_id": "release-153",
                "channel_id": "release-153",
                "family": "release",
                "line_number": 153,
                "artifact_version": "153.0",
                "support_state": "supported",
                "selectable": True,
            },
        ],
        "refreshed_lines": [],
        "retired_lines": [],
        "same_line_patch_refreshes": [],
        "retirement_successor_mappings": [],
    }


def test_same_line_patch_refresh_is_exact_and_deterministic() -> None:
    candidate = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-140",
        artifact_id="esr-140.14",
        channel_id="esr-140.14",
        artifact_version="140.14",
    )
    plan = build_lifecycle_transition_plan(
        tuple(reversed(SCHEMA_CHANNEL_CATALOG)),
        candidate,
        bundled_artifact_ids=_bundled(candidate),
    )

    assert [line.line_id for line in plan.refreshed_lines] == ["esr-140"]
    assert [line.line_id for line in plan.retained_lines] == [
        "esr-115",
        "esr-153",
        "release-153",
    ]
    assert len(plan.same_line_patch_refreshes) == 1
    refresh = plan.same_line_patch_refreshes[0]
    assert refresh.line_id == "esr-140"
    assert refresh.previous.artifact_id == "esr-140.13"
    assert refresh.candidate.artifact_id == "esr-140.14"


def test_added_line_is_classified_without_relying_on_catalog_declaration_order() -> None:
    channels = _by_line()
    candidate = tuple(
        replace(
            channels["esr-153"],
            is_latest_esr=False,
            is_product_default=False,
            retirement_successor_line_id="esr-165",
        )
        if channel.line_id == "esr-153"
        else replace(channel, recommendation_target_line_id="esr-165")
        if channel.line_id in {"esr-115", "esr-140"}
        else channel
        for channel in SCHEMA_CHANNEL_CATALOG
    ) + (
        replace(
            channels["esr-153"],
            line_id="esr-165",
            artifact_id="esr-165.0",
            channel_id="esr-165.0",
            line_number=165,
            artifact_version="165.0",
            is_latest_esr=True,
            is_product_default=True,
            retirement_successor_line_id=None,
            recommendation_target_line_id=None,
        ),
    )
    plan = build_lifecycle_transition_plan(
        tuple(reversed(SCHEMA_CHANNEL_CATALOG)),
        tuple(reversed(candidate)),
        bundled_artifact_ids=_bundled(candidate),
    )

    assert [line.line_id for line in plan.added_lines] == ["esr-165"]
    assert [line.line_id for line in plan.retained_lines] == [
        "esr-115",
        "esr-140",
        "esr-153",
        "release-153",
    ]


def test_retirement_maps_esr140_to_exact_immediate_esr153_successor() -> None:
    candidate = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-140",
        support_state="retired",
        selectable=False,
    )
    candidate = _replace_line(
        candidate,
        "esr-115",
        retirement_successor_line_id="esr-153",
    )
    plan = build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        tuple(reversed(candidate)),
        bundled_artifact_ids=_bundled(candidate),
    )

    assert [line.line_id for line in plan.retired_lines] == ["esr-140"]
    assert len(plan.retirement_successor_mappings) == 1
    mapping = plan.retirement_successor_mappings[0]
    assert mapping.declared_successor_line_id == "esr-153"
    assert mapping.source.line_id == "esr-140"
    assert mapping.source.artifact_id == "esr-140.13"
    assert mapping.target.line_id == "esr-153"
    assert mapping.target.artifact_id == "esr-153.0"


def test_retirement_maps_esr115_to_exact_immediate_esr140_successor() -> None:
    candidate = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-115",
        support_state="retired",
        selectable=False,
    )
    plan = build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        candidate,
        bundled_artifact_ids=_bundled(candidate),
    )

    assert [
        (item.source.line_id, item.target.line_id) for item in plan.retirement_successor_mappings
    ] == [("esr-115", "esr-140")]


@pytest.mark.parametrize(
    ("candidate", "bundled_artifact_ids", "code"),
    [
        (
            lambda: _replace_line(
                _replace_line(
                    SCHEMA_CHANNEL_CATALOG,
                    "esr-140",
                    support_state="retired",
                    selectable=False,
                    retirement_successor_line_id=None,
                ),
                "esr-115",
                retirement_successor_line_id="esr-153",
            ),
            None,
            "retirement_successor_missing",
        ),
        (
            lambda: _replace_line(
                SCHEMA_CHANNEL_CATALOG,
                "esr-115",
                retirement_successor_line_id="esr-153",
            ),
            None,
            "retirement_successor_skips_supported_intermediate",
        ),
        (
            lambda: _replace_line(
                SCHEMA_CHANNEL_CATALOG,
                "esr-140",
                retirement_successor_line_id="release-153",
            ),
            None,
            "retirement_successor_family_mismatch",
        ),
        (
            lambda: _replace_line(
                SCHEMA_CHANNEL_CATALOG,
                "esr-140",
                retirement_successor_line_id="esr-115",
            ),
            None,
            "retirement_successor_cycle",
        ),
        (
            lambda: SCHEMA_CHANNEL_CATALOG,
            {"esr-115.38", "esr-153.0", "release-153"},
            "retirement_successor_unbundled_target",
        ),
    ],
)
def test_catalog_graph_rejects_unsafe_or_unbundled_successors(
    candidate: object,
    bundled_artifact_ids: set[str] | None,
    code: str,
) -> None:
    assert callable(candidate)
    resolved_candidate = candidate()
    assert isinstance(resolved_candidate, tuple)
    with pytest.raises(LifecycleTransitionPlanError, match=code) as error:
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            resolved_candidate,
            bundled_artifact_ids=(
                _bundled(resolved_candidate)
                if bundled_artifact_ids is None
                else bundled_artifact_ids
            ),
        )
    assert error.value.code == code


def test_retirement_rejects_unsupported_successor_and_refresh_in_same_transition() -> None:
    candidate = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-140",
        support_state="retired",
        selectable=False,
    )
    with pytest.raises(
        LifecycleTransitionPlanError, match="retirement_successor_unsupported_target"
    ):
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            candidate,
            bundled_artifact_ids=_bundled(candidate),
        )

    candidate = _replace_line(
        candidate,
        "esr-115",
        retirement_successor_line_id="esr-153",
    )
    candidate = _replace_line(
        candidate,
        "esr-140",
        artifact_id="esr-140.14",
        channel_id="esr-140.14",
        artifact_version="140.14",
    )
    with pytest.raises(
        LifecycleTransitionPlanError, match="lifecycle_transition_refresh_and_retire"
    ):
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            candidate,
            bundled_artifact_ids=_bundled(candidate),
        )


def test_transition_rejects_removed_or_reactivated_or_ambiguous_lines() -> None:
    candidate = tuple(channel for channel in SCHEMA_CHANNEL_CATALOG if channel.line_id != "esr-115")
    with pytest.raises(LifecycleTransitionPlanError, match="lifecycle_transition_line_removed"):
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            candidate,
            bundled_artifact_ids=_bundled(candidate),
        )

    retired_previous = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-115",
        support_state="retired",
        selectable=False,
    )
    with pytest.raises(
        LifecycleTransitionPlanError, match="lifecycle_transition_unretire_forbidden"
    ):
        build_lifecycle_transition_plan(
            retired_previous,
            SCHEMA_CHANNEL_CATALOG,
            bundled_artifact_ids=_bundled(SCHEMA_CHANNEL_CATALOG),
        )

    duplicate_number = replace(
        _by_line()["esr-115"],
        line_id="esr-115-alias",
        artifact_id="esr-115.alias",
        channel_id="esr-115.alias",
    )
    with pytest.raises(LifecycleTransitionPlanError, match="retirement_successor_ambiguous"):
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            SCHEMA_CHANNEL_CATALOG + (duplicate_number,),
            bundled_artifact_ids=_bundled(SCHEMA_CHANNEL_CATALOG + (duplicate_number,)),
        )


def test_transition_rejects_malformed_exact_identity_without_mutating_inputs() -> None:
    candidate = _replace_line(
        SCHEMA_CHANNEL_CATALOG,
        "esr-140",
        channel_id="different-channel-id",
    )
    original = tuple(SCHEMA_CHANNEL_CATALOG)
    with pytest.raises(LifecycleTransitionPlanError, match="lifecycle_catalog_malformed_identity"):
        build_lifecycle_transition_plan(
            SCHEMA_CHANNEL_CATALOG,
            candidate,
            bundled_artifact_ids=_bundled(candidate),
        )
    assert SCHEMA_CHANNEL_CATALOG == original
