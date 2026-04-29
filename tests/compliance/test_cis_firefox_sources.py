from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.compliance.firefox.cis.validation import (
    BASE_DIR,
    ValidationResult,
    build_coverage_report,
    find_benchmark,
    format_coverage_markdown,
    format_validation_summary,
    load_benchmarks,
    load_yaml_file,
    validate_sources,
)


def test_cis_firefox_sources_validate_current_dataset() -> None:
    result = validate_sources()

    assert result.ok, result.errors
    assert result.summary["benchmark_count"] == 1
    assert result.summary["benchmarks"][0]["id"] == "cis-firefox-esr-gpo"
    assert result.summary["benchmarks"][0]["official_source_status"] == "imported"
    assert result.summary["benchmarks"][0]["recommendations"] == 55
    assert result.summary["benchmarks"][0]["mappings"] == 55
    assert result.warnings == ()


def test_cis_coverage_report_counts_current_dataset() -> None:
    report = build_coverage_report()

    assert report["ok"] is True
    benchmark = report["benchmarks"][0]
    assert benchmark["benchmark_id"] == "cis-firefox-esr-gpo"
    assert benchmark["total_recommendations"] == 55
    assert benchmark["total_mappings"] == 55
    assert benchmark["by_recommendation_status"] == {
        "deprecated_or_removed": 1,
        "mapped": 43,
        "needs_research": 1,
        "preference_mapped": 10,
    }
    assert benchmark["by_mapping_status"] == {
        "deprecated_or_removed": 1,
        "mapped": 43,
        "needs_research": 1,
        "preference_mapped": 10,
    }
    assert benchmark["by_level"] == {"L1": 51, "L2": 4}
    assert benchmark["schema_compatibility"] == {
        "esr-140.10:valid": 53,
        "release-150:valid": 53,
    }


def test_cis_sources_have_expected_files() -> None:
    expected_files = {
        "README.md",
        "sources.yaml",
        "firefox_esr_gpo_1_0_0.yaml",
        "mappings.yaml",
        "schema.yaml",
    }

    assert expected_files <= {path.name for path in BASE_DIR.iterdir()}


def test_cis_source_helpers_handle_empty_ambiguous_and_missing_sources(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert load_yaml_file(empty) == {}

    _write_yaml(tmp_path / "sources.yaml", {"benchmarks": [{"id": "single"}]})
    assert find_benchmark("single", base_dir=tmp_path) == {"id": "single"}

    _write_yaml(tmp_path / "sources.yaml", {"benchmarks": {"not": "a-list"}})
    assert load_benchmarks(tmp_path) == []
    assert find_benchmark("missing", base_dir=tmp_path) is None

    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                {"id": "bench", "upstream_version": "1.0.0"},
                {"id": "bench", "upstream_version": "2.0.0", "is_default": True},
            ]
        },
    )

    assert find_benchmark("bench", base_dir=tmp_path)["upstream_version"] == "2.0.0"
    assert find_benchmark("bench", upstream_version="1.0.0", base_dir=tmp_path)[
        "upstream_version"
    ] == "1.0.0"
    assert find_benchmark("bench", upstream_version="3.0.0", base_dir=tmp_path) is None


def test_cis_validator_rejects_non_list_benchmarks(tmp_path: Path) -> None:
    _write_yaml(tmp_path / "sources.yaml", {"benchmarks": {"bad": "shape"}})

    result = validate_sources(tmp_path)

    assert not result.ok
    assert "sources.yaml: benchmarks must be a list" in result.errors


