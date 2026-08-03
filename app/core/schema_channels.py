from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchemaChannel:
    value: str
    label: str
    filename: str
    raw_dir: str
    mozilla_version: str
    source_tag: str
    family: str
    i18n_key: str
    is_default: bool = False


SCHEMA_CHANNELS: tuple[SchemaChannel, ...] = (
    SchemaChannel(
        value="esr-140.13",
        label="ESR 140.13",
        filename="firefox-esr-140.13.json",
        raw_dir="esr14013",
        mozilla_version="140.13",
        source_tag="mozilla-policy-templates-v7.12",
        family="esr",
        i18n_key="profiles.firefox_schema_esr_140_13",
        is_default=True,
    ),
    SchemaChannel(
        value="esr-153.0",
        label="ESR 153.0",
        filename="firefox-esr-153.0.json",
        raw_dir="esr1530",
        mozilla_version="153.0",
        source_tag="mozilla-policy-templates-v8.0",
        family="esr",
        i18n_key="profiles.firefox_schema_esr_153_0",
    ),
    SchemaChannel(
        value="release-153",
        label="Release 153",
        filename="firefox-release-153.json",
        raw_dir="release153",
        mozilla_version="153.0",
        source_tag="mozilla-policy-templates-v8.0",
        family="release",
        i18n_key="profiles.firefox_schema_release_153",
    ),
)

# The header presents the newest generally available schema first, followed by
# the supported ESR schemas from newest to oldest. Keep this product-facing
# order separate from the technical/default schema order above.
HEADER_SCHEMA_CHANNEL_VALUES: tuple[str, ...] = (
    "release-153",
    "esr-153.0",
    "esr-140.13",
)
HEADER_SCHEMA_CHANNELS: tuple[SchemaChannel, ...] = tuple(
    next(channel for channel in SCHEMA_CHANNELS if channel.value == value)
    for value in HEADER_SCHEMA_CHANNEL_VALUES
)

SUPPORTED_SCHEMA_CHANNELS: tuple[str, ...] = tuple(channel.value for channel in SCHEMA_CHANNELS)
SUPPORTED_SCHEMA_CHANNEL_SET: frozenset[str] = frozenset(SUPPORTED_SCHEMA_CHANNELS)

DEFAULT_SCHEMA_CHANNEL = next(channel.value for channel in SCHEMA_CHANNELS if channel.is_default)
DEFAULT_RELEASE_SCHEMA_CHANNEL = next(
    channel.value for channel in SCHEMA_CHANNELS if channel.family == "release"
)
SUPPORTED_ESR_SCHEMA_CHANNELS: tuple[str, ...] = tuple(
    channel.value for channel in SCHEMA_CHANNELS if channel.family == "esr"
)
# Compatibility alias for editor/default selection. Persistence migration must use its explicit map.
CURRENT_ESR_SCHEMA_CHANNEL = DEFAULT_SCHEMA_CHANNEL
CURRENT_RELEASE_SCHEMA_CHANNEL = DEFAULT_RELEASE_SCHEMA_CHANNEL

SCHEMA_LABELS: dict[str, str] = {channel.value: channel.label for channel in SCHEMA_CHANNELS}
SCHEMA_FILENAMES: dict[str, str] = {channel.value: channel.filename for channel in SCHEMA_CHANNELS}
RAW_SCHEMA_DIRS: dict[str, str] = {channel.value: channel.raw_dir for channel in SCHEMA_CHANNELS}
SCHEMA_MOZILLA_VERSIONS: dict[str, str] = {
    channel.value: channel.mozilla_version for channel in SCHEMA_CHANNELS
}
SCHEMA_SOURCES: dict[str, str] = {channel.value: channel.source_tag for channel in SCHEMA_CHANNELS}


def get_schema_channel(channel: str) -> SchemaChannel | None:
    return next((entry for entry in SCHEMA_CHANNELS if entry.value == channel), None)


def get_schema_label(channel: str) -> str:
    return SCHEMA_LABELS.get(channel, channel)


def build_schema_channels_catalog(
    *,
    label_overrides: Mapping[str, str] | None = None,
) -> dict[str, object]:
    labels = {
        channel.value: label_overrides.get(channel.value, channel.label)
        if label_overrides
        else channel.label
        for channel in SCHEMA_CHANNELS
    }
    return {
        "supported_channels": list(SUPPORTED_SCHEMA_CHANNELS),
        "default_channel": DEFAULT_SCHEMA_CHANNEL,
        "default_release_channel": DEFAULT_RELEASE_SCHEMA_CHANNEL,
        "esr_channels": list(SUPPORTED_ESR_SCHEMA_CHANNELS),
        "default_label": labels[DEFAULT_SCHEMA_CHANNEL],
        "labels": labels,
        "filenames": dict(SCHEMA_FILENAMES),
        "mozilla_versions": dict(SCHEMA_MOZILLA_VERSIONS),
        "sources": dict(SCHEMA_SOURCES),
        "options": [
            {
                "value": channel.value,
                "label": labels[channel.value],
                "i18n_key": channel.i18n_key,
            }
            for channel in SCHEMA_CHANNELS
        ],
    }
