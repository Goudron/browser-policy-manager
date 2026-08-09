from __future__ import annotations

from tools import profile_performance_harness as harness


def test_human_summary_includes_reproducibility_rules_and_baseline():
    report = {
        "procedure": {
            "fixture": "fixed fixture",
            "warmups": 1,
            "repetitions": 3,
            "cache_rule": "recorded",
            "failure_rule": "non-zero",
        },
        "routes": {
            "/profiles": {
                "median_wall_seconds": 0.2,
                "median_response_bytes": 12,
                "baseline_093": {"wall_seconds": 5.639, "response_bytes": 228569},
                "samples": [{"query_operations": {"scalars": 1}, "validation_calls": 1}],
            }
        },
        "test_layers": {"unit": {"wall_seconds": 0.1, "exit_code": 0}},
        "owned_sizes": {"application": {"files": 1, "bytes": 2}},
        "complexity": {"max_cyclomatic_estimate": 3},
    }

    summary = harness.human_summary(report)

    assert "Warm-up: 1" in summary
    assert "0.9.3 seconds" in summary
    assert "Queries/sample" in summary
    assert "maximum AST cyclomatic estimate: 3" in summary


def test_parse_args_accepts_measurement_counts():
    assert harness.parse_args(["--warmups", "1", "--repetitions", "2"]).repetitions == 2
