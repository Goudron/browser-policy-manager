from __future__ import annotations

import json

import pytest

from tools.convert_policies_from_upstream_lib.common import load_schema_build_targets
from tools.verify_firefox_schema_matrix import (
    EXPECTED_CHANNELS,
    REPORT_SCHEMA,
    FirefoxSchemaMatrixGateError,
    _assert_bundle_metadata,
    _load_json,
    run_fail_closed_mutation_checks,
    run_gate,
)


def test_four_channel_gate_emits_truthful_progress_and_deterministic_report(tmp_path) -> None:
    messages: list[str] = []
    first_report_path = tmp_path / "first.json"
    second_report_path = tmp_path / "second.json"

    first = run_gate(report_path=first_report_path, emit=messages.append)
    second = run_gate(report_path=second_report_path, emit=lambda _message: None)

    assert [entry["channel"] for entry in first["channels"]] == list(EXPECTED_CHANNELS)
    assert first == second
    assert json.loads(first_report_path.read_text(encoding="utf-8")) == first
    assert second_report_path.read_text(encoding="utf-8") == first_report_path.read_text(
        encoding="utf-8"
    )
    assert any("phase=preflight-input" in message and "[1/6]" in message for message in messages)
    for position, channel in enumerate(EXPECTED_CHANNELS, start=1):
        assert any(
            message.startswith(f"phase=channel-proof channel={channel} [{position}/4]")
            for message in messages
        )
    assert any(
        "phase=m3-05-audit" in message and "pair=esr-115.39->" in message for message in messages
    )
    assert messages[-1] == "phase=complete channel=matrix [4/4] status=passed"

    import jsonschema

    jsonschema.Draft202012Validator(REPORT_SCHEMA).validate(first)


def test_four_channel_gate_mutations_fail_closed() -> None:
    checks = run_fail_closed_mutation_checks(load_schema_build_targets())

    assert "manifest_source_tag_drift_rejected" in checks
    assert "pinned_input_hash_drift_rejected" in checks
    assert "retired_channel_rejected" in checks
    assert "unbundled_channel_rejected" in checks


def test_four_channel_gate_rejects_bundle_metadata_drift() -> None:
    target = next(item for item in load_schema_build_targets() if item.channel == "esr-115.39")
    bundle = _load_json(target.output)
    bundle["x-bpm-source"] = "drifted-source"

    with pytest.raises(FirefoxSchemaMatrixGateError, match="x-bpm-source"):
        _assert_bundle_metadata(target, bundle)
