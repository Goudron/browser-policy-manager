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
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.11", "release-151")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.11", "release-151"}
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.11"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-151"
    assert CURRENT_ESR_SCHEMA_CHANNEL == DEFAULT_SCHEMA_CHANNEL
    assert CURRENT_RELEASE_SCHEMA_CHANNEL == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert SCHEMA_LABELS["esr-140.11"] == "ESR 140.11"
    assert SCHEMA_LABELS["release-151"] == "Release 151"
    assert SCHEMA_FILENAMES["esr-140.11"] == "firefox-esr-140.11.json"
    assert SCHEMA_FILENAMES["release-151"] == "firefox-release-151.json"
    assert RAW_SCHEMA_DIRS["esr-140.11"] == "esr14011"
    assert RAW_SCHEMA_DIRS["release-151"] == "release151"
    assert SCHEMA_MOZILLA_VERSIONS["esr-140.11"] == "140.11"
    assert SCHEMA_MOZILLA_VERSIONS["release-151"] == "151.0"
    assert get_schema_channel("release-151") is not None
    assert get_schema_channel("unknown-channel") is None


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.11"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["filenames"] == SCHEMA_FILENAMES
    assert catalog["mozilla_versions"] == SCHEMA_MOZILLA_VERSIONS
    assert catalog["options"] == [
        {"value": "esr-140.11", "label": "ESR 140.11"},
        {"value": "release-151", "label": "Release 151"},
    ]
    assert get_schema_label("release-151") == "Release 151"
