from app.core.schema_channels import (
    CURRENT_ESR_SCHEMA_CHANNEL,
    CURRENT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_SCHEMA_CHANNEL,
    RAW_SCHEMA_DIRS,
    SCHEMA_CHANNELS,
    SCHEMA_FILENAMES,
    SCHEMA_LABELS,
    SCHEMA_MOZILLA_VERSIONS,
    SUPPORTED_SCHEMA_CHANNEL_SET,
    SUPPORTED_SCHEMA_CHANNELS,
    build_schema_channels_catalog,
    get_schema_channel,
    get_schema_label,
)


def test_schema_channels_constants_are_consistent():
    assert tuple(channel.value for channel in SCHEMA_CHANNELS) == SUPPORTED_SCHEMA_CHANNELS
    assert SCHEMA_LABELS == {channel.value: channel.label for channel in SCHEMA_CHANNELS}
    assert SCHEMA_FILENAMES == {channel.value: channel.filename for channel in SCHEMA_CHANNELS}
    assert RAW_SCHEMA_DIRS == {channel.value: channel.raw_dir for channel in SCHEMA_CHANNELS}
    assert SCHEMA_MOZILLA_VERSIONS == {
        channel.value: channel.mozilla_version for channel in SCHEMA_CHANNELS
    }
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.12", "release-152")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.12", "release-152"}
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.12"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-152"
    assert CURRENT_ESR_SCHEMA_CHANNEL == DEFAULT_SCHEMA_CHANNEL
    assert CURRENT_RELEASE_SCHEMA_CHANNEL == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert SCHEMA_LABELS["esr-140.12"] == "ESR 140.12"
    assert SCHEMA_LABELS["release-152"] == "Release 152"
    assert SCHEMA_FILENAMES["esr-140.12"] == "firefox-esr-140.12.json"
    assert SCHEMA_FILENAMES["release-152"] == "firefox-release-152.json"
    assert RAW_SCHEMA_DIRS["esr-140.12"] == "esr14012"
    assert RAW_SCHEMA_DIRS["release-152"] == "release152"
    assert SCHEMA_MOZILLA_VERSIONS["esr-140.12"] == "140.12"
    assert SCHEMA_MOZILLA_VERSIONS["release-152"] == "152.0"
    assert get_schema_channel("release-152") is not None
    assert get_schema_channel("unknown-channel") is None


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.12"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["filenames"] == SCHEMA_FILENAMES
    assert catalog["mozilla_versions"] == SCHEMA_MOZILLA_VERSIONS
    assert catalog["options"] == [
        {"value": "esr-140.12", "label": "ESR 140.12"},
        {"value": "release-152", "label": "Release 152"},
    ]
    assert get_schema_label("release-152") == "Release 152"