def test_cis_validator_rejects_duplicate_recommendation_ids(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        recommendations=[
            _recommendation("1.1.1"),
            _recommendation("1.1.1"),
        ],
        mappings=[
            _mapping("1.1.1"),
        ],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("duplicate recommendation id '1.1.1'" in error for error in result.errors)


def test_cis_validator_rejects_invalid_status_and_level(tmp_path: Path) -> None:
    bad = _recommendation("1.1.1")
    bad["level"] = 3
    bad["mapping_status"] = "surprisingly_secure"
    _write_fixture(
        tmp_path,
        recommendations=[bad],
        mappings=[
            _mapping("1.1.1", status="surprisingly_secure"),
        ],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("level must be 1 or 2" in error for error in result.errors)
    assert any("unknown mapping_status 'surprisingly_secure'" in error for error in result.errors)
    assert any("unknown status 'surprisingly_secure'" in error for error in result.errors)


def test_cis_validator_rejects_mapping_to_unknown_recommendation(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        recommendations=[_recommendation("1.1.1")],
        mappings=[
            _mapping("1.1.1"),
            _mapping("1.1.2"),
        ],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("unknown recommendation_id '1.1.2'" in error for error in result.errors)


def test_cis_validator_rejects_missing_mapping_entry(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        recommendations=[
            _recommendation("1.1.1"),
            _recommendation("1.1.2"),
        ],
        mappings=[
            _mapping("1.1.1"),
        ],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("missing mapping for recommendation '1.1.2'" in error for error in result.errors)


def test_cis_validator_rejects_invalid_policy_target_path(tmp_path: Path) -> None:
    mapping = _mapping("1.1.1")
    mapping["targets"][0]["path"] = []
    _write_fixture(
        tmp_path,
        recommendations=[_recommendation("1.1.1")],
        mappings=[mapping],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("policy target path must be a non-empty string list" in error for error in result.errors)


def test_cis_validator_reports_source_shape_and_empty_recommendations(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                "bad",
                {
                    "id": "cis-firefox-esr-gpo",
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "benchmark_page_url": "not-a-url",
                    "public_versions_page_url": "",
                    "release_window": "2024-07",
                    "official_source_status": "pending",
                    "source_file": "missing-source.yaml",
                    "mapping_file": "missing-mapping.yaml",
                },
            ]
        },
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("benchmark entry must be an object" in error for error in result.errors)
    assert any("missing required field 'public_versions_page_url'" in error for error in result.errors)
    assert any("field 'benchmark_page_url' must be an HTTP(S) URL" in error for error in result.errors)
    assert any("file does not exist" in error for error in result.errors)
    assert any("recommendation list is empty while official CIS PDF curation is pending" in warning for warning in result.warnings)


def test_cis_validator_warns_on_empty_imported_recommendations(tmp_path: Path) -> None:
    _write_fixture(tmp_path, recommendations=[], mappings=[])

    result = validate_sources(tmp_path)

    assert result.ok
    assert "firefox_esr_gpo_1_0_0.yaml: recommendation list is empty" in result.warnings


def test_cis_validator_reports_duplicate_benchmark_ids(tmp_path: Path) -> None:
    _write_fixture(tmp_path, recommendations=[], mappings=[])
    sources = load_yaml_file(tmp_path / "sources.yaml")
    sources["benchmarks"].append(dict(sources["benchmarks"][0]))
    _write_yaml(tmp_path / "sources.yaml", sources)

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("duplicate benchmark id 'cis-firefox-esr-gpo'" in error for error in result.errors)


def test_cis_validator_reports_missing_benchmark_and_recommendation_ids(tmp_path: Path) -> None:
    recommendation = _recommendation("1.1.1")
    recommendation.pop("id")
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                {
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "benchmark_page_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
                    "public_versions_page_url": "https://www.cisecurity.org/cis-benchmarks",
                    "release_window": "2024-07",
                    "official_source_status": "fixture",
                    "source_file": "firefox_esr_gpo_1_0_0.yaml",
                    "mapping_file": "mappings.yaml",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path / "firefox_esr_gpo_1_0_0.yaml",
        {
            "benchmark": {"upstream_version": "1.0.0"},
            "recommendations": [recommendation],
        },
    )
    _write_yaml(
        tmp_path / "mappings.yaml",
        {"upstream_version": "1.0.0", "mappings": []},
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("missing required field 'id'" in error for error in result.errors)
    assert any("missing mapping for recommendation" not in error for error in result.errors)


def test_cis_validator_reports_bad_recommendation_and_mapping_shapes(tmp_path: Path) -> None:
    bad_recommendation = _recommendation("1.1.1")
    bad_recommendation["assessment"] = "robot"
    bad_recommendation["rationale_summary"] = "word " * 81
    bad_mapping = _mapping("1.1.1", status="manual")
    bad_mapping["confidence"] = "certain"
    bad_mapping["targets"] = "not-a-list"
    _write_fixture(
        tmp_path,
        recommendations=[
            "bad-rec",
            bad_recommendation,
        ],
        mappings=[
            "bad-map",
            bad_mapping,
        ],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("recommendation must be an object" in error for error in result.errors)
    assert any("unknown assessment 'robot'" in error for error in result.errors)
    assert any("mapping must be an object" in error for error in result.errors)
    assert any("status 'manual' does not match recommendation mapping_status 'mapped'" in error for error in result.errors)
    assert any("unknown confidence 'certain'" in error for error in result.errors)
    assert any("targets must be a list" in error for error in result.errors)
    assert any("contains long prose" in warning for warning in result.warnings)


def test_cis_validator_reports_non_object_yaml_documents(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                {
                    "id": "cis-firefox-esr-gpo",
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "benchmark_page_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
                    "public_versions_page_url": "https://www.cisecurity.org/cis-benchmarks",
                    "release_window": "2024-07",
                    "official_source_status": "fixture",
                    "source_file": "firefox_esr_gpo_1_0_0.yaml",
                    "mapping_file": "mappings.yaml",
                }
            ]
        },
    )
    (tmp_path / "firefox_esr_gpo_1_0_0.yaml").write_text("- bad\n", encoding="utf-8")
    (tmp_path / "mappings.yaml").write_text("- bad\n", encoding="utf-8")

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("top-level YAML document must be an object" in error for error in result.errors)


def test_cis_validator_reports_bad_benchmark_and_recommendation_collection(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                {
                    "id": "cis-firefox-esr-gpo",
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "benchmark_page_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
                    "public_versions_page_url": "https://www.cisecurity.org/cis-benchmarks",
                    "release_window": "2024-07",
                    "official_source_status": "fixture",
                    "source_file": "firefox_esr_gpo_1_0_0.yaml",
                    "mapping_file": "mappings.yaml",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path / "firefox_esr_gpo_1_0_0.yaml",
        {"benchmark": "bad", "recommendations": {"bad": "shape"}},
    )
    _write_yaml(
        tmp_path / "mappings.yaml",
        {"benchmark_id": "cis-firefox-esr-gpo", "upstream_version": "1.0.0", "mappings": []},
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("benchmark must be an object" in error for error in result.errors)
    assert any("recommendations must be a list" in error for error in result.errors)


def test_cis_validator_reports_target_shape_errors(tmp_path: Path) -> None:
    mapping = _mapping(
        "1.1.1",
        targets=[
            "bad-target",
            {
                "kind": "policy",
                "path": ["DisableTelemetry"],
                "schema_channels": "bad",
            },
            {
                "kind": "policy",
                "path": ["DisableTelemetry"],
                "value": True,
                "schema_channels": {"nightly": "valid"},
            },
            {
                "kind": "preference",
                "path": ["browser.one", "browser.two"],
                "value": {"Value": True, "Status": "locked", "Type": "boolean"},
            },
            {
                "kind": "spaceship",
                "path": ["Unknown"],
                "value": True,
            },
        ],
    )
    _write_fixture(
        tmp_path,
        recommendations=[_recommendation("1.1.1")],
        mappings=[mapping],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("target must be an object" in error for error in result.errors)
    assert any("policy target requires value" in error for error in result.errors)
    assert any("schema_channels must be an object" in error for error in result.errors)
    assert any("unsupported schema channel 'nightly'" in error for error in result.errors)
    assert any("duplicate target ('policy', ('DisableTelemetry',))" in error for error in result.errors)
    assert any("preference target path must contain exactly one preference key" in error for error in result.errors)
    assert any("unknown target kind 'spaceship'" in error for error in result.errors)


def test_cis_validator_reports_mapping_collection_and_required_field_errors(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "benchmarks": [
                {
                    "id": "cis-firefox-esr-gpo",
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "benchmark_page_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
                    "public_versions_page_url": "https://www.cisecurity.org/cis-benchmarks",
                    "release_window": "2024-07",
                    "official_source_status": "fixture",
                    "source_file": "firefox_esr_gpo_1_0_0.yaml",
                    "mapping_file": "mappings.yaml",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path / "firefox_esr_gpo_1_0_0.yaml",
        {
            "benchmark": {"id": "cis-firefox-esr-gpo", "upstream_version": "1.0.0"},
            "recommendations": [_recommendation("1.1.1")],
        },
    )
    _write_yaml(
        tmp_path / "mappings.yaml",
        {
            "benchmark_id": "wrong",
            "upstream_version": "2.0.0",
            "mappings": {
                "bad": "shape",
            },
        },
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("benchmark_id must be 'cis-firefox-esr-gpo'" in error for error in result.errors)
    assert any("upstream_version must be '1.0.0'" in error for error in result.errors)
    assert any("mappings must be a list" in error for error in result.errors)
    assert any("missing mapping for recommendation '1.1.1'" in error for error in result.errors)


def test_cis_validator_reports_duplicate_mapping_and_missing_target(tmp_path: Path) -> None:
    mapping_without_targets = _mapping("1.1.1")
    mapping_without_targets["targets"] = []
    mapping_duplicate = _mapping("1.1.1")
    _write_fixture(
        tmp_path,
        recommendations=[_recommendation("1.1.1")],
        mappings=[mapping_without_targets, mapping_duplicate],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("mapped statuses require at least one target" in error for error in result.errors)
    assert any("duplicate mapping for recommendation '1.1.1'" in error for error in result.errors)


def test_cis_validator_reports_missing_and_non_string_required_fields(tmp_path: Path) -> None:
    bad_recommendation = _recommendation("1.1.1")
    bad_recommendation["title"] = 123
    bad_recommendation["mapping_status"] = ""
    bad_mapping = _mapping("1.1.1")
    bad_mapping["recommendation_id"] = 123
    bad_mapping["status"] = ""
    bad_mapping["confidence"] = 123
    _write_fixture(
        tmp_path,
        recommendations=[bad_recommendation],
        mappings=[bad_mapping],
    )

    result = validate_sources(tmp_path)

    assert not result.ok
    assert any("field 'title' must be a string" in error for error in result.errors)
    assert any("missing required field 'mapping_status'" in error for error in result.errors)
    assert any("field 'recommendation_id' must be a string" in error for error in result.errors)
    assert any("missing required field 'status'" in error for error in result.errors)
    assert any("field 'confidence' must be a string" in error for error in result.errors)


def test_cis_validation_and_coverage_formatters_include_errors_warnings_and_empty_counts() -> None:
    result = validate_sources()
    text = format_validation_summary(result)
    assert "CIS Firefox source validation: ok" in text
    assert "Benchmarks: 1" in text

    markdown = format_coverage_markdown(
        {
            "benchmarks": [
                {
                    "upstream_name": "Fixture",
                    "upstream_version": "1.0",
                    "benchmark_id": "fixture",
                    "official_source_status": "fixture",
                    "total_recommendations": 0,
                    "total_mappings": 0,
                    "by_recommendation_status": {},
                    "by_mapping_status": {},
                    "by_level": {},
                    "schema_compatibility": {},
                }
            ],
            "warnings": ["careful"],
            "errors": ["broken"],
        }
    )

    assert "## Fixture v1.0" in markdown
    assert "- none: 0" in markdown
    assert "## Warnings" in markdown
    assert "## Errors" in markdown

    invalid = validate_sources(Path("/tmp/definitely-missing-cis-fixture"))
    invalid_text = format_validation_summary(invalid)
    assert "Warnings:" not in invalid_text
    assert "Errors:" in invalid_text

    warning_text = format_validation_summary(
        ValidationResult(
            errors=(),
            warnings=("check manually",),
            summary={"benchmark_count": 0, "benchmarks": []},
        )
    )
    assert "Warnings:" in warning_text
    assert "- check manually" in warning_text
    assert "Errors:" not in warning_text

    no_warning_markdown = format_coverage_markdown(
        {
            "benchmarks": [
                {
                    "upstream_name": "Fixture",
                    "upstream_version": "1.0",
                    "benchmark_id": "fixture",
                    "official_source_status": "fixture",
                    "total_recommendations": 1,
                    "total_mappings": 1,
                    "by_recommendation_status": {"mapped": 1},
                    "by_mapping_status": {"mapped": 1},
                    "by_level": {"L1": 1},
                    "schema_compatibility": {"release-150:valid": 1},
                }
            ],
            "warnings": [],
            "errors": [],
        }
    )
    assert "- mapped: 1" in no_warning_markdown
    assert "## Warnings" not in no_warning_markdown
    assert "## Errors" not in no_warning_markdown


def test_cis_coverage_report_skips_non_object_mappings_and_targets(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        recommendations=[_recommendation("1.1.1", status="manual")],
        mappings=[
            "bad",
            {
                "recommendation_id": "1.1.1",
                "status": "manual",
                "confidence": "high",
                "targets": ["bad-target"],
            },
        ],
    )

    report = build_coverage_report(tmp_path)

    assert report["ok"] is False
    assert report["benchmarks"][0]["schema_compatibility"] == {}


def test_cis_coverage_report_counts_statuses(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        recommendations=[
            _recommendation("1.1.1", level=1, status="mapped"),
            _recommendation("1.1.2", level=2, status="manual"),
        ],
        mappings=[
            _mapping("1.1.1", status="mapped"),
            _mapping("1.1.2", status="manual", targets=[]),
        ],
    )

    report = build_coverage_report(tmp_path)
    benchmark = report["benchmarks"][0]

    assert report["ok"] is True
    assert benchmark["by_recommendation_status"] == {"manual": 1, "mapped": 1}
    assert benchmark["by_mapping_status"] == {"manual": 1, "mapped": 1}
    assert benchmark["by_level"] == {"L1": 1, "L2": 1}
    assert benchmark["schema_compatibility"] == {"esr-140.10:valid": 1, "release-150:valid": 1}


def _write_fixture(
    base_dir: Path,
    *,
    recommendations: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> None:
    _write_yaml(
        base_dir / "sources.yaml",
        {
            "benchmarks": [
                {
                    "id": "cis-firefox-esr-gpo",
                    "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                    "upstream_version": "1.0.0",
                    "product": "Mozilla Firefox",
                    "product_family": "Desktop Software",
                    "benchmark_page_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
                    "public_versions_page_url": "https://www.cisecurity.org/cis-benchmarks",
                    "release_window": "2024-07",
                    "official_source_status": "fixture",
                    "source_file": "firefox_esr_gpo_1_0_0.yaml",
                    "mapping_file": "mappings.yaml",
                }
            ]
        },
    )
    _write_yaml(
        base_dir / "firefox_esr_gpo_1_0_0.yaml",
        {
            "benchmark": {
                "id": "cis-firefox-esr-gpo",
                "upstream_name": "CIS Mozilla Firefox ESR GPO Benchmark",
                "upstream_version": "1.0.0",
                "source_url": "https://www.cisecurity.org/benchmark/mozilla_firefox",
            },
            "recommendations": recommendations,
        },
    )
    _write_yaml(
        base_dir / "mappings.yaml",
        {
            "benchmark_id": "cis-firefox-esr-gpo",
            "upstream_version": "1.0.0",
            "mappings": mappings,
        },
    )


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _recommendation(
    rec_id: str,
    *,
    level: int = 1,
    status: str = "mapped",
) -> dict[str, Any]:
    return {
        "id": rec_id,
        "title": "Ensure example setting is enabled",
        "level": level,
        "assessment": "automated",
        "scored": True,
        "category": "browser_security",
        "mapping_status": status,
    }


def _mapping(
    rec_id: str,
    *,
    status: str = "mapped",
    targets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if targets is None:
        targets = [
            {
                "kind": "policy",
                "path": ["DisableTelemetry"],
                "value": True,
                "schema_channels": {
                    "esr-140.10": "valid",
                    "release-150": "valid",
                },
            }
        ]
    return {
        "recommendation_id": rec_id,
        "status": status,
        "confidence": "high",
        "targets": targets,
    }
