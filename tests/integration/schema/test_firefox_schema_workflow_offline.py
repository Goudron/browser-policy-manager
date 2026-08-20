from __future__ import annotations

import json
import socket
from dataclasses import replace
from pathlib import Path

from app.core.schema_channels import SCHEMA_FILENAMES, SCHEMA_SOURCES, SUPPORTED_SCHEMA_CHANNELS
from tools.convert_policies_from_upstream_lib.cli import generate_schema_targets
from tools.convert_policies_from_upstream_lib.common import load_schema_build_targets

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pinned_schema_targets_include_generated_esr115_before_runtime_wiring() -> None:
    targets = load_schema_build_targets()

    assert tuple(target.channel for target in targets) == (
        "release-153",
        "esr-153.0",
        "esr-140.13",
        "esr-115.39",
    )
    runtime_targets = tuple(
        target for target in targets if target.channel in SUPPORTED_SCHEMA_CHANNELS
    )
    assert {target.channel for target in runtime_targets} == set(SUPPORTED_SCHEMA_CHANNELS)
    assert {target.channel: target.output.name for target in runtime_targets} == SCHEMA_FILENAMES
    assert {target.channel: target.source_tag for target in runtime_targets} == SCHEMA_SOURCES

    esr115 = next(target for target in targets if target.channel == "esr-115.39")
    assert esr115.schema_metadata is not None
    assert esr115.schema_metadata["line_id"] == "esr-115"
    assert esr115.schema_metadata["firefox_line"] == 115
    assert esr115.schema_metadata["firefox_version"] == "115.39.0esr"


def test_pinned_schema_conversion_is_offline_and_reproduces_all_bundles(
    tmp_path: Path, monkeypatch
) -> None:
    def _network_is_forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("Pinned schema conversion must not access the network")

    monkeypatch.setattr(socket, "create_connection", _network_is_forbidden)
    first_targets = tuple(
        replace(target, output=tmp_path / "first" / target.output.name)
        for target in load_schema_build_targets()
    )
    second_targets = tuple(
        replace(target, output=tmp_path / "second" / target.output.name)
        for target in load_schema_build_targets()
    )

    generate_schema_targets(first_targets)
    generate_schema_targets(second_targets)

    for target, second_target in zip(first_targets, second_targets, strict=True):
        bundled = REPO_ROOT / "app" / "schemas" / "policies" / target.output.name
        assert target.output.read_bytes() == bundled.read_bytes()
        assert target.output.read_bytes() == second_target.output.read_bytes()

    esr115 = next(target for target in first_targets if target.channel == "esr-115.39")
    second_esr115 = next(target for target in second_targets if target.channel == "esr-115.39")
    generated = json.loads(esr115.output.read_text(encoding="utf-8"))
    assert generated["x-bpm-channel"] == "esr-115.39"
    assert generated["x-bpm-artifact-id"] == "esr-115.39"
    assert generated["x-bpm-line-id"] == "esr-115"
    assert generated["x-bpm-firefox-line"] == 115
    assert generated["x-bpm-firefox-version"] == "115.39.0esr"
    assert generated["x-bpm-source"] == "mozilla-policy-templates-v5.12"
    assert generated["x-bpm-ui-label"] == "ESR 115.39"
    assert generated["x-bpm-generator"] == {
        "identity": "bpm-firefox-policy-schema-converter/v1",
        "entrypoint": "tools/convert_policies_from_upstream.py",
    }
    assert (
        generated["x-bpm-source-provenance"]["inputs"]["policy-templates.md"]["sha256"]
        == "ce84a587dabc8e995e93206866e8d8ab3c9cf8423bb7dfbe74f20b9b28aaac42"
    )
    assert list(generated["properties"]) == list(
        json.loads(second_esr115.output.read_text(encoding="utf-8"))["properties"]
    )
    assert all(
        esr115.output.read_bytes() != target.output.read_bytes()
        for target in first_targets
        if target.channel != esr115.channel
    )


def test_esr115_nested_policy_completeness_and_channel_boundaries() -> None:
    schema = json.loads(
        (REPO_ROOT / "app" / "schemas" / "policies" / "firefox-esr-115.39.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(schema["properties"]) == 97
    assert schema["properties"]["DisplayMenuBar"]["enum"] == [
        "always",
        "never",
        "default-on",
        "default-off",
    ]
    assert schema["properties"]["OverrideFirstRunPage"]["default"] == "http://example.org"
    assert schema["properties"]["UseSystemPrintDialog"]["type"] == "boolean"
    extension_properties = schema["properties"]["ExtensionSettings"]["additionalProperties"][
        "properties"
    ]
    assert set(extension_properties) == {
        "allowed_types",
        "blocked_install_message",
        "default_area",
        "install_sources",
        "install_url",
        "installation_mode",
        "private_browsing",
        "restricted_domains",
        "temporarily_allow_weak_signatures",
        "update_url",
        "updates_disabled",
    }
    assert extension_properties["allowed_types"]["items"]["enum"] == [
        "extension",
        "theme",
        "dictionary",
        "locale",
        "sitepermission",
    ]
    assert "allowed_permissions" not in extension_properties
    assert {
        "AIControls",
        "AllowFileSelectionDialogs",
        "ContentAnalysis",
        "GenerativeAI",
    }.isdisjoint(schema["properties"])
