from dataclasses import replace

import pytest

import app.core.schema_channels as schema_channels
from app.core.profile_recommendation import profile_conversion_recommendation
from app.core.schema_channels import (
    CURRENT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_SCHEMA_CHANNEL,
    HEADER_SCHEMA_CHANNEL_VALUES,
    HEADER_SCHEMA_CHANNELS,
    LATEST_ESR_SCHEMA_CHANNEL,
    SCHEMA_CHANNEL_CATALOG,
    SCHEMA_CHANNELS,
    SCHEMA_FILENAMES,
    SCHEMA_LABELS,
    SCHEMA_MOZILLA_VERSIONS,
    SCHEMA_SOURCES,
    SUPPORTED_ESR_SCHEMA_CHANNELS,
    SUPPORTED_SCHEMA_CHANNEL_SET,
    SUPPORTED_SCHEMA_CHANNELS,
    RetiredSchemaChannelError,
    UnbundledSchemaChannelError,
    UnknownSchemaChannelError,
    build_schema_channels_catalog,
    get_schema_channel,
    get_schema_label,
    ordered_schema_channels,
    require_supported_schema_channel,
    retired_schema_channel_artifact_ids,
    retired_schema_channels,
)


def test_schema_channels_are_four_independent_catalog_artifacts_in_public_order():
    assert tuple(channel.value for channel in SCHEMA_CHANNELS) == SUPPORTED_SCHEMA_CHANNELS
    assert SUPPORTED_SCHEMA_CHANNELS == (
        "release-153",
        "esr-153.0",
        "esr-140.13",
        "esr-115.39",
    )
    assert HEADER_SCHEMA_CHANNEL_VALUES == SUPPORTED_SCHEMA_CHANNELS
    assert tuple(channel.value for channel in HEADER_SCHEMA_CHANNELS) == SUPPORTED_SCHEMA_CHANNELS
    assert SUPPORTED_SCHEMA_CHANNEL_SET == set(SUPPORTED_SCHEMA_CHANNELS)
    assert SUPPORTED_ESR_SCHEMA_CHANNELS == ("esr-153.0", "esr-140.13", "esr-115.39")
    assert DEFAULT_SCHEMA_CHANNEL == LATEST_ESR_SCHEMA_CHANNEL == "esr-153.0"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == CURRENT_RELEASE_SCHEMA_CHANNEL == "release-153"
    assert SCHEMA_LABELS == {channel.value: channel.label for channel in SCHEMA_CHANNELS}
    assert SCHEMA_FILENAMES == {channel.value: channel.filename for channel in SCHEMA_CHANNELS}
    assert SCHEMA_MOZILLA_VERSIONS == {
        channel.value: channel.mozilla_version for channel in SCHEMA_CHANNELS
    }
    assert SCHEMA_SOURCES == {channel.value: channel.source_tag for channel in SCHEMA_CHANNELS}
    assert SCHEMA_FILENAMES["esr-115.39"] == "firefox-esr-115.39.json"
    assert get_schema_channel("release-153") is not None
    assert get_schema_channel("unknown-channel") is None


