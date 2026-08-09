from __future__ import annotations

import copy

import pytest

from tools import profile_performance_budgets as budgets


def comparable_report() -> tuple[dict, dict]:
    budget = budgets.load_json(budgets.DEFAULT_BUDGET)
    routes = {}
    for route in budget["current_guardrail"]["routes"]:
        sample = {
            "request": 1,
            "wall_seconds": 0.1,
            "response_bytes": 10,
            "query_operations": {},
            "validation_calls": 0,
        }
        routes[route] = {
            "route_template": route,
            "fixture_path": route.replace("{id}", "1"),
            "status": "ok",
            "warmups_excluded": 1,
            "samples": [copy.deepcopy(sample) | {"request": request} for request in (1, 2, 3)],
            "median_wall_seconds": 0.1,
            "median_response_bytes": 10,
            "baseline_093": {},
        }
    layers = {
        name: {
            "exit_code": 0,
            "collected_tests": limit["minimum_collected_tests"],
            "source_sha256": limit["source_sha256"],
            "wall_seconds": 0.1,
        }
        for name, limit in budget["current_guardrail"]["test_layers"].items()
    }
    report = {
        "schema_version": 1,
        "procedure": budget["required_procedure"],
        "routes": routes,
        "test_layers": layers,
        "owned_sizes": {
            name: {"files": 0, "bytes": 0} for name in budget["current_guardrail"]["owned_sizes"]
        },
        "package_footprint": {"application_source_files": 0, "application_source_bytes": 0},
        "complexity": {"max_cyclomatic_estimate": 0},
    }
    return report, budget


def test_current_guardrail_accepts_complete_comparable_report():
    report, budget = comparable_report()

    assert budgets.validate_report(report, budget) == []


def test_guardrail_rejects_incomplete_or_fabricated_route_measurement():
    report, budget = comparable_report()
    del report["routes"]["/profiles/new"]
    report["routes"]["/profiles"]["median_wall_seconds"] = 999

    violations = budgets.validate_report(report, budget)

    assert any(violation.startswith("routes:") for violation in violations)


def test_guardrail_rejects_test_shrink_or_source_identity_change():
    report, budget = comparable_report()
    report["test_layers"]["unit"]["collected_tests"] = 0
    report["test_layers"]["api"]["source_sha256"] = {
        "tests/integration/api/test_profiles_api.py": "fake"
    }

    violations = budgets.validate_report(report, budget)

    assert any("collected-test floor" in violation for violation in violations)
    assert any("test-source identity" in violation for violation in violations)


def test_release_targets_report_both_runtime_and_coverage_gaps():
    report, budget = comparable_report()
    report["routes"]["/profiles"]["median_wall_seconds"] = 2.0
    budget["coverage_policy"]["release_minimum_percent"] = 101

    violations = budgets.validate_report(report, budget, release=True)

    assert any("coverage policy" in violation for violation in violations)
    assert any("one-second median target" in violation for violation in violations)


def test_external_report_cannot_enforce_release_targets():
    with pytest.raises(SystemExit, match="cannot be used"):
        budgets.main(["--report", "report.json", "--enforce-release-targets"])
