from __future__ import annotations

import socket
from dataclasses import replace
from pathlib import Path

from app.core.schema_channels import SCHEMA_FILENAMES, SCHEMA_SOURCES, SUPPORTED_SCHEMA_CHANNELS
from tools.convert_policies_from_upstream_lib.cli import generate_schema_targets
from tools.convert_policies_from_upstream_lib.common import load_schema_build_targets

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pinned_schema_targets_match_the_supported_runtime_matrix() -> None:
    targets = load_schema_build_targets()

    assert tuple(target.channel for target in targets) == (
        "release-153",
        "esr-153.0",
        "esr-140.13",
    )
    assert {target.channel for target in targets} == set(SUPPORTED_SCHEMA_CHANNELS)
    assert {target.channel: target.output.name for target in targets} == SCHEMA_FILENAMES
    assert {target.channel: target.source_tag for target in targets} == SCHEMA_SOURCES


def test_pinned_schema_conversion_is_offline_and_reproduces_all_bundles(
    tmp_path: Path, monkeypatch
) -> None:
    def _network_is_forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("Pinned schema conversion must not access the network")

    monkeypatch.setattr(socket, "create_connection", _network_is_forbidden)
    targets = tuple(
        replace(target, output=tmp_path / target.output.name)
        for target in load_schema_build_targets()
    )

    generate_schema_targets(targets)

    for target in targets:
        bundled = REPO_ROOT / "app" / "schemas" / "policies" / target.output.name
        assert target.output.read_bytes() == bundled.read_bytes()
