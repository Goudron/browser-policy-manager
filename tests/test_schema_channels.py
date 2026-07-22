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
    SCHEMA_SOURCES,
    SUPPORTED_ESR_SCHEMA_CHANNELS,
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
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.13", "esr-153.0", "release-153")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.13", "esr-153.0", "release-153"}
    assert SUPPORTED_ESR_SCHEMA_CHANNELS == ("esr-140.13", "esr-153.0")
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.13"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-153"
    assert CURRENT_ESR_SCHEMA_CHANNEL == DEFAULT_SCHEMA_CHANNEL
    assert CURRENT_RELEASE_SCHEMA_CHANNEL == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert SCHEMA_LABELS["esr-140.13"] == "ESR 140.13"
    assert SCHEMA_LABELS["esr-153.0"] == "ESR 153.0"
    assert SCHEMA_LABELS["release-153"] == "Release 153"
    assert SCHEMA_FILENAMES["esr-140.13"] == "firefox-esr-140.13.json"
    assert SCHEMA_FILENAMES["esr-153.0"] == "firefox-esr-153.0.json"
    assert SCHEMA_FILENAMES["release-153"] == "firefox-release-153.json"
    assert RAW_SCHEMA_DIRS["esr-140.13"] == "esr14013"
    assert RAW_SCHEMA_DIRS["esr-153.0"] == "esr1530"
    assert RAW_SCHEMA_DIRS["release-153"] == "release153"
    assert SCHEMA_MOZILLA_VERSIONS["esr-140.13"] == "140.13"
    assert SCHEMA_MOZILLA_VERSIONS["esr-153.0"] == "153.0"
    assert SCHEMA_MOZILLA_VERSIONS["release-153"] == "153.0"
    assert SCHEMA_SOURCES == {
        "esr-140.13": "mozilla-policy-templates-v7.12",
        "esr-153.0": "mozilla-policy-templates-v8.0",
        "release-153": "mozilla-policy-templates-v8.0",
    }
    assert get_schema_channel("release-153") is not None
    assert get_schema_channel("unknown-channel") is None


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.13"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["filenames"] == SCHEMA_FILENAMES
    assert catalog["mozilla_versions"] == SCHEMA_MOZILLA_VERSIONS
    assert catalog["sources"] == SCHEMA_SOURCES
    assert catalog["esr_channels"] == list(SUPPORTED_ESR_SCHEMA_CHANNELS)
    assert catalog["options"] == [
        {
            "value": "esr-140.13",
            "label": "ESR 140.13",
            "i18n_key": "profiles.firefox_schema_esr_140_13",
        },
        {
            "value": "esr-153.0",
            "label": "ESR 153.0",
            "i18n_key": "profiles.firefox_schema_esr_153_0",
        },
        {
            "value": "release-153",
            "label": "Release 153",
            "i18n_key": "profiles.firefox_schema_release_153",
        },
    ]
    assert get_schema_label("release-153") == "Release 153"


def test_schema_channels_catalog_accepts_localized_label_overrides():
    catalog = build_schema_channels_catalog(
        label_overrides={"release-153": "релиз 153"}
    )

    assert catalog["labels"]["release-153"] == "релиз 153"
    assert catalog["options"][-1]["label"] == "релиз 153"
