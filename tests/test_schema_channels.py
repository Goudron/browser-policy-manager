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
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.9", "release-149")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.9", "release-149"}
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.9"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-149"
    assert SCHEMA_LABELS["esr-140.9"] == "ESR 140.9"
    assert SCHEMA_LABELS["release-149"] == "Release 149"
    assert SCHEMA_FILENAMES["esr-140.9"] == "firefox-esr-140.9.json"
    assert SCHEMA_FILENAMES["release-149"] == "firefox-release-149.json"
    assert RAW_SCHEMA_DIRS["esr-140.9"] == "esr1409"
    assert RAW_SCHEMA_DIRS["release-149"] == "release149"


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.9"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["options"] == [
        {"value": "esr-140.9", "label": "ESR 140.9"},
        {"value": "release-149", "label": "Release 149"},
    ]
    assert get_schema_label("release-149") == "Release 149"
