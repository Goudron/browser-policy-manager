from __future__ import annotations

import json

from tools.verify_firefox_conversion_matrix import (
    EXPECTED_CHANNELS,
    EXPECTED_PAIR_COUNT,
    run_fail_closed_mutation_checks,
    run_gate,
)


def test_directed_conversion_matrix_gate_is_deterministic_value_free_and_bounded(tmp_path) -> None:
    messages: list[str] = []
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    first = run_gate(report_path=first_path, emit=messages.append)
    second = run_gate(report_path=second_path, emit=lambda _message: None)

    assert first == second
    assert json.loads(first_path.read_text(encoding="utf-8")) == first
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["channels"] == list(EXPECTED_CHANNELS)
    assert first["pair_count"] == EXPECTED_PAIR_COUNT == 12
    assert first["completed_pairs"] == EXPECTED_PAIR_COUNT
    assert first["production_transformations"] == {
        "count": 0,
        "disposition": "no-production-recipe-after-four-channel-diff-audit",
    }
    assert first["runtime_budget"] == {
        "schema_loader_misses": 4,
        "schema_loader_miss_budget": 4,
        "validator_cache_entries": 4,
        "validator_cache_entry_budget": 4,
        "disposable_database_setups": 1,
        "wall_clock_budget": "not-used",
    }
    assert [item["pair_id"] for item in first["api_preview_pairs"]] == [
        pair["pair_id"] for pair in first["pairs"]
    ]
    assert all(item["available"] is True for item in first["api_preview_pairs"])
    assert all(item["source_immutable"] is True for item in first["api_preview_pairs"])
    assert all(item["repeatable"] is True for item in first["api_preview_pairs"])
    assert messages[0] == "phase=planner pair=release-153->esr-153.0 [1/12]"
    assert messages[-1] == "phase=complete pair=matrix [12/12] status=passed"


def test_directed_conversion_matrix_gate_mutations_fail_closed(tmp_path) -> None:
    report = run_gate(report_path=tmp_path / "matrix.json", emit=lambda _message: None)

    assert run_fail_closed_mutation_checks(report) == (
        "missing_pair_rejected",
        "missing_scenario_rejected",
        "target_validation_skip_rejected",
        "source_mutation_rejected",
        "nondeterminism_rejected",
        "digest_drift_rejected",
        "registry_drift_rejected",
        "production_recipe_rejected",
    )
