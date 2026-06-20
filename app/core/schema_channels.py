from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchemaChannel:
    value: str
    label: str
    filename: str
    raw_dir: str
    mozilla_version: str
    family: str
    is_default: bool = False


SCHEMA_CHANNELS: tuple[SchemaChannel, ...] = (
    SchemaChannel(
        value="esr-140.12",
        label="ESR 140.12",
        filename="firefox-esr-140.12.json",
        raw_dir="esr14012",
        mozilla_version="140.12",
        family="esr",
        is_default=True,
    ),
    SchemaChannel(
        value="release-152",
        label="Release 152",
        filename="firefox-release-152.json",
        raw_dir="release152",
        mozilla_version="152.0",
        family="release",
    ),
)

SUPPORTED_SCHEMA_CHANNELS: tuple[str, ...] = tuple(channel.value for channel in SCHEMA_CHANNELS)
SUPPORTED_SCHEMA_CHANNEL_SET: frozenset[str] = frozenset(SUPPORTED_SCHEMA_CHANNELS)

DEFAULT_SCHEMA_CHANNEL = next(channel.value for channel in SCHEMA_CHANNELS if channel.is_default)
DEFAULT_RELEASE_SCHEMA_CHANNEL = next(
    channel.value for channel in SCHEMA_CHANNELS if channel.family == "release"
)
CURRENT_ESR_SCHEMA_CHANNEL = next(channel.value for channel in SCHEMA_CHANNELS if channel.family == "esr")
CURRENT_RELEASE_SCHEMA_CHANNEL = DEFAULT_RELEASE_SCHEMA_CHANNEL

SCHEMA_LABELS: dict[str, str] = {channel.value: channel.label for channel in SCHEMA_CHANNELS}
SCHEMA_FILENAMES: dict[str, str] = {channel.value: channel.filename for channel in SCHEMA_CHANNELS}
RAW_SCHEMA_DIRS: dict[str, str] = {channel.value: channel.raw_dir for channel in SCHEMA_CHANNELS}
SCHEMA_MOZILLA_VERSIONS: dict[str, str] = {
    channel.value: channel.mozilla_version for channel in SCHEMA_CHANNELS
}


def get_schema_channel(channel: str) -> SchemaChannel | None:
    return next((entry for entry in SCHEMA_CHANNELS if entry.value == channel), None)


def get_schema_label(channel: str) -> str:
    return SCHEMA_LABELS.get(channel, channel)


def build_schema_channels_catalog() -> dict[str, object]:
    return {
        "supported_channels": list(SUPPORTED_SCHEMA_CHANNELS),
        "default_channel": DEFAULT_SCHEMA_CHANNEL,
        "default_release_channel": DEFAULT_RELEASE_SCHEMA_CHANNEL,
        "default_label": get_schema_label(DEFAULT_SCHEMA_CHANNEL),
        "labels": dict(SCHEMA_LABELS),
        "filenames": dict(SCHEMA_FILENAMES),
        "mozilla_versions": dict(SCHEMA_MOZILLA_VERSIONS),
        "options": [
            {"value": channel, "label": get_schema_label(channel)}
            for channel in SUPPORTED_SCHEMA_CHANNELS
        ],
    }