def test_catalog_serialization_uses_lifecycle_roles_and_public_order():
    catalog = build_schema_channels_catalog()

    assert catalog["catalog_version"] == 1
    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["selector_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["header_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == "esr-153.0"
    assert catalog["default_release_channel"] == "release-153"
    assert catalog["latest_esr_channel"] == "esr-153.0"
    assert catalog["default_label"] == "ESR 153.0"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["filenames"] == SCHEMA_FILENAMES
    assert catalog["mozilla_versions"] == SCHEMA_MOZILLA_VERSIONS
    assert catalog["sources"] == SCHEMA_SOURCES
    assert catalog["esr_channels"] == list(SUPPORTED_ESR_SCHEMA_CHANNELS)
    assert [option["value"] for option in catalog["options"]] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["options"][2]["recommendation_target"] == "esr-153.0"
    assert catalog["options"][3]["recommendation_target"] == "esr-153.0"
    assert get_schema_label("release-153") == "Release 153"


def test_public_order_does_not_depend_on_catalog_declaration_order():
    assert ordered_schema_channels(tuple(reversed(SCHEMA_CHANNEL_CATALOG))) == SCHEMA_CHANNELS


def test_supported_resolution_fails_closed_for_unknown_retired_and_unbundled_channels(
    monkeypatch: pytest.MonkeyPatch,
):
    assert require_supported_schema_channel("esr-115.39").line_id == "esr-115"

    with pytest.raises(UnknownSchemaChannelError):
        require_supported_schema_channel("unknown")

    channel = get_schema_channel("esr-140.13")
    assert channel is not None
    retired = replace(channel, support_state="retired", selectable=False)
    monkeypatch.setattr(
        schema_channels,
        "SCHEMA_CHANNEL_CATALOG",
        tuple(
            retired if entry.artifact_id == retired.artifact_id else entry
            for entry in SCHEMA_CHANNEL_CATALOG
        ),
    )
    with pytest.raises(RetiredSchemaChannelError):
        require_supported_schema_channel("esr-140.13")

    monkeypatch.undo()
    monkeypatch.setattr(
        schema_channels, "SCHEMA_FILENAMES", {"release-153": "firefox-release-153.json"}
    )
    with pytest.raises(UnbundledSchemaChannelError):
        require_supported_schema_channel("esr-140.13")


def test_retired_catalog_status_keeps_the_exact_artifact_visible_only_to_runtime_readiness(
    monkeypatch: pytest.MonkeyPatch,
):
    source = get_schema_channel("esr-140.13")
    assert source is not None
    retired = replace(source, support_state="retired", selectable=False)
    monkeypatch.setattr(
        schema_channels,
        "SCHEMA_CHANNEL_CATALOG",
        tuple(
            retired if channel.artifact_id == retired.artifact_id else channel
            for channel in SCHEMA_CHANNEL_CATALOG
        ),
    )

    assert retired_schema_channels() == (retired,)
    assert retired_schema_channel_artifact_ids() == ("esr-140.13",)
    assert "esr-140.13" not in build_schema_channels_catalog()["supported_channels"]


def test_schema_channels_catalog_accepts_localized_label_overrides():
    catalog = build_schema_channels_catalog(label_overrides={"release-153": "релиз 153"})

    assert catalog["labels"]["release-153"] == "релиз 153"
    assert catalog["options"][0]["label"] == "релиз 153"


def test_latest_esr_recommendation_uses_catalog_roles_not_declaration_order():
    bundled = {channel.artifact_id: channel.filename for channel in SCHEMA_CHANNEL_CATALOG}

    recommendation = profile_conversion_recommendation(
        schema_version="esr-115.39",
        revision=7,
        is_active=True,
        channels=tuple(reversed(SCHEMA_CHANNEL_CATALOG)),
        bundled_artifact_ids=bundled,
    )

    assert recommendation == {
        "recommendation_id": "schema-conversion.older-esr-recommendation",
        "reason_code": "supported_older_esr_to_latest_esr",
        "profile_revision": 7,
        "source": {"line_id": "esr-115", "artifact_id": "esr-115.39"},
        "target": {
            "line_id": "esr-153",
            "artifact_id": "esr-153.0",
            "label": "ESR 153.0",
            "i18n_key": "profiles.firefox_schema_esr_153_0",
        },
        "action": {
            "action_id": "conversion-preview",
            "preview_target_artifact_id": "esr-153.0",
        },
    }


def test_latest_esr_recommendation_fails_closed_for_catalog_and_profile_states():
    bundled = {channel.artifact_id: channel.filename for channel in SCHEMA_CHANNEL_CATALOG}
    for source in ("esr-115.39", "esr-140.13"):
        recommendation = profile_conversion_recommendation(
            schema_version=source,
            revision=1,
            is_active=True,
            channels=SCHEMA_CHANNEL_CATALOG,
            bundled_artifact_ids=bundled,
        )
        assert recommendation is not None
        assert recommendation["target"]["artifact_id"] == "esr-153.0"

    for source in ("release-153", "esr-153.0", "unknown"):
        assert (
            profile_conversion_recommendation(
                schema_version=source,
                revision=1,
                is_active=True,
                channels=SCHEMA_CHANNEL_CATALOG,
                bundled_artifact_ids=bundled,
            )
            is None
        )
    assert (
        profile_conversion_recommendation(
            schema_version="esr-140.13",
            revision=1,
            is_active=False,
            channels=SCHEMA_CHANNEL_CATALOG,
            bundled_artifact_ids=bundled,
        )
        is None
    )

    latest = next(channel for channel in SCHEMA_CHANNEL_CATALOG if channel.is_latest_esr)
    ambiguous = SCHEMA_CHANNEL_CATALOG + (replace(latest, artifact_id="esr-153.1"),)
    assert (
        profile_conversion_recommendation(
            schema_version="esr-115.39",
            revision=1,
            is_active=True,
            channels=ambiguous,
            bundled_artifact_ids=bundled,
        )
        is None
    )
    assert (
        profile_conversion_recommendation(
            schema_version="esr-115.39",
            revision=1,
            is_active=True,
            channels=SCHEMA_CHANNEL_CATALOG,
            bundled_artifact_ids={"esr-115.39": "firefox-esr-115.39.json"},
        )
        is None
    )
