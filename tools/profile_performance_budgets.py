#!/usr/bin/env python3
"""Validate BPM 0.9.4 profile-performance reports against reviewed budgets.

The default mode produces a fresh report in a temporary directory before it
judges it.  ``--report`` is deliberately inspection-only: an arbitrary JSON
file cannot become release evidence.  Release targets are intentionally opt-in
until the later runtime and frontend optimization milestones make them true.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUDGET = REPO_ROOT / "tools" / "profile_performance_budgets_0_9_4.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "performance" / "gate"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def progress(phase: str, detail: str) -> None:
    print(f"[{phase}] {detail}", flush=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON from {path}: {error}") from error
    if not isinstance(result, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return result


def source_sha256(relative_path: str) -> str | None:
    path = REPO_ROOT / relative_path
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(violations: list[str], identifier: str, detail: str) -> None:
    violations.append(f"{identifier}: {detail}")


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_procedure(report: Mapping[str, Any], budget: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    procedure = report.get("procedure")
    if not isinstance(procedure, Mapping):
        return ["procedure: missing object"]
    for key, expected in budget["required_procedure"].items():
        if procedure.get(key) != expected:
            fail(
                violations, f"procedure.{key}", f"expected {expected!r}, got {procedure.get(key)!r}"
            )
    return violations


def check_routes(report: Mapping[str, Any], budget: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    routes = report.get("routes")
    expected_routes = budget["current_guardrail"]["routes"]
    if not isinstance(routes, Mapping):
        return ["routes: missing object"]
    if set(routes) != set(expected_routes):
        fail(
            violations,
            "routes",
            f"expected exactly {sorted(expected_routes)}, got {sorted(routes)}",
        )
        return violations
    repetitions = budget["required_procedure"]["repetitions"]
    for route, limits in expected_routes.items():
        value = routes[route]
        if not isinstance(value, Mapping):
            fail(violations, f"route {route}", "missing object")
            continue
        if value.get("status") != "ok" or value.get("route_template") != route:
            fail(
                violations,
                f"route {route}",
                "status or route template is not the required measurement",
            )
        if value.get("warmups_excluded") != budget["required_procedure"]["warmups"]:
            fail(violations, f"route {route}", "warm-up count is not comparable")
        samples = value.get("samples")
        if not isinstance(samples, list) or len(samples) != repetitions:
            fail(violations, f"route {route}", f"requires exactly {repetitions} measured samples")
            continue
        if [sample.get("request") for sample in samples if isinstance(sample, Mapping)] != list(
            range(1, repetitions + 1)
        ):
            fail(violations, f"route {route}", "sample request indexes are incomplete or reordered")
        times: list[float] = []
        sizes: list[int | float] = []
        for index, sample in enumerate(samples, start=1):
            if not isinstance(sample, Mapping):
                fail(violations, f"route {route} sample {index}", "not an object")
                continue
            elapsed = sample.get("wall_seconds")
            response_bytes = sample.get("response_bytes")
            if not numeric(elapsed) or elapsed <= 0:
                fail(violations, f"route {route} sample {index}", "invalid wall_seconds")
            else:
                times.append(float(elapsed))
            if not numeric(response_bytes) or response_bytes <= 0:
                fail(violations, f"route {route} sample {index}", "invalid response_bytes")
            else:
                sizes.append(response_bytes)
            query_operations = sample.get("query_operations")
            if not isinstance(query_operations, Mapping) or not all(
                isinstance(count, int) and count >= 0 for count in query_operations.values()
            ):
                fail(
                    violations, f"route {route} sample {index}", "invalid query operation counters"
                )
            elif sum(query_operations.values()) > limits["max_query_operations"]:
                fail(violations, f"route {route} sample {index}", "query-operation budget exceeded")
            validations = sample.get("validation_calls")
            if not isinstance(validations, int) or validations < 0:
                fail(violations, f"route {route} sample {index}", "invalid validation counter")
            elif validations > limits["max_validation_calls"]:
                fail(violations, f"route {route} sample {index}", "validation-call budget exceeded")
        actual_median = value.get("median_wall_seconds")
        if len(times) == repetitions and (
            not numeric(actual_median)
            or not math.isclose(actual_median, statistics.median(times), rel_tol=0, abs_tol=1e-9)
        ):
            fail(violations, f"route {route}", "reported time median does not equal samples")
        elif numeric(actual_median) and actual_median > limits["max_median_wall_seconds"]:
            fail(
                violations,
                f"route {route}",
                f"{actual_median:.3f}s exceeds {limits['max_median_wall_seconds']:.3f}s",
            )
        actual_size = value.get("median_response_bytes")
        if len(sizes) == repetitions and actual_size != statistics.median(sizes):
            fail(violations, f"route {route}", "reported byte median does not equal samples")
        elif numeric(actual_size) and actual_size > limits["max_median_response_bytes"]:
            fail(
                violations,
                f"route {route}",
                f"{actual_size} B exceeds {limits['max_median_response_bytes']} B",
            )
    return violations


def check_test_layers(report: Mapping[str, Any], budget: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    layers = report.get("test_layers")
    expected_layers = budget["current_guardrail"]["test_layers"]
    if not isinstance(layers, Mapping):
        return ["test_layers: missing object"]
    if set(layers) != set(expected_layers):
        return [f"test_layers: expected exactly {sorted(expected_layers)}, got {sorted(layers)}"]
    total_duration = 0.0
    for layer, limits in expected_layers.items():
        value = layers[layer]
        if not isinstance(value, Mapping):
            fail(violations, f"test layer {layer}", "missing object")
            continue
        if value.get("exit_code") != 0:
            fail(violations, f"test layer {layer}", "measured test command did not pass")
        collected = value.get("collected_tests")
        if not isinstance(collected, int) or collected < limits["minimum_collected_tests"]:
            fail(violations, f"test layer {layer}", "collected-test floor was reduced or omitted")
        report_hashes = value.get("source_sha256")
        if report_hashes != limits["source_sha256"]:
            fail(
                violations,
                f"test layer {layer}",
                "reported test-source identity differs from reviewed manifest",
            )
        for path, expected_hash in limits["source_sha256"].items():
            if source_sha256(path) != expected_hash:
                fail(
                    violations,
                    f"test layer {layer}",
                    f"current {path} differs from reviewed manifest",
                )
        duration = value.get("wall_seconds")
        if not numeric(duration) or duration <= 0:
            fail(violations, f"test layer {layer}", "invalid duration")
        else:
            total_duration += float(duration)
            if duration > limits["max_wall_seconds"]:
                fail(violations, f"test layer {layer}", "duration budget exceeded")
    if total_duration > budget["current_guardrail"]["max_selected_test_layer_seconds"]:
        fail(violations, "test layers", "combined duration budget exceeded")
    return violations


def check_repository(report: Mapping[str, Any], budget: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    guardrail = budget["current_guardrail"]
    owned_sizes = report.get("owned_sizes")
    if not isinstance(owned_sizes, Mapping):
        fail(violations, "owned_sizes", "missing object")
    else:
        for name, limits in guardrail["owned_sizes"].items():
            value = owned_sizes.get(name)
            if not isinstance(value, Mapping):
                fail(violations, f"owned_sizes.{name}", "missing object")
                continue
            for metric, limit in limits.items():
                actual = value.get(metric.removeprefix("max_"))
                if not isinstance(actual, int) or actual > limit:
                    fail(violations, f"owned_sizes.{name}", f"{metric} budget exceeded")
    footprint = report.get("package_footprint")
    if not isinstance(footprint, Mapping):
        fail(violations, "package_footprint", "missing object")
    else:
        for metric, limit in guardrail["package_footprint"].items():
            actual = footprint.get(metric.removeprefix("max_"))
            if not isinstance(actual, int) or actual > limit:
                fail(violations, "package_footprint", f"{metric} budget exceeded")
    complexity = report.get("complexity")
    if (
        not isinstance(complexity, Mapping)
        or complexity.get("max_cyclomatic_estimate", -1) > guardrail["max_cyclomatic_estimate"]
    ):
        fail(violations, "complexity", "maximum complexity budget exceeded or omitted")
    return violations


def configured_coverage_threshold(path: Path) -> int | None:
    match = re.search(
        r"^COVERAGE_FAIL_UNDER\s*\?=\s*(\d+)\s*$",
        path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    return int(match.group(1)) if match else None


def print_measurements(report: Mapping[str, Any]) -> None:
    for route, value in report["routes"].items():
        print(
            "[measurement] "
            f"{route}: {value['median_wall_seconds']:.3f}s, "
            f"{value['median_response_bytes']} B",
            flush=True,
        )
    for layer, value in report["test_layers"].items():
        print(
            "[measurement] "
            f"test {layer}: {value['wall_seconds']:.3f}s, "
            f"{value['collected_tests']} collected",
            flush=True,
        )


def check_coverage_policy(budget: Mapping[str, Any], *, release: bool) -> list[str]:
    policy = budget["coverage_policy"]
    threshold = configured_coverage_threshold(REPO_ROOT / policy["path"])
    required = policy["release_minimum_percent"] if release else policy["current_minimum_percent"]
    if threshold is None or threshold < required:
        return [f"coverage policy: configured {threshold!r}%, requires at least {required}%"]
    return []


def validate_report(
    report: Mapping[str, Any], budget: Mapping[str, Any], *, release: bool = False
) -> list[str]:
    violations: list[str] = []
    if report.get("schema_version") != budget["report_schema_version"]:
        fail(violations, "schema_version", "incompatible performance report")
    violations.extend(check_procedure(report, budget))
    violations.extend(check_routes(report, budget))
    violations.extend(check_test_layers(report, budget))
    violations.extend(check_repository(report, budget))
    violations.extend(check_coverage_policy(budget, release=release))
    if release:
        targets = budget["release_targets"]
        route_values = report["routes"]
        for route, value in route_values.items():
            if value["median_wall_seconds"] > targets["max_route_median_wall_seconds"]:
                fail(violations, f"release route {route}", "one-second median target exceeded")
            if value["median_response_bytes"] > targets["route_response_bytes"][route]:
                fail(violations, f"release route {route}", "response-byte target exceeded")
        if (
            sum(value["wall_seconds"] for value in report["test_layers"].values())
            > targets["max_selected_test_layer_seconds"]
        ):
            fail(violations, "release test layers", "90-second selected-layer target exceeded")
    return violations


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=Path, default=DEFAULT_BUDGET)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="ignored local directory for the newly generated authoritative report",
    )
    parser.add_argument(
        "--report", type=Path, help="inspect an existing report; not admissible release evidence"
    )
    parser.add_argument("--enforce-release-targets", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.report and args.enforce_release_targets:
        raise SystemExit(
            "--report cannot be used with --enforce-release-targets; run a fresh measurement"
        )
    budget = load_json(args.budget)
    if args.report:
        progress("gate", f"inspection-only report: {args.report}")
        report = load_json(args.report)
    else:
        from tools import profile_performance_harness as harness

        progress("gate", f"creating fresh comparable report in {args.output_dir}")
        if harness.main(["--output-dir", str(args.output_dir)]) != 0:
            return 1
        report = load_json(args.output_dir / "profile-performance.json")
    print_measurements(report)
    violations = validate_report(report, budget, release=args.enforce_release_targets)
    if violations:
        progress("gate", f"FAILED: {len(violations)} budget violation(s)")
        for violation in violations:
            print(f"  - {violation}", flush=True)
        return 1
    mode = "release targets" if args.enforce_release_targets else "current guardrail"
    progress("gate", f"PASSED: {mode}; actual measurements are in the generated report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
