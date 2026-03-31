from __future__ import annotations

SUPPORTED_SCHEMA_CHANNELS: tuple[str, ...] = ("esr-140.9", "release-149")
SUPPORTED_SCHEMA_CHANNEL_SET: frozenset[str] = frozenset(SUPPORTED_SCHEMA_CHANNELS)

DEFAULT_SCHEMA_CHANNEL = "esr-140.9"
DEFAULT_RELEASE_SCHEMA_CHANNEL = "release-149"

SCHEMA_LABELS: dict[str, str] = {
    "esr-140.9": "ESR 140.9",
    "release-149": "Release 149",
}

SCHEMA_FILENAMES: dict[str, str] = {
    "esr-140.9": "firefox-esr-140.9.json",
    "release-149": "firefox-release-149.json",
}

RAW_SCHEMA_DIRS: dict[str, str] = {
    "esr-140.9": "esr1409",
    "release-149": "release149",
}


def get_schema_label(channel: str) -> str:
    return SCHEMA_LABELS.get(channel, channel)


def build_schema_channels_catalog() -> dict[str, object]:
    return {
        "supported_channels": list(SUPPORTED_SCHEMA_CHANNELS),
        "default_channel": DEFAULT_SCHEMA_CHANNEL,
        "default_release_channel": DEFAULT_RELEASE_SCHEMA_CHANNEL,
        "default_label": get_schema_label(DEFAULT_SCHEMA_CHANNEL),
        "labels": dict(SCHEMA_LABELS),
        "options": [
            {"value": channel, "label": get_schema_label(channel)}
            for channel in SUPPORTED_SCHEMA_CHANNELS
        ],
    }
