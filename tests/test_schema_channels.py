from app.core.schema_channels import (
    DEFAULT_RELEASE_SCHEMA_CHANNEL,
    DEFAULT_SCHEMA_CHANNEL,
    RAW_SCHEMA_DIRS,
    SCHEMA_FILENAMES,
    SCHEMA_LABELS,
    SUPPORTED_SCHEMA_CHANNEL_SET,
    SUPPORTED_SCHEMA_CHANNELS,
    build_schema_channels_catalog,
    get_schema_label,
)


def test_schema_channels_constants_are_consistent():
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.10", "release-150")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.10", "release-150"}
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.10"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-150"
    assert SCHEMA_LABELS["esr-140.10"] == "ESR 140.10"
    assert SCHEMA_LABELS["release-150"] == "Release 150"
    assert SCHEMA_FILENAMES["esr-140.10"] == "firefox-esr-140.10.json"
    assert SCHEMA_FILENAMES["release-150"] == "firefox-release-150.json"
    assert RAW_SCHEMA_DIRS["esr-140.10"] == "esr14010"
    assert RAW_SCHEMA_DIRS["release-150"] == "release150"


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.10"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["options"] == [
        {"value": "esr-140.10", "label": "ESR 140.10"},
        {"value": "release-150", "label": "Release 150"},
    ]
    assert get_schema_label("release-150") == "Release 150"
