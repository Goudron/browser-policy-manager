#!/usr/bin/env python3
"""Measure the stable pre-refactor profile-route and repository-health baseline.

Reports deliberately stay local (``artifacts/performance/`` is already ignored).
They describe the fixture and process state so M2-04 can make like-for-like gates
rather than treating a result from an arbitrary workstation as a regression.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "performance"
REPETITIONS_DEFAULT = 3
WARMUPS_DEFAULT = 1
ROUTE_BASELINE_093 = {
    "/profiles": {"wall_seconds": 5.639, "response_bytes": 228569},
    "/profiles/compare": {"wall_seconds": 5.350, "response_bytes": 302780},
    "/profiles/new": {"wall_seconds": 6.153, "response_bytes": 1311354},
    "/profiles/{id}/edit": {"wall_seconds": 5.638, "response_bytes": 1311875},
    "/profiles/{id}/settings": {"wall_seconds": 5.792, "response_bytes": 1360232},
    "/profiles/{id}/json": {"wall_seconds": 5.003, "response_bytes": 1125399},
}
ROUTE_PATHS = (
    ("/profiles", "/profiles"),
    ("/profiles/compare", "/profiles/compare"),
    ("/profiles/new", "/profiles/new"),
    ("/profiles/{id}/edit", "/profiles/{id}/edit"),
    ("/profiles/{id}/settings", "/profiles/{id}/settings"),
    ("/profiles/{id}/json", "/profiles/{id}/json"),
)
TEST_LAYERS = {
    "unit": ("tests/unit/profiles/test_profiles_core_unit.py",),
    "api": ("tests/integration/api/test_profiles_api.py",),
    "ui_contract": ("tests/contract/ui/profiles/test_semantic_characterization.py",),
}
FIXTURE_CONTRACT = {
    "storage": "fresh in-memory SQLite",
    "profiles": 1,
    "profile_name": "Performance baseline fixture",
    "profile_schema_version": "release-153",
    "profile_flags": {"DisableTelemetry": True},
}
OWNED_PREFIXES = ("app/", "tests/", "tools/", "documentation/tools/")


def progress(phase: str, detail: str) -> None:
    print(f"[{phase}] {detail}", flush=True)


def command_output(command: list[str], *, timeout: int = 180) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    return completed.returncode, completed.stdout


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_test_layer_integrity(paths: tuple[str, ...]) -> dict[str, Any]:
    """Record collected tests and source identity before timing a layer.

    A duration is not useful evidence if a layer was silently made smaller.  The
    source digests and collected node count let the M2-04 gate reject that kind
    of incomparable report while still leaving intentional test changes visible
    for reviewed budget-manifest updates.
    """
    command = [sys.executable, "-m", "pytest", "-q", "--collect-only", *paths]
    exit_code, output = command_output(command)
    if exit_code != 0:
        raise RuntimeError(f"test-layer collection failed (exit {exit_code})")
    collected_tests = sum(
        int(line.rsplit(":", maxsplit=1)[1].strip())
        for line in output.splitlines()
        if line.startswith("tests/") and ":" in line and line.rsplit(":", 1)[1].strip().isdigit()
    )
    if collected_tests < 1:
        raise RuntimeError("test-layer collection produced no counted tests")
    return {
        "collection_command": command,
        "collected_tests": collected_tests,
        "source_sha256": {path: sha256_file(REPO_ROOT / path) for path in paths},
    }


def git_output(*args: str) -> str:
    code, output = command_output(["git", *args], timeout=30)
    return output.strip() if code == 0 else f"unavailable (git exit {code})"


def _version_command(command: list[str]) -> str:
    code, output = command_output(command, timeout=30)
    return output.strip() if code == 0 else f"unavailable (exit {code})"


def environment_manifest() -> dict[str, Any]:
    return {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count(),
        "git_head": git_output("rev-parse", "HEAD"),
        "git_status_porcelain": git_output("status", "--porcelain"),
        "node_version": _version_command(["node", "--version"]),
        "pytest_version": _version_command([sys.executable, "-m", "pytest", "--version"]),
        "cache_state": {
            "python_bytecode": os.environ.get("PYTHONDONTWRITEBYTECODE") != "1",
            "pytest_cache_present": (REPO_ROOT / ".pytest_cache").exists(),
            "node_modules_present": (REPO_ROOT / "node_modules").exists(),
            "route_catalog_caches_reset": True,
        },
    }


class CountingSession:
    """Count ORM operation boundaries without changing application code."""

    def __init__(self, session: Any) -> None:
        self._session = session
        self.counts: Counter[str] = Counter()

    def reset(self) -> None:
        self.counts.clear()

    async def scalars(self, *args: Any, **kwargs: Any) -> Any:
        self.counts["scalars"] += 1
        return await self._session.scalars(*args, **kwargs)

    async def scalar(self, *args: Any, **kwargs: Any) -> Any:
        self.counts["scalar"] += 1
        return await self._session.scalar(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        self.counts["execute"] += 1
        return await self._session.execute(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


async def measure_routes(*, warmups: int, repetitions: int) -> dict[str, Any]:
    """Use a fresh in-memory fixture; warm-ups are excluded from medians."""
    from app.db import get_session
    from app.main import create_app
    from app.models.profile import Base, Profile
    from app.services import profile_service

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as async_session:
        profile = Profile(
            name="Performance baseline fixture",
            description="Fixed in-memory fixture for M2-03 only.",
            schema_version="release-153",
            flags={"DisableTelemetry": True},
            compliance=None,
        )
        async_session.add(profile)
        await async_session.commit()
        profile_id = profile.id
        counted_session = CountingSession(async_session)
        validation_count = 0
        original_validate = profile_service.validate_profile_payload_with_schema

        def counted_validate(*args: Any, **kwargs: Any) -> Any:
            nonlocal validation_count
            validation_count += 1
            return original_validate(*args, **kwargs)

        async def override_get_session():
            yield counted_session

        app = create_app()
        app.dependency_overrides[get_session] = override_get_session
        profile_service.validate_profile_payload_with_schema = counted_validate
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://benchmark"
            ) as client:
                measurements: dict[str, Any] = {}
                for baseline_name, route_template in ROUTE_PATHS:
                    path = route_template.replace("{id}", str(profile_id))
                    progress("routes", f"warm-up {baseline_name} ({warmups} request(s))")
                    for _ in range(warmups):
                        response = await client.get(path)
                        if response.status_code != 200:
                            raise RuntimeError(
                                f"warm-up {baseline_name} returned {response.status_code}"
                            )
                    samples: list[dict[str, Any]] = []
                    progress("routes", f"measure {baseline_name} ({repetitions} request(s))")
                    for index in range(repetitions):
                        counted_session.reset()
                        validation_count = 0
                        started = time.perf_counter()
                        response = await client.get(path)
                        elapsed = time.perf_counter() - started
                        if response.status_code != 200:
                            raise RuntimeError(
                                f"measurement {baseline_name} returned {response.status_code}"
                            )
                        samples.append(
                            {
                                "request": index + 1,
                                "wall_seconds": elapsed,
                                "response_bytes": len(response.content),
                                "query_operations": dict(counted_session.counts),
                                "validation_calls": validation_count,
                            }
                        )
                    times = [sample["wall_seconds"] for sample in samples]
                    sizes = [sample["response_bytes"] for sample in samples]
                    measurements[baseline_name] = {
                        "route_template": baseline_name,
                        "fixture_path": path,
                        "status": "ok",
                        "warmups_excluded": warmups,
                        "samples": samples,
                        "median_wall_seconds": statistics.median(times),
                        "median_response_bytes": statistics.median(sizes),
                        "baseline_093": ROUTE_BASELINE_093[baseline_name],
                    }
                return measurements
        finally:
            profile_service.validate_profile_payload_with_schema = original_validate
            app.dependency_overrides.clear()
            await async_session.close()
            await engine.dispose()


def tracked_owned_files() -> list[Path]:
    paths = git_output("ls-files").splitlines()
    return [REPO_ROOT / path for path in paths if path.startswith(OWNED_PREFIXES)]


def collect_sizes() -> dict[str, Any]:
    files = [path for path in tracked_owned_files() if path.is_file()]
    groups = {
        "application": [
            path for path in files if path.relative_to(REPO_ROOT).as_posix().startswith("app/")
        ],
        "profile_static": [
            path
            for path in files
            if path.relative_to(REPO_ROOT).as_posix().startswith("app/static/profiles")
        ],
        "tests": [
            path for path in files if path.relative_to(REPO_ROOT).as_posix().startswith("tests/")
        ],
        "tools": [
            path
            for path in files
            if path.relative_to(REPO_ROOT).as_posix().startswith(("tools/", "documentation/tools/"))
        ],
    }
    return {
        name: {"files": len(group), "bytes": sum(path.stat().st_size for path in group)}
        for name, group in groups.items()
    }


def complexity() -> dict[str, Any]:
    functions: list[dict[str, Any]] = []
    decision_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
        ast.IfExp,
        ast.Match,
    )
    for path in tracked_owned_files():
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except OSError, SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                score = 1 + sum(isinstance(child, decision_nodes) for child in ast.walk(node))
                functions.append(
                    {
                        "path": path.relative_to(REPO_ROOT).as_posix(),
                        "function": node.name,
                        "line": node.lineno,
                        "cyclomatic_estimate": score,
                    }
                )
    return {
        "method": "AST estimate: 1 plus if/for/async-for/while/except/if-expression/match nodes",
        "functions_over_10": sorted(
            (item for item in functions if item["cyclomatic_estimate"] > 10),
            key=lambda item: item["cyclomatic_estimate"],
            reverse=True,
        ),
        "max_cyclomatic_estimate": max(
            (item["cyclomatic_estimate"] for item in functions), default=0
        ),
    }


def package_footprint() -> dict[str, Any]:
    app_files = [path for path in (REPO_ROOT / "app").rglob("*") if path.is_file()]
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dependency_lines = [
        line.strip().strip('",')
        for line in pyproject.splitlines()
        if line.strip().startswith('"') and ">=" in line
    ]
    return {
        "application_source_files": len(app_files),
        "application_source_bytes": sum(path.stat().st_size for path in app_files),
        "declared_dependency_lines": dependency_lines,
        "note": "Source footprint only; clean wheel/install footprint is owned by BPM094-M10-03.",
    }


def measure_test_layers() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for layer, paths in TEST_LAYERS.items():
        integrity = collect_test_layer_integrity(paths)
        command = [sys.executable, "-m", "pytest", "-q", *paths]
        progress("tests", f"{layer}: {' '.join(command)}")
        started = time.perf_counter()
        exit_code, output = command_output(command)
        result[layer] = {
            "command": command,
            "wall_seconds": time.perf_counter() - started,
            "exit_code": exit_code,
            "terminal_output": output[-4000:],
            **integrity,
        }
        if exit_code != 0:
            raise RuntimeError(f"test layer {layer} failed (exit {exit_code})")
    return result


def human_summary(report: dict[str, Any]) -> str:
    lines = ["# BPM profile performance and repository-health report", "", "## Procedure"]
    procedure = report["procedure"]
    lines.extend(
        [
            f"- Fixture: {procedure['fixture']}",
            f"- Warm-up: {procedure['warmups']} per route (excluded).",
            f"- Samples: {procedure['repetitions']} per route; median reported.",
            f"- Cache: {procedure['cache_rule']}",
            f"- Failure: {procedure['failure_rule']}",
            "",
            "## Route measurements",
            "",
            "| Route | Median seconds | Bytes | 0.9.3 seconds | 0.9.3 bytes | Queries/sample | Validations/sample |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for route, value in report["routes"].items():
        sample = value["samples"][0]
        query_count = sum(sample["query_operations"].values())
        lines.append(
            "| {route} | {time:.6f} | {bytes} | {old_time:.3f} | {old_bytes} | {queries} | {validations} |".format(
                route=route,
                time=value["median_wall_seconds"],
                bytes=value["median_response_bytes"],
                old_time=value["baseline_093"]["wall_seconds"],
                old_bytes=value["baseline_093"]["response_bytes"],
                queries=query_count,
                validations=sample["validation_calls"],
            )
        )
    lines.extend(["", "## Test-layer durations", ""])
    for name, value in report["test_layers"].items():
        lines.append(f"- {name}: {value['wall_seconds']:.3f}s (exit {value['exit_code']})")
    lines.extend(["", "## Repository footprint", ""])
    for name, value in report["owned_sizes"].items():
        lines.append(f"- {name}: {value['files']} files, {value['bytes']} bytes")
    lines.append(
        f"- maximum AST cyclomatic estimate: {report['complexity']['max_cyclomatic_estimate']}"
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--warmups", type=int, default=WARMUPS_DEFAULT)
    parser.add_argument("--repetitions", type=int, default=REPETITIONS_DEFAULT)
    parser.add_argument("--skip-test-layers", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.warmups < 1 or args.repetitions < 1:
        raise SystemExit("--warmups and --repetitions must both be at least one")
    started = time.perf_counter()
    progress("manifest", "recording machine, process, git, and cache state")
    report: dict[str, Any] = {
        "schema_version": 1,
        "procedure": {
            "fixture": "fresh FastAPI app + one fixed profile in in-memory SQLite",
            "fixture_contract": FIXTURE_CONTRACT,
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "statistic": "median wall-clock response time",
            "cache_rule": (
                "catalog process caches are cold for this process; one route warm-up is excluded; filesystem/node/pytest cache state is recorded, not cleared"
            ),
            "failure_rule": (
                "a non-200 route response, failed measured test layer, subprocess failure, or report-write failure exits non-zero and no completed report is claimed"
            ),
            "baseline_source": "BPM094 backlog 0.9.3 same-machine in-memory single-request table",
        },
        "environment": environment_manifest(),
    }
    progress("routes", "building isolated in-memory fixture")
    report["routes"] = asyncio.run(
        measure_routes(warmups=args.warmups, repetitions=args.repetitions)
    )
    if args.skip_test_layers:
        progress("tests", "skipped by --skip-test-layers")
        report["test_layers"] = {}
    else:
        report["test_layers"] = measure_test_layers()
    progress(
        "repository", "measuring tracked owned sizes, complexity, and package source footprint"
    )
    report["owned_sizes"] = collect_sizes()
    report["complexity"] = complexity()
    report["package_footprint"] = package_footprint()
    report["elapsed_seconds"] = time.perf_counter() - started
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "profile-performance.json"
    markdown_path = args.output_dir / "profile-performance.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(human_summary(report), encoding="utf-8")
    progress("complete", f"JSON: {json_path}")
    progress("complete", f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
