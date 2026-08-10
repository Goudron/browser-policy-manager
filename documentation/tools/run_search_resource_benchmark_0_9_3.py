"""Run the BPM093 M3-04 resource and static-artifact operability benchmark.

The caller supplies the exact M3-03 artifacts.  This tool performs no download and writes all
measured output only to an explicitly supplied ignored report directory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from . import run_search_relevance_benchmark_0_9_3 as relevance
except ImportError:  # Direct execution keeps documentation/tools on sys.path.
    import run_search_relevance_benchmark_0_9_3 as relevance


def _tree_size(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_growth_documents(copies: int = 10) -> list[dict[str, Any]]:
    """Create a deterministic 10x synthetic documentation-growth fixture from the M3 corpus."""
    documents: list[dict[str, Any]] = []
    for copy_number in range(1, copies + 1):
        for source in relevance.build_compact_documents():
            document = copy.deepcopy(source)
            suffix = f"-growth-{copy_number:02d}"
            document["document_id"] = f"{source['document_id']}{suffix}"
            document["topic_id"] = f"{source['topic_id']}{suffix}"
            output_path = Path(source["source"]["output_path"])
            document["source"]["output_path"] = str(
                output_path.with_name(f"{output_path.stem}{suffix}{output_path.suffix}")
            )
            document["url"] = f"{source['url'].removesuffix('.html')}{suffix}.html"
            documents.append(document)
    return documents


def _percentile_95(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot calculate P95 of an empty measurement set")
    return sorted(values)[max(0, (len(values) * 95 + 99) // 100 - 1)]


def _pagefind_query_metrics(site_root: Path, work_dir: Path) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    cases = [
        relevance.QueryCase(
            query_id=f"{locale}-{attempt}",
            locale=locale,
            query="API-VAL-001",
            query_class="technical_identifier",
            expected_topic_id="admin-task-validate-firefox-policies-json",
            expected_no_result=False,
            disposition="answer",
            scored=True,
        )
        for locale in relevance._read_json(relevance.EVALUATION_CORPUS)["locales"]
        for attempt in range(35)
    ]
    by_locale: dict[str, list[relevance.QueryCase]] = {}
    for case in cases:
        by_locale.setdefault(case.locale, []).append(case)

    measurements: list[float] = []
    first_query_bytes: dict[str, int] = {}
    with relevance._StaticServer(site_root) as server:
        for locale, locale_cases in by_locale.items():
            input_path = work_dir / f"m3-04-pagefind-input-{locale}.json"
            output_path = work_dir / f"m3-04-pagefind-output-{locale}.json"
            input_path.write_text(
                json.dumps([case.__dict__ for case in locale_cases], sort_keys=True),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "--eval",
                    relevance.PAGEFIND_QUERY_CLIENT,
                    str(site_root),
                    server.origin,
                    locale,
                    str(input_path),
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode:
                raise relevance.BenchmarkError(
                    f"Pagefind resource query failed for {locale}: {completed.stderr.strip()}"
                )
            payload = relevance._read_json(output_path)
            if any(not item["url"].startswith(server.origin) for item in payload["fetches"]):
                raise relevance.BenchmarkError(
                    f"Pagefind resource query escaped loopback for {locale}"
                )
            first_query_bytes[locale] = payload["output"][0]["fetched_bytes"]
            measurements.extend(item["elapsed_ms"] for item in payload["output"][5:])
    return {
        "query": "API-VAL-001",
        "warmups_per_locale": 5,
        "measured_attempts_per_locale": 30,
        "measured_attempt_count": len(measurements),
        "first_query_bytes_by_locale": first_query_bytes,
        "median_ms": sorted(measurements)[len(measurements) // 2],
        "p95_ms": _percentile_95(measurements),
    }


def atomic_install_update_rollback(
    baseline_site: Path, growth_site: Path, install_root: Path
) -> dict[str, Any]:
    """Exercise clean install, atomic update, and rollback without touching BPM runtime paths."""
    active = install_root / "active"
    prior = install_root / "prior"
    install_root.mkdir(parents=True, exist_ok=True)

    def promote(source: Path, version: str) -> None:
        staged = install_root / f".{version}.staged"
        shutil.copytree(source, staged)
        (staged / "bpm093-install.json").write_text(
            json.dumps({"version": version, "tree_sha256": _tree_sha256(source)}, sort_keys=True),
            encoding="utf-8",
        )
        os_replace(staged, active)

    promote(baseline_site, "baseline")
    initial = json.loads((active / "bpm093-install.json").read_text(encoding="utf-8"))
    os_replace(active, prior)
    promote(growth_site, "growth")
    updated = json.loads((active / "bpm093-install.json").read_text(encoding="utf-8"))
    failed_update = install_root / "failed-growth"
    os_replace(active, failed_update)
    os_replace(prior, active)
    rolled_back = json.loads((active / "bpm093-install.json").read_text(encoding="utf-8"))
    shutil.rmtree(failed_update)
    return {
        "clean_install": initial["version"] == "baseline",
        "atomic_update": (
            updated["version"] == "growth" and initial["tree_sha256"] != updated["tree_sha256"]
        ),
        "rollback": rolled_back == initial,
    }


def os_replace(source: Path, destination: Path) -> None:
    source.replace(destination)


def run_benchmark(
    work_dir: Path,
    pagefind_package: Path,
    pagefind_linux_package: Path,
    meilisearch_binary: Path,
    output_dir: Path,
) -> dict[str, Any]:
    config = relevance._read_json(relevance.BENCHMARK_CONFIG)["artifacts"]
    relevance._validate_artifact(
        pagefind_package,
        config["pagefind"]["npm_package"],
        config["pagefind"]["npm_package_sha256"],
    )
    relevance._validate_artifact(
        pagefind_linux_package,
        config["pagefind"]["linux_x64_package"],
        config["pagefind"]["linux_x64_package_sha256"],
    )
    relevance._validate_artifact(
        meilisearch_binary,
        config["meilisearch_ce"]["linux_amd64_binary"],
        config["meilisearch_ce"]["linux_amd64_binary_sha256"],
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_documents = relevance.build_compact_documents()
    growth_documents = build_growth_documents()
    baseline_started = time.perf_counter()
    baseline_site = relevance._prepare_pagefind_site(
        work_dir / "baseline", pagefind_package, pagefind_linux_package, baseline_documents
    )
    baseline_index_seconds = time.perf_counter() - baseline_started
    growth_started = time.perf_counter()
    growth_site = relevance._prepare_pagefind_site(
        work_dir / "growth", pagefind_package, pagefind_linux_package, growth_documents
    )
    growth_index_seconds = time.perf_counter() - growth_started
    summary = {
        "schema_version": 1,
        "backlog_item": "BPM093-M3-04",
        "status": "measured-no-selection",
        "host": relevance._host_fingerprint(),
        "artifacts": {
            "pagefind": relevance._sha256(pagefind_package),
            "pagefind_linux_x64": relevance._sha256(pagefind_linux_package),
            "meilisearch_ce": relevance._sha256(meilisearch_binary),
        },
        "pagefind": {
            "baseline_document_count": len(baseline_documents),
            "growth_document_count": len(growth_documents),
            "baseline_index_seconds": baseline_index_seconds,
            "growth_index_seconds": growth_index_seconds,
            "baseline_site_bytes": _tree_size(baseline_site),
            "growth_site_bytes": _tree_size(growth_site),
            "query_metrics": _pagefind_query_metrics(baseline_site, work_dir / "queries"),
            "install_update_rollback": atomic_install_update_rollback(
                baseline_site, growth_site, work_dir / "installed"
            ),
        },
    }
    (output_dir / "bpm093-m3-04-search-resource.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--pagefind-package", type=Path, required=True)
    parser.add_argument("--pagefind-linux-package", type=Path, required=True)
    parser.add_argument("--meilisearch-binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_benchmark(
        args.work_dir,
        args.pagefind_package,
        args.pagefind_linux_package,
        args.meilisearch_binary,
        args.output_dir,
    )
    print(
        json.dumps({"status": summary["status"], "pagefind": summary["pagefind"]}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
