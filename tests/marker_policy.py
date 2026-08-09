"""Fail-closed pytest taxonomy driven by explicit ownership metadata.

``tests/test-layer-ownership-0.9.4.json`` owns every primary execution layer.
Directory prefixes deliberately accept new tests below an established owner.
There is no root inventory or catch-all primary-layer default.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

PRIMARY_LAYERS = frozenset({"unit", "integration", "contract", "browser", "live"})
DOMAIN_MARKERS = frozenset({"api", "db", "schema", "ui", "docs", "compliance", "ai", "tooling"})
DURATION_MARKERS = frozenset({"slow"})
ENVIRONMENT_MARKERS = frozenset({"ai_incubation", "browser_ui", "firefox_live", "firefox_live_amo"})
COMPATIBILITY_MARKERS = frozenset({"docs_contract", "ui_contract"})
LAYER_MARKERS = (
    PRIMARY_LAYERS | DOMAIN_MARKERS | DURATION_MARKERS | ENVIRONMENT_MARKERS | COMPATIBILITY_MARKERS
)

OWNERSHIP_PATH = Path(__file__).with_name("test-layer-ownership-0.9.4.json")


class OwnershipPolicyError(ValueError):
    """Raised when a test path has no unique, valid ownership rule."""


@dataclass(frozen=True)
class OwnershipRule:
    identifier: str
    layer: str
    markers: frozenset[str]
    paths: frozenset[str]
    prefix: str | None

    def matches(self, path: str) -> bool:
        return path in self.paths or (self.prefix is not None and path.startswith(self.prefix))


@dataclass(frozen=True)
class MarkerOverride:
    """Orthogonal markers for exceptional tests below a directory owner."""

    identifier: str
    markers: frozenset[str]
    paths: frozenset[str]

    def matches(self, path: str) -> bool:
        return path in self.paths


def normalize_test_path(path: str | Path) -> str:
    """Normalise a repository-relative test path for metadata matching."""

    return Path(path).as_posix()


def _as_string_list(value: Any, *, owner: str, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise OwnershipPolicyError(
            f"owner {owner!r} must define a non-empty string list for {field}"
        )
    return tuple(value)


def parse_ownership_rules(payload: Mapping[str, Any]) -> tuple[OwnershipRule, ...]:
    """Validate and parse the repository-owned layer metadata.

    The parser is public so tests can prove malformed and overlapping metadata
    stops collection instead of silently reverting to a heuristic.
    """

    if payload.get("schema_version") != 1:
        raise OwnershipPolicyError("test-layer ownership metadata requires schema_version 1")
    entries = payload.get("owners")
    if not isinstance(entries, list) or not entries:
        raise OwnershipPolicyError("test-layer ownership metadata requires non-empty owners")

    rules: list[OwnershipRule] = []
    identifiers: set[str] = set()
    configured_paths: set[str] = set()
    for raw_entry in entries:
        if not isinstance(raw_entry, Mapping):
            raise OwnershipPolicyError("each test-layer owner must be an object")
        identifier = raw_entry.get("id")
        layer = raw_entry.get("layer")
        markers = raw_entry.get("markers")
        if not isinstance(identifier, str) or not identifier:
            raise OwnershipPolicyError("each test-layer owner requires a non-empty id")
        if identifier in identifiers:
            raise OwnershipPolicyError(f"duplicate test-layer owner id {identifier!r}")
        identifiers.add(identifier)
        if layer not in PRIMARY_LAYERS:
            raise OwnershipPolicyError(f"owner {identifier!r} has invalid primary layer {layer!r}")
        if not isinstance(markers, list) or not all(isinstance(marker, str) for marker in markers):
            raise OwnershipPolicyError(f"owner {identifier!r} must define a string list of markers")
        marker_set = frozenset(markers)
        unknown_markers = marker_set - LAYER_MARKERS
        invalid_primary_markers = marker_set & PRIMARY_LAYERS
        if unknown_markers or invalid_primary_markers:
            raise OwnershipPolicyError(
                f"owner {identifier!r} has invalid markers "
                f"{sorted(unknown_markers | invalid_primary_markers)}"
            )

        raw_paths = raw_entry.get("paths")
        prefix = raw_entry.get("prefix")
        if (raw_paths is None) == (prefix is None):
            raise OwnershipPolicyError(
                f"owner {identifier!r} must define exactly one of paths or prefix"
            )
        paths: frozenset[str]
        if raw_paths is not None:
            paths = frozenset(
                normalize_test_path(item)
                for item in _as_string_list(raw_paths, owner=identifier, field="paths")
            )
            if len(paths) != len(raw_paths):
                raise OwnershipPolicyError(f"owner {identifier!r} repeats an explicit test path")
            repeated_paths = configured_paths & paths
            if repeated_paths:
                raise OwnershipPolicyError(
                    f"test-layer ownership duplicates explicit path(s) {sorted(repeated_paths)}"
                )
            configured_paths.update(paths)
            rule_prefix = None
        else:
            if not isinstance(prefix, str) or not prefix.endswith("/"):
                raise OwnershipPolicyError(f"owner {identifier!r} prefix must end in '/'")
            paths = frozenset()
            rule_prefix = normalize_test_path(prefix)
            if not rule_prefix.endswith("/"):
                rule_prefix += "/"
        rules.append(OwnershipRule(identifier, layer, marker_set, paths, rule_prefix))

    for index, rule in enumerate(rules):
        for other in rules[index + 1 :]:
            prefixes = tuple(prefix for prefix in (rule.prefix, other.prefix) if prefix is not None)
            if len(prefixes) == 2 and (
                prefixes[0].startswith(prefixes[1]) or prefixes[1].startswith(prefixes[0])
            ):
                raise OwnershipPolicyError(
                    f"test-layer ownership prefixes overlap: {rule.identifier!r} and {other.identifier!r}"
                )
            for prefix, paths, owner in (
                (rule.prefix, other.paths, other.identifier),
                (other.prefix, rule.paths, rule.identifier),
            ):
                if prefix is not None and any(path.startswith(prefix) for path in paths):
                    raise OwnershipPolicyError(
                        f"test-layer ownership prefix {prefix!r} overlaps explicit paths of {owner!r}"
                    )
    return tuple(rules)


def parse_marker_overrides(
    payload: Mapping[str, Any], rules: tuple[OwnershipRule, ...]
) -> tuple[MarkerOverride, ...]:
    """Parse exceptional orthogonal markers without creating a second owner."""

    entries = payload.get("marker_overrides", [])
    if not isinstance(entries, list):
        raise OwnershipPolicyError("test-layer marker_overrides must be a list")

    overrides: list[MarkerOverride] = []
    identifiers: set[str] = set()
    configured_paths: set[str] = set()
    for raw_entry in entries:
        if not isinstance(raw_entry, Mapping):
            raise OwnershipPolicyError("each marker override must be an object")
        identifier = raw_entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise OwnershipPolicyError("each marker override requires a non-empty id")
        if identifier in identifiers:
            raise OwnershipPolicyError(f"duplicate marker override id {identifier!r}")
        identifiers.add(identifier)

        paths = frozenset(
            normalize_test_path(item)
            for item in _as_string_list(raw_entry.get("paths"), owner=identifier, field="paths")
        )
        if len(paths) != len(raw_entry["paths"]):
            raise OwnershipPolicyError(f"marker override {identifier!r} repeats a test path")
        repeated_paths = configured_paths & paths
        if repeated_paths:
            raise OwnershipPolicyError(
                f"marker overrides duplicate test path(s) {sorted(repeated_paths)}"
            )
        configured_paths.update(paths)

        raw_markers = raw_entry.get("markers")
        if (
            not isinstance(raw_markers, list)
            or not raw_markers
            or not all(isinstance(marker, str) for marker in raw_markers)
        ):
            raise OwnershipPolicyError(
                f"marker override {identifier!r} must define a non-empty string list of markers"
            )
        markers = frozenset(raw_markers)
        invalid_markers = (markers - LAYER_MARKERS) | (markers & PRIMARY_LAYERS)
        if invalid_markers:
            raise OwnershipPolicyError(
                f"marker override {identifier!r} has invalid markers {sorted(invalid_markers)}"
            )

        for path in paths:
            owners = tuple(rule for rule in rules if rule.matches(path))
            if len(owners) != 1:
                raise OwnershipPolicyError(
                    f"marker override {identifier!r} requires exactly one owner for {path!r}"
                )
        overrides.append(MarkerOverride(identifier, markers, paths))
    return tuple(overrides)


@cache
def ownership_metadata() -> Mapping[str, Any]:
    """Load the versioned ownership document once per pytest process."""

    try:
        payload = json.loads(OWNERSHIP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OwnershipPolicyError(f"cannot load test-layer ownership metadata: {error}") from error
    if not isinstance(payload, Mapping):
        raise OwnershipPolicyError("test-layer ownership metadata root must be an object")
    return payload


@cache
def ownership_rules() -> tuple[OwnershipRule, ...]:
    """Load the versioned ownership configuration once per pytest process."""

    return parse_ownership_rules(ownership_metadata())


@cache
def marker_overrides() -> tuple[MarkerOverride, ...]:
    """Load exceptional non-primary markers once per pytest process."""

    return parse_marker_overrides(ownership_metadata(), ownership_rules())


def ownership_for_path(path: str | Path) -> OwnershipRule:
    """Return exactly one owner for ``path`` or raise a collection-stopping error."""

    normalized = normalize_test_path(path)
    matches = tuple(rule for rule in ownership_rules() if rule.matches(normalized))
    if not matches:
        raise OwnershipPolicyError(
            f"unowned test path {normalized!r}; add it below an owned directory or to "
            f"{OWNERSHIP_PATH.as_posix()}"
        )
    if len(matches) != 1:
        raise OwnershipPolicyError(
            f"test path {normalized!r} has duplicate owners {[rule.identifier for rule in matches]}"
        )
    return matches[0]


def primary_layer_for_path(path: str | Path) -> str:
    """Return the sole execution layer owned by a test path."""

    return ownership_for_path(path).layer


def markers_for_path(path: str | Path) -> set[str]:
    """Return declared primary and orthogonal markers without inference."""

    normalized = normalize_test_path(path)
    owner = ownership_for_path(path)
    override_markers = {
        marker
        for override in marker_overrides()
        if override.matches(normalized)
        for marker in override.markers
    }
    return {owner.layer, *owner.markers, *override_markers}


def primary_markers(markers: Iterable[str]) -> set[str]:
    """Extract primary execution layers from marker names."""

    return set(markers) & PRIMARY_LAYERS


def _test_files_for_rule(rule: OwnershipRule) -> tuple[str, ...]:
    """Return materialized test modules for one explicit or directory owner."""

    if rule.prefix is None:
        return tuple(sorted(rule.paths))
    project_root = OWNERSHIP_PATH.parent.parent
    directory = project_root / rule.prefix
    return tuple(
        path.relative_to(project_root).as_posix() for path in sorted(directory.rglob("test_*.py"))
    )


AI_INCUBATION_TEST_FILES = frozenset(
    path
    for rule in ownership_rules()
    if "ai_incubation" in rule.markers
    for path in _test_files_for_rule(rule)
)
