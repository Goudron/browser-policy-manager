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
    assert SUPPORTED_SCHEMA_CHANNELS == ("esr-140.11", "release-151")
    assert SUPPORTED_SCHEMA_CHANNEL_SET == {"esr-140.11", "release-151"}
    assert DEFAULT_SCHEMA_CHANNEL == "esr-140.11"
    assert DEFAULT_RELEASE_SCHEMA_CHANNEL == "release-151"
    assert SCHEMA_LABELS["esr-140.11"] == "ESR 140.11"
    assert SCHEMA_LABELS["release-151"] == "Release 151"
    assert SCHEMA_FILENAMES["esr-140.11"] == "firefox-esr-140.11.json"
    assert SCHEMA_FILENAMES["release-151"] == "firefox-release-151.json"
    assert RAW_SCHEMA_DIRS["esr-140.11"] == "esr14011"
    assert RAW_SCHEMA_DIRS["release-151"] == "release151"


def test_schema_channels_catalog_matches_constants():
    catalog = build_schema_channels_catalog()

    assert catalog["supported_channels"] == list(SUPPORTED_SCHEMA_CHANNELS)
    assert catalog["default_channel"] == DEFAULT_SCHEMA_CHANNEL
    assert catalog["default_release_channel"] == DEFAULT_RELEASE_SCHEMA_CHANNEL
    assert catalog["default_label"] == "ESR 140.11"
    assert catalog["labels"] == SCHEMA_LABELS
    assert catalog["options"] == [
        {"value": "esr-140.11", "label": "ESR 140.11"},
        {"value": "release-151", "label": "Release 151"},
    ]
    assert get_schema_label("release-151") == "Release 151"
