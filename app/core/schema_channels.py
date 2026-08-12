"""Runtime lifecycle catalog for bundled Firefox policy schemas.

The catalog deliberately owns lifecycle roles independently from declaration
order.  Persisted profile values are exact artifact IDs; stable line IDs only
identify lifecycle/recommendation/retirement relationships.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchemaChannelSource:
    """Pinned provenance and bundle identity for one schema artifact."""

    source_tag: str
    upstream_tag: str
    documentation_input_path: str
    documentation_input_url: str
    documentation_input_sha256: str
    linux_policies_input_path: str
    linux_policies_input_url: str
    linux_policies_input_sha256: str
    output_path: str
    filename: str


@dataclass(frozen=True, slots=True)
class SchemaChannel:
    """One exact browser-policy schema artifact and its lifecycle roles."""

    line_id: str
    artifact_id: str
    channel_id: str
    family: str
    line_number: int
    artifact_version: str
    label: str
    i18n_key: str
    support_state: str
    selectable: bool
    is_latest_esr: bool
    is_product_default: bool
    is_default_release: bool
    recommendation_target_line_id: str | None
    retirement_successor_line_id: str | None
    source: SchemaChannelSource

    # Compatibility accessors deliberately expose exact artifact facts, not a
    # singular "current ESR" semantic alias.
    @property
    def value(self) -> str:
        return self.artifact_id

    @property
    def filename(self) -> str:
        return self.source.filename

    @property
    def mozilla_version(self) -> str:
        return self.artifact_version

    @property
    def source_tag(self) -> str:
        return self.source.source_tag


def _source(
    *,
    source_tag: str,
    upstream_tag: str,
    documentation_input_path: str,
    documentation_input_url: str,
    documentation_input_sha256: str,
    linux_policies_input_path: str,
    linux_policies_input_url: str,
    linux_policies_input_sha256: str,
    output_path: str,
) -> SchemaChannelSource:
    return SchemaChannelSource(
        source_tag=source_tag,
        upstream_tag=upstream_tag,
        documentation_input_path=documentation_input_path,
        documentation_input_url=documentation_input_url,
        documentation_input_sha256=documentation_input_sha256,
        linux_policies_input_path=linux_policies_input_path,
        linux_policies_input_url=linux_policies_input_url,
        linux_policies_input_sha256=linux_policies_input_sha256,
        output_path=output_path,
        filename=output_path.rsplit("/", 1)[-1],
    )


_V8_SOURCE = _source(
    source_tag="mozilla-policy-templates-v8.0",
    upstream_tag="v8.0",
    documentation_input_path="data/upstream/policy-templates/v8.0/policy-templates.md",
    documentation_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v8.0/docs/index.md",
    documentation_input_sha256="2e00f3bf14ce2e90b96d9697700c493cc3688fb95aed2af49a000a5b62ef0bc1",
    linux_policies_input_path="data/upstream/policy-templates/v8.0/linux-policies.json",
    linux_policies_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v8.0/linux/policies.json",
    linux_policies_input_sha256="cadcd2052e4c449d68be760234c1eebc2916cb89319d9a4f1b71788504747fac",
    output_path="app/schemas/policies/firefox-release-153.json",
)
_V8_ESR_SOURCE = _source(
    source_tag="mozilla-policy-templates-v8.0",
    upstream_tag="v8.0",
    documentation_input_path="data/upstream/policy-templates/v8.0/policy-templates.md",
    documentation_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v8.0/docs/index.md",
    documentation_input_sha256="2e00f3bf14ce2e90b96d9697700c493cc3688fb95aed2af49a000a5b62ef0bc1",
    linux_policies_input_path="data/upstream/policy-templates/v8.0/linux-policies.json",
    linux_policies_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v8.0/linux/policies.json",
    linux_policies_input_sha256="cadcd2052e4c449d68be760234c1eebc2916cb89319d9a4f1b71788504747fac",
    output_path="app/schemas/policies/firefox-esr-153.0.json",
)
_V7_SOURCE = _source(
    source_tag="mozilla-policy-templates-v7.12",
    upstream_tag="v7.12",
    documentation_input_path="data/upstream/policy-templates/v7.12/policy-templates.md",
    documentation_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v7.12/docs/index.md",
    documentation_input_sha256="cebeacfdff92699c53d1fa7ab3b9db76fb2dae4362e3dd929165be1da79e265b",
    linux_policies_input_path="data/upstream/policy-templates/v7.12/linux-policies.json",
    linux_policies_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v7.12/linux/policies.json",
    linux_policies_input_sha256="5a180e55c6838e6d359ce2223e8e41294ab5ebde439347cf4c08bab459f39e5c",
    output_path="app/schemas/policies/firefox-esr-140.13.json",
)
_V5_SOURCE = _source(
    source_tag="mozilla-policy-templates-v5.12",
    upstream_tag="v5.12",
    documentation_input_path="data/upstream/policy-templates/v5.12/policy-templates.md",
    documentation_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v5.12/docs/index.md",
    documentation_input_sha256="ce84a587dabc8e995e93206866e8d8ab3c9cf8423bb7dfbe74f20b9b28aaac42",
    linux_policies_input_path="data/upstream/policy-templates/v5.12/linux-policies.json",
    linux_policies_input_url="https://raw.githubusercontent.com/mozilla/policy-templates/v5.12/linux/policies.json",
    linux_policies_input_sha256="da9caaefe75f7f5e54694bccda8a044e62f034dbd5889bcf1595bb08d6a04347",
    output_path="app/schemas/policies/firefox-esr-115.38.json",
)


# This declaration is intentionally not a product/API order.  All consumers
# receive sorted views through the helpers below, so an accidental reorder
# cannot change selector/header/default semantics.
SCHEMA_CHANNEL_CATALOG: tuple[SchemaChannel, ...] = (
    SchemaChannel(
        line_id="esr-115",
        artifact_id="esr-115.38",
        channel_id="esr-115.38",
        family="esr",
        line_number=115,
        artifact_version="115.38",
        label="ESR 115.38",
        i18n_key="profiles.firefox_schema_esr_115_38",
        support_state="supported",
        selectable=True,
        is_latest_esr=False,
        is_product_default=False,
        is_default_release=False,
        recommendation_target_line_id="esr-153",
        retirement_successor_line_id="esr-140",
        source=_V5_SOURCE,
    ),
    SchemaChannel(
        line_id="release-153",
        artifact_id="release-153",
        channel_id="release-153",
        family="release",
        line_number=153,
        artifact_version="153.0",
        label="Release 153",
        i18n_key="profiles.firefox_schema_release_153",
        support_state="supported",
        selectable=True,
        is_latest_esr=False,
        is_product_default=False,
        is_default_release=True,
        recommendation_target_line_id=None,
        retirement_successor_line_id=None,
        source=_V8_SOURCE,
    ),
    SchemaChannel(
        line_id="esr-140",
        artifact_id="esr-140.13",
        channel_id="esr-140.13",
        family="esr",
        line_number=140,
        artifact_version="140.13",
        label="ESR 140.13",
        i18n_key="profiles.firefox_schema_esr_140_13",
        support_state="supported",
        selectable=True,
        is_latest_esr=False,
        is_product_default=False,
        is_default_release=False,
        recommendation_target_line_id="esr-153",
        retirement_successor_line_id="esr-153",
        source=_V7_SOURCE,
    ),
    SchemaChannel(
        line_id="esr-153",
        artifact_id="esr-153.0",
        channel_id="esr-153.0",
        family="esr",
        line_number=153,
        artifact_version="153.0",
        label="ESR 153.0",
        i18n_key="profiles.firefox_schema_esr_153_0",
        support_state="supported",
        selectable=True,
        is_latest_esr=True,
        is_product_default=True,
        is_default_release=False,
        recommendation_target_line_id=None,
        retirement_successor_line_id=None,
        source=_V8_ESR_SOURCE,
    ),
)


def _artifact_version_key(channel: SchemaChannel) -> tuple[int, ...]:
    return tuple(int(part) for part in channel.artifact_version.split("."))


def ordered_schema_channels(
    channels: Iterable[SchemaChannel] | None = None,
) -> tuple[SchemaChannel, ...]:
    """Return public Release-first / descending ESR order independent of declaration."""
    family_rank = {"release": 0, "esr": 1}
    return tuple(
        sorted(
            SCHEMA_CHANNEL_CATALOG if channels is None else channels,
            key=lambda channel: (
                family_rank[channel.family],
                -channel.line_number,
                tuple(-part for part in _artifact_version_key(channel)),
                channel.artifact_id,
            ),
        )
    )


def supported_schema_channels(
    channels: Iterable[SchemaChannel] | None = None,
) -> tuple[SchemaChannel, ...]:
    return tuple(
        channel
        for channel in ordered_schema_channels(channels)
        if channel.support_state == "supported" and channel.selectable
    )


def retired_schema_channels(
    channels: Iterable[SchemaChannel] | None = None,
) -> tuple[SchemaChannel, ...]:
    """Return exact artifacts explicitly retired by the lifecycle catalog.

    This intentionally does not treat an unbundled or otherwise non-selectable
    supported artifact as a retirement. Only an explicit lifecycle retirement
    may require the offline Alembic successor migration.
    """
    return tuple(
        channel
        for channel in ordered_schema_channels(channels)
        if channel.support_state == "retired"
    )


def retired_schema_channel_artifact_ids(
    channels: Iterable[SchemaChannel] | None = None,
) -> tuple[str, ...]:
    """Return the persisted artifact IDs which require offline migration."""
    return tuple(channel.artifact_id for channel in retired_schema_channels(channels))


# Compatibility collection names are derived projections.  They are not an
# alternate catalog and must never be indexed as semantic ordering input.
SCHEMA_CHANNELS = supported_schema_channels()
SUPPORTED_SCHEMA_CHANNELS: tuple[str, ...] = tuple(
    channel.artifact_id for channel in SCHEMA_CHANNELS
)
SUPPORTED_SCHEMA_CHANNEL_SET: frozenset[str] = frozenset(SUPPORTED_SCHEMA_CHANNELS)
HEADER_SCHEMA_CHANNELS = SCHEMA_CHANNELS
HEADER_SCHEMA_CHANNEL_VALUES = SUPPORTED_SCHEMA_CHANNELS
SUPPORTED_ESR_SCHEMA_CHANNELS: tuple[str, ...] = tuple(
    channel.artifact_id for channel in SCHEMA_CHANNELS if channel.family == "esr"
)

DEFAULT_SCHEMA_CHANNEL = next(
    channel.artifact_id for channel in SCHEMA_CHANNELS if channel.is_product_default
)
DEFAULT_RELEASE_SCHEMA_CHANNEL = next(
    channel.artifact_id for channel in SCHEMA_CHANNELS if channel.is_default_release
)
LATEST_ESR_SCHEMA_CHANNEL = next(
    channel.artifact_id for channel in SCHEMA_CHANNELS if channel.is_latest_esr
)
CURRENT_RELEASE_SCHEMA_CHANNEL = DEFAULT_RELEASE_SCHEMA_CHANNEL

SCHEMA_LABELS: dict[str, str] = {channel.artifact_id: channel.label for channel in SCHEMA_CHANNELS}
SCHEMA_FILENAMES: dict[str, str] = {
    channel.artifact_id: channel.filename for channel in SCHEMA_CHANNELS
}
SCHEMA_MOZILLA_VERSIONS: dict[str, str] = {
    channel.artifact_id: channel.mozilla_version for channel in SCHEMA_CHANNELS
}
SCHEMA_SOURCES: dict[str, str] = {
    channel.artifact_id: channel.source_tag for channel in SCHEMA_CHANNELS
}


class SchemaChannelError(ValueError):
    code = "schema_channel_unknown"


class UnknownSchemaChannelError(SchemaChannelError):
    code = "schema_channel_unknown"


class RetiredSchemaChannelError(SchemaChannelError):
    code = "schema_channel_retired"


class UnbundledSchemaChannelError(SchemaChannelError):
    code = "schema_channel_unbundled"


def get_schema_channel(channel: str) -> SchemaChannel | None:
    return next((entry for entry in SCHEMA_CHANNEL_CATALOG if entry.artifact_id == channel), None)


def require_supported_schema_channel(channel: str) -> SchemaChannel:
    """Resolve an exact, currently selectable artifact or fail closed."""
    resolved = get_schema_channel(channel)
    if resolved is None:
        raise UnknownSchemaChannelError(f"Unknown schema channel '{channel}'")
    if resolved.support_state == "retired" or not resolved.selectable:
        raise RetiredSchemaChannelError(f"Schema channel '{channel}' is retired")
    if channel not in SCHEMA_FILENAMES:
        raise UnbundledSchemaChannelError(f"Schema channel '{channel}' is not bundled")
    return resolved


def get_schema_label(channel: str) -> str:
    return SCHEMA_LABELS.get(channel, channel)


def build_schema_channels_catalog(
    *,
    label_overrides: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Serialize the stable public catalog from lifecycle roles and sorted views."""
    channels = supported_schema_channels()
    by_line = {channel.line_id: channel for channel in channels}
    labels = {
        channel.artifact_id: (
            label_overrides.get(channel.artifact_id, channel.label)
            if label_overrides
            else channel.label
        )
        for channel in channels
    }

    def option(channel: SchemaChannel) -> dict[str, object]:
        target = (
            by_line[channel.recommendation_target_line_id].artifact_id
            if channel.recommendation_target_line_id is not None
            else None
        )
        return {
            "value": channel.artifact_id,
            "label": labels[channel.artifact_id],
            "i18n_key": channel.i18n_key,
            "line_id": channel.line_id,
            "artifact_id": channel.artifact_id,
            "family": channel.family,
            "support_state": channel.support_state,
            "selectable": channel.selectable,
            "is_latest_esr": channel.is_latest_esr,
            "is_product_default": channel.is_product_default,
            "is_default_release": channel.is_default_release,
            "recommendation_target": target,
        }

    ids = [channel.artifact_id for channel in channels]
    return {
        "catalog_version": 1,
        "supported_channels": ids,
        "default_channel": DEFAULT_SCHEMA_CHANNEL,
        "default_release_channel": DEFAULT_RELEASE_SCHEMA_CHANNEL,
        "latest_esr_channel": LATEST_ESR_SCHEMA_CHANNEL,
        "esr_channels": [channel.artifact_id for channel in channels if channel.family == "esr"],
        "selector_channels": ids,
        "header_channels": ids,
        "default_label": labels[DEFAULT_SCHEMA_CHANNEL],
        "labels": labels,
        "filenames": {channel.artifact_id: channel.filename for channel in channels},
        "mozilla_versions": {channel.artifact_id: channel.artifact_version for channel in channels},
        "sources": {channel.artifact_id: channel.source_tag for channel in channels},
        "options": [option(channel) for channel in channels],
    }
