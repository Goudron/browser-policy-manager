#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWN_ARTIFACT_PATHS = (
    ".bpm-test-browsers",
    ".coverage",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "artifacts",
    "browser_policy_manager.egg-info",
    "coverage.xml",
    "data",
    "docs/screenshots",
    "htmlcov",
    "tmp-bootstrap.db",
)
WATCH_DIRS = (
    "app",
    "app/static",
    "app/static/vendor",
    "app/i18n",
    "docs",
    "tests",
    "tools",
)
VENDOR_OR_GENERATED_PREFIXES = (
    "app/static/vendor/",
    "app/schemas/policies/",
    "app/compliance/firefox/cis/generated/",
)
PYTEST_BASELINE = {
    "command": "pytest --durations=25 --durations-min=0.05",
    "result": "583 passed, 53 deselected",
    "test_time": "803.15s",
    "wall_time": "807.50s",
    "recorded": "2026-06-01",
}


@dataclass(frozen=True)
class FileStats:
    path: str
    size: int
    lines: int


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True)


def human_size(size: int) -> str:
    value = float(size)
    for suffix in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or suffix == "GiB":
            if suffix == "B":
                return f"{int(value)} {suffix}"
            return f"{value:.1f} {suffix}"
        value /= 1024
    return f"{size} B"


def path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    if path.is_dir():
        for root, dirs, files in os.walk(path):
            dirs[:] = [name for name in dirs if name not in {".git", "__pycache__"}]
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                try:
                    total += file_path.stat().st_size
                except OSError:
                    continue
    return total


def tracked_files() -> list[Path]:
    output = run_git(["ls-files"])
    return [REPO_ROOT / line for line in output.splitlines() if line]


def line_count(path: Path) -> int:
    try:
        with path.open("rb") as file_obj:
            return sum(1 for _ in file_obj)
    except OSError:
        return 0


def collect_file_stats(files: list[Path]) -> list[FileStats]:
    stats: list[FileStats] = []
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        stats.append(
            FileStats(
                path=path.relative_to(REPO_ROOT).as_posix(),
                size=size,
                lines=line_count(path),
            )
        )
    return stats


def print_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> None:
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        print("| " + " | ".join(str(value) for value in row) + " |")


def report_top_files(stats: list[FileStats], limit: int) -> None:
    print("## Largest Tracked Files By Size")
    print_table(
        ("Path", "Size", "Lines"),
        [(item.path, human_size(item.size), item.lines) for item in sorted(stats, key=lambda item: item.size, reverse=True)[:limit]],
    )
    print()

    print("## Largest Tracked Files By Lines")
    print_table(
        ("Path", "Lines", "Size"),
        [(item.path, item.lines, human_size(item.size)) for item in sorted(stats, key=lambda item: item.lines, reverse=True)[:limit]],
    )
    print()


def report_directory_sizes() -> None:
    print("## Watched Directory Sizes")
    rows = []
    for relative in WATCH_DIRS:
        path = REPO_ROOT / relative
        if path.exists():
            rows.append((relative, human_size(path_size(path))))
    print_table(("Path", "Size"), rows)
    print()


def report_vendor_generated(files: list[Path]) -> None:
    print("## Vendor And Generated Tracked Files")
    rows = []
    for prefix in VENDOR_OR_GENERATED_PREFIXES:
        matching = [
            path
            for path in files
            if path.relative_to(REPO_ROOT).as_posix().startswith(prefix)
        ]
        rows.append((prefix.rstrip("/"), len(matching), human_size(sum(path.stat().st_size for path in matching))))
    print_table(("Prefix", "Files", "Size"), rows)
    print()


def report_ignored_artifacts() -> None:
    print("## Ignored Local Artifacts")
    rows = []
    ignored = set()
    status_output = run_git(["status", "--ignored", "--short", *KNOWN_ARTIFACT_PATHS])
    for line in status_output.splitlines():
        if line.startswith("!! "):
            ignored.add(line[3:].rstrip("/"))
    for relative in KNOWN_ARTIFACT_PATHS:
        path = REPO_ROOT / relative
        if path.exists():
            state = "ignored" if relative in ignored or f"{relative}/" in ignored else "present"
            rows.append((relative, state, human_size(path_size(path))))
    if not rows:
        rows.append(("(none)", "-", "-"))
    print_table(("Path", "State", "Size"), rows)
    print()


def report_locale_catalogs() -> None:
    print("## Locale Catalogs")
    rows = []
    for path in sorted((REPO_ROOT / "app" / "i18n").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        values = [value for value in data.values() if isinstance(value, str)]
        rows.append(
            (
                path.name,
                len(data),
                sum(len(value) for value in values),
                human_size(path.stat().st_size),
            )
        )
    print_table(("Catalog", "Keys", "String chars", "Size"), rows)
    print()


def report_file_mix(files: list[Path]) -> None:
    print("## Tracked File Mix")
    top_levels = Counter(path.relative_to(REPO_ROOT).parts[0] for path in files)
    extensions = Counter(path.suffix or "[none]" for path in files)
    print_table(("Top-level path", "Files"), sorted(top_levels.items(), key=lambda item: (-item[1], item[0])))
    print()
    print_table(("Extension", "Files"), sorted(extensions.items(), key=lambda item: (-item[1], item[0]))[:15])
    print()


def collect_default_pytest_count() -> str:
    try:
        output = subprocess.check_output(
            [".venv/bin/pytest" if (REPO_ROOT / ".venv/bin/pytest").exists() else "pytest", "--collect-only", "-q"],
            cwd=REPO_ROOT,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return f"unavailable ({exc.__class__.__name__})"
    total = 0
    for line in output.splitlines():
        if ": " not in line:
            continue
        _, _, count_text = line.rpartition(": ")
        try:
            total += int(count_text)
        except ValueError:
            continue
    return str(total) if total else "unavailable"


def report_test_timing(skip_collect: bool) -> None:
    print("## Test Timing")
    rows = [
        ("Recorded default baseline", PYTEST_BASELINE["command"]),
        ("Recorded result", PYTEST_BASELINE["result"]),
        ("Recorded test time", PYTEST_BASELINE["test_time"]),
        ("Recorded wall time", PYTEST_BASELINE["wall_time"]),
        ("Recorded date", PYTEST_BASELINE["recorded"]),
    ]
    if not skip_collect:
        rows.append(("Current default collect count", collect_default_pytest_count()))
    rows.append(("Full timing command", "pytest --durations=25 --durations-min=0.05"))
    print_table(("Metric", "Value"), rows)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a compact repository health report.")
    parser.add_argument("--top", type=int, default=15, help="Number of largest files to show.")
    parser.add_argument(
        "--skip-pytest-collect",
        action="store_true",
        help="Skip pytest collection when a very fast report is needed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = tracked_files()
    stats = collect_file_stats(files)
    print("# Browser Policy Manager Repo Health Report")
    print()
    report_file_mix(files)
    report_directory_sizes()
    report_top_files(stats, args.top)
    report_vendor_generated(files)
    report_locale_catalogs()
    report_ignored_artifacts()
    report_test_timing(skip_collect=args.skip_pytest_collect)


if __name__ == "__main__":
    main()
