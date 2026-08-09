"""Fail closed on the measured BPM 0.9.4 PDF pipeline optimization record."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "documentation/config/pdf-pipeline-optimization-benchmark-0.9.4.json"

pytestmark = pytest.mark.docs_contract


def _record() -> dict[str, object]:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_pdf_optimization_record_has_truthful_baseline_and_warm_medians() -> None:
    record = _record()

    assert record["schema_version"] == 1
    assert record["backlog_item"] == "BPM094-M11-10"
    assert record["target_bpm_version"] == "0.9.4"
    assert record["command"] == "make docs-pdf-build"
    assert record["measurement"]["sample_count"] == 3
    for name in ("baseline_full_rebuild", "optimized_unchanged_development_build"):
        measurement = record[name]
        samples = measurement["samples"]
        assert len(samples) == 3
        for field in ("wall_seconds", "cpu_seconds", "peak_rss_kib"):
            assert measurement["median"][field] == statistics.median(
                sample[field] for sample in samples
            )
        assert all(sample["pdf_count"] == 12 for sample in samples)
        assert all(sample["total_output_count"] == 13 for sample in samples)

    baseline = record["baseline_full_rebuild"]["median"]
    optimized = record["optimized_unchanged_development_build"]["median"]
    assert optimized["wall_seconds"] < baseline["wall_seconds"]
    assert optimized["cpu_seconds"] < baseline["cpu_seconds"]
    assert optimized["peak_rss_kib"] < baseline["peak_rss_kib"]


def test_pdf_optimization_record_preserves_fail_closed_cache_and_release_boundaries() -> None:
    record = _record()
    cache = record["cache_contract"]

    assert cache["unit"] == "locale-guide"
    assert cache["layers"] == ["dita-html5", "verified-pdf"]
    assert "transitive map/topic/key/local asset SHA-256" in cache["html_inputs"]
    assert "exact locale footer catalog and template SHA-256" in cache["pdf_inputs"]
    assert "complete binary PDF print contract" in cache["reuse_gate"]
    assert cache["invalid_entry"] == "quarantine and rebuild"
    assert "atomic promotion" in cache["promotion"]
    assert cache["independent_reproducibility"].startswith("cache bypass")

    cold = record["optimized_cold_prime"]
    assert cold["rebuilt_dita_pairs"] == 12
    assert cold["rebuilt_pdf_pairs"] == 12
    assert cold["pdf_count"] == 12
    assert cold["baseline_pdf_sha256_equivalence"] == "12 of 12 byte-identical"

    parallelism = record["parallelism_assessment"]
    assert parallelism["evaluated_max_workers"] == [1, 2]
    assert parallelism["selected_max_workers"] == 1
    assert parallelism["renderer"].startswith("chromium retained")
