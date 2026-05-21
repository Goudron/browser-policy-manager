from __future__ import annotations

SUPPORTED_SCHEMA_CHANNELS: tuple[str, ...] = ("esr-140.11", "release-151")
SUPPORTED_SCHEMA_CHANNEL_SET: frozenset[str] = frozenset(SUPPORTED_SCHEMA_CHANNELS)

DEFAULT_SCHEMA_CHANNEL = "esr-140.11"
DEFAULT_RELEASE_SCHEMA_CHANNEL = "release-151"

SCHEMA_LABELS: dict[str, str] = {
    "esr-140.11": "ESR 140.11",
    "release-151": "Release 151",
}

SCHEMA_FILENAMES: dict[str, str] = {
    "esr-140.11": "firefox-esr-140.11.json",
    "release-151": "firefox-release-151.json",
}

RAW_SCHEMA_DIRS: dict[str, str] = {
    "esr-140.11": "esr14011",
    "release-151": "release151",
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
