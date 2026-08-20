from __future__ import annotations

import copy
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from app.core.schema_channels import SCHEMA_CHANNELS
from tests.docs_index import doc_path_from_index

# This is a documentation-owned architecture contract; it intentionally checks
# the current application artifacts without changing their implementation.

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
CONTRACT_PATH = REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.md"
DUAL_ESR_PATH = REPO_ROOT / "docs/architecture/firefox-153-dual-esr-schema-contract-0.9.2.md"
PROVENANCE_PATH = REPO_ROOT / "docs/architecture/firefox-four-channel-provenance-matrix-0.9.5.md"
TARGETS_PATH = REPO_ROOT / "tools/firefox_schema_targets.json"
INPUT_MANIFEST_PATH = REPO_ROOT / "tools/firefox_schema_inputs_manifest_0_9_4.json"
SCHEMAS_DIR = REPO_ROOT / "app/schemas/policies"

EXPECTED_ARTIFACT_IDS = (
    "release-153",
    "esr-153.0",
    "esr-140.13",
    "esr-115.39",
)
CURRENT_RUNTIME_ARTIFACT_IDS = EXPECTED_ARTIFACT_IDS


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    assert isinstance(value, dict)
    return value


def _catalog() -> dict[str, Any]:
    return _load_json(CATALOG_PATH)


def _artifact_version_key(row: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(part) for part in row["artifact_version"].split("."))


def _ordered_rows(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    family_order = catalog["ordering"]["family_order"]
    family_rank = {family: rank for rank, family in enumerate(family_order)}
    return sorted(
        catalog["channels"],
        key=lambda row: (
            family_rank[row["family"]],
            -row["line_number"],
            tuple(-part for part in _artifact_version_key(row)),
            row["artifact_id"],
        ),
    )


def _public_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    ordered_rows = _ordered_rows(catalog)
    rows_by_line = {row["line_id"]: row for row in ordered_rows}
    supported_rows = [
        row for row in ordered_rows if row["support"]["state"] == "supported" and row["selectable"]
    ]
    latest_esr = next(row for row in supported_rows if row["roles"]["latest_esr"])
    default = next(row for row in supported_rows if row["roles"]["product_default"])
    default_release = next(row for row in supported_rows if row["roles"]["default_release"])

    def option(row: dict[str, Any]) -> dict[str, Any]:
        target_line_id = row["recommendation_target_line_id"]
        return {
            "value": row["artifact_id"],
            "label": row["label"],
            "i18n_key": row["i18n_key"],
            "line_id": row["line_id"],
            "artifact_id": row["artifact_id"],
            "family": row["family"],
            "support_state": row["support"]["state"],
            "selectable": row["selectable"],
            "is_latest_esr": row["roles"]["latest_esr"],
            "is_product_default": row["roles"]["product_default"],
            "is_default_release": row["roles"]["default_release"],
            "recommendation_target": (
                rows_by_line[target_line_id]["artifact_id"] if target_line_id is not None else None
            ),
        }

    supported_ids = [row["artifact_id"] for row in supported_rows]
    return {
        "catalog_version": catalog["serialization"]["catalog_version"],
        "supported_channels": supported_ids,
        "default_channel": default["artifact_id"],
        "default_release_channel": default_release["artifact_id"],
        "latest_esr_channel": latest_esr["artifact_id"],
        "esr_channels": [row["artifact_id"] for row in supported_rows if row["family"] == "esr"],
        "selector_channels": supported_ids,
        "header_channels": supported_ids,
        "default_label": default["label"],
        "labels": {row["artifact_id"]: row["label"] for row in supported_rows},
        "filenames": {row["artifact_id"]: row["source"]["filename"] for row in supported_rows},
        "mozilla_versions": {row["artifact_id"]: row["artifact_version"] for row in supported_rows},
        "sources": {row["artifact_id"]: row["source"]["source_tag"] for row in supported_rows},
        "options": [option(row) for row in supported_rows],
    }


def _assert_catalog_is_valid(catalog: dict[str, Any]) -> None:
    assert catalog["schema_version"] == 1
    assert catalog["contract_id"] == "bpm095-firefox-schema-lifecycle-catalog"
    assert catalog["target_bpm_version"] == "0.9.5.1"
    assert catalog["status"] == "active-runtime-catalog"
    assert catalog["implementation"] == {
        "phase": "m3-03-runtime-wired",
        "current_runtime_artifact_ids": list(CURRENT_RUNTIME_ARTIFACT_IDS),
        "generated_artifact_ids": list(EXPECTED_ARTIFACT_IDS),
    }

    rows = catalog["channels"]
    assert len(rows) == len(EXPECTED_ARTIFACT_IDS)
    assert {row["artifact_id"] for row in rows} == set(EXPECTED_ARTIFACT_IDS)
    assert all(row["artifact_id"] == row["channel_id"] for row in rows)

    for field in ("line_id", "artifact_id", "channel_id", "i18n_key"):
        values = [row[field] for row in rows]
        assert len(values) == len(set(values)), field
    filenames = [row["source"]["filename"] for row in rows]
    assert len(filenames) == len(set(filenames))

    for row in rows:
        assert row["family"] in {"esr", "release"}
        assert isinstance(row["line_number"], int) and row["line_number"] > 0
        assert re.fullmatch(r"\d+(?:\.\d+)+", row["artifact_version"])
        assert row["source"]["output_path"].endswith(row["source"]["filename"])
        assert row["i18n_key"].startswith("profiles.firefox_schema_")
        assert set(row["roles"]) == {"latest_esr", "product_default", "default_release"}

        support = row["support"]
        assert support["state"] in {"supported", "retired"}
        assert support["browser_version_field"]
        assert support["browser_version"]
        assert support["evidence_urls"]
        assert all(url.startswith("https://") for url in support["evidence_urls"])
        date.fromisoformat(support["verified_on"])
        date.fromisoformat(support["recheck_on"])
        assert set(support["end"]) == {"kind", "value"}
        assert support["end"]["kind"] in {"not-announced", "date", "month"}
        if support["end"]["kind"] == "not-announced":
            assert support["end"]["value"] is None
        elif support["end"]["kind"] == "date":
            date.fromisoformat(support["end"]["value"])
        else:
            assert re.fullmatch(r"\d{4}-\d{2}", support["end"]["value"])
        assert row["selectable"] is (support["state"] == "supported")

        source = row["source"]
        assert re.fullmatch(
            r"mozilla-policy-templates-(?:v\d+(?:\.\d+)*|master-[0-9a-f]{40})",
            source["source_tag"],
        )
        assert re.fullmatch(r"(?:v\d+(?:\.\d+)*|[0-9a-f]{40})", source["upstream_tag"])
        for input_name in ("documentation_input", "linux_policies_input"):
            input_spec = source[input_name]
            assert input_spec["local_path"].startswith("data/upstream/policy-templates/")
            assert input_spec["url"].startswith("https://raw.githubusercontent.com/mozilla/")
            assert re.fullmatch(r"[0-9a-f]{64}", input_spec["sha256"])

    rows_by_line = {row["line_id"]: row for row in rows}
    esr_rows = [row for row in rows if row["family"] == "esr"]
    release_rows = [row for row in rows if row["family"] == "release"]
    assert [
        row["line_id"] for row in sorted(esr_rows, key=lambda row: row["line_number"], reverse=True)
    ] == ["esr-153", "esr-140", "esr-115"]
    assert len(release_rows) == 1
    assert all(row["line_id"] == f"esr-{row['line_number']}" for row in esr_rows)

    supported_rows = [row for row in rows if row["support"]["state"] == "supported"]
    selectable_rows = [row for row in rows if row["selectable"]]
    assert {row["artifact_id"] for row in supported_rows} == set(EXPECTED_ARTIFACT_IDS)
    assert {row["artifact_id"] for row in selectable_rows} == set(EXPECTED_ARTIFACT_IDS)
    assert [row["artifact_id"] for row in rows if row["roles"]["latest_esr"]] == ["esr-153.0"]
    assert [row["artifact_id"] for row in rows if row["roles"]["product_default"]] == ["esr-153.0"]
    assert [row["artifact_id"] for row in rows if row["roles"]["default_release"]] == [
        "release-153"
    ]
    assert all(not row["roles"]["latest_esr"] for row in release_rows)
    assert all(not row["roles"]["product_default"] for row in release_rows)

    latest_esr = next(row for row in esr_rows if row["roles"]["latest_esr"])
    assert latest_esr["roles"]["product_default"]
    for row in rows:
        target_line_id = row["recommendation_target_line_id"]
        if row["family"] == "esr" and row["line_number"] < latest_esr["line_number"]:
            assert target_line_id == latest_esr["line_id"]
        else:
            assert target_line_id is None

    # The expected edge is calculated from numeric ESR line order, never the
    # row declaration order, artifact string, or the recommendation target.
    successors: dict[str, str] = {}
    for row in esr_rows:
        newer_rows = sorted(
            (candidate for candidate in esr_rows if candidate["line_number"] > row["line_number"]),
            key=lambda candidate: candidate["line_number"],
        )
        expected_successor = newer_rows[0]["line_id"] if newer_rows else None
        successor_line_id = row["retirement_successor_line_id"]
        assert successor_line_id == expected_successor
        if successor_line_id is not None:
            successor = rows_by_line[successor_line_id]
            assert successor["family"] == "esr"
            assert successor["support"]["state"] == "supported"
            assert successor["selectable"]
            assert successor["line_number"] > row["line_number"]
            successors[row["line_id"]] = successor_line_id
    assert all(row["retirement_successor_line_id"] is None for row in release_rows)

    for line_id in successors:
        seen: set[str] = set()
        cursor = line_id
        while cursor in successors:
            assert cursor not in seen
            seen.add(cursor)
            cursor = successors[cursor]

    ordered_ids = [row["artifact_id"] for row in _ordered_rows(catalog)]
    assert ordered_ids == list(EXPECTED_ARTIFACT_IDS)
    assert catalog["ordering"]["public_orders"] == {
        "selector": ordered_ids,
        "header": ordered_ids,
    }

    public_catalog = _public_catalog(catalog)
    expected_public_keys = set(catalog["serialization"]["legacy_top_level_fields"]) | set(
        catalog["serialization"]["added_top_level_fields"]
    )
    assert set(public_catalog) == expected_public_keys
    assert public_catalog["supported_channels"] == ordered_ids
    assert public_catalog["selector_channels"] == ordered_ids
    assert public_catalog["header_channels"] == ordered_ids
    assert public_catalog["default_channel"] == "esr-153.0"
    assert public_catalog["default_release_channel"] == "release-153"
    assert public_catalog["latest_esr_channel"] == "esr-153.0"
    assert public_catalog["esr_channels"] == ["esr-153.0", "esr-140.13", "esr-115.39"]
    assert public_catalog["default_label"] == "ESR 153.0"
    assert [set(option) for option in public_catalog["options"]] == [
        set(catalog["serialization"]["option_fields"])
    ] * len(ordered_ids)
    assert public_catalog["options"][2]["recommendation_target"] == "esr-153.0"
    assert public_catalog["options"][3]["recommendation_target"] == "esr-153.0"

    assert catalog["api_behavior"] == {
        "catalog_visibility": {
            "supported": "listed",
            "retired": "not-listed",
            "unknown": "not-listed",
        },
        "write_target_errors": {
            "unknown": {"status": 422, "code": "schema_channel_unknown"},
            "retired": {"status": 422, "code": "schema_channel_retired"},
        },
        "stored_profile_errors": {
            "unknown": {"status": 409, "code": "schema_channel_unknown"},
            "retired": {
                "status": 409,
                "code": "schema_channel_retired_requires_migration",
            },
        },
    }


def test_catalog_fixture_is_normative_and_fail_closed() -> None:
    _assert_catalog_is_valid(_catalog())


def test_catalog_order_and_public_serialization_ignore_declaration_order() -> None:
    catalog = _catalog()
    expected_payload = _public_catalog(catalog)
    catalog["channels"].reverse()

    _assert_catalog_is_valid(catalog)
    assert _public_catalog(catalog) == expected_payload


@pytest.mark.parametrize(
    ("mutation", "expected_failure"),
    [
        (
            lambda catalog: catalog["channels"][3].__setitem__(
                "i18n_key", catalog["channels"][2]["i18n_key"]
            ),
            "i18n_key",
        ),
        (
            lambda catalog: catalog["channels"][2].__setitem__("selectable", False),
            "AssertionError",
        ),
        (
            lambda catalog: (
                catalog["channels"][2].__setitem__("retirement_successor_line_id", "esr-153")
                or catalog["channels"][3].__setitem__("retirement_successor_line_id", "esr-153")
            ),
            "AssertionError",
        ),
        (
            lambda catalog: catalog["channels"][2]["roles"].__setitem__("product_default", True),
            "AssertionError",
        ),
        (
            lambda catalog: catalog["ordering"]["public_orders"].__setitem__(
                "header", list(reversed(catalog["ordering"]["public_orders"]["header"]))
            ),
            "AssertionError",
        ),
    ],
)
def test_catalog_validation_rejects_identity_role_order_and_successor_mutations(
    mutation: Any,
    expected_failure: str,
) -> None:
    catalog = copy.deepcopy(_catalog())
    mutation(catalog)

    with pytest.raises(AssertionError) as error:
        _assert_catalog_is_valid(catalog)
    if expected_failure != "AssertionError":
        assert expected_failure in str(error.value)


def test_generated_four_artifacts_match_catalog_source_and_output_identity() -> None:
    catalog = _catalog()
    rows = {row["artifact_id"]: row for row in catalog["channels"]}
    current_rows = {artifact_id: rows[artifact_id] for artifact_id in CURRENT_RUNTIME_ARTIFACT_IDS}
    declared_channels = {channel.value: channel for channel in SCHEMA_CHANNELS}
    assert set(declared_channels) == set(current_rows)

    targets = _load_json(TARGETS_PATH)["targets"]
    targets_by_channel = {target["channel"]: target for target in targets}
    assert set(targets_by_channel) == set(EXPECTED_ARTIFACT_IDS)

    inputs = _load_json(INPUT_MANIFEST_PATH)["inputs"]
    inputs_by_tag = {input_spec["source_tag"]: input_spec for input_spec in inputs}

    for artifact_id, row in rows.items():
        source = row["source"]
        if artifact_id in current_rows:
            channel = declared_channels[artifact_id]
            assert channel.filename == source["filename"]
            assert channel.mozilla_version == row["artifact_version"]
            assert channel.source_tag == source["source_tag"]
            assert channel.label == row["label"]
            assert channel.i18n_key == row["i18n_key"]
        else:
            assert artifact_id not in declared_channels

        target = targets_by_channel[artifact_id]
        assert target["channel"] == artifact_id
        assert target["artifact_id"] == artifact_id
        assert target["line_id"] == row["line_id"]
        assert target["version"] == row["artifact_version"]
        assert target["source_tag"] == source["source_tag"]
        assert target["documentation_input"] == source["documentation_input"]["local_path"]
        assert target["linux_policies_input"] == source["linux_policies_input"]["local_path"]
        assert target["output"] == source["output_path"]

        input_spec = inputs_by_tag[source["source_tag"]]
        assert input_spec["upstream_tag"] == source["upstream_tag"]
        expected_files = {
            "policy-templates.md": source["documentation_input"],
            "linux-policies.json": source["linux_policies_input"],
        }
        assert {file_spec["name"] for file_spec in input_spec["files"]} == set(expected_files)
        for file_spec in input_spec["files"]:
            expected = expected_files[file_spec["name"]]
            assert file_spec["url"] == expected["url"]
            assert file_spec["sha256"] == expected["sha256"]
            assert file_spec["bytes"] > 0

        schema = _load_json(SCHEMAS_DIR / source["filename"])
        assert schema["x-bpm-channel"] == artifact_id
        assert schema["x-bpm-version"] == row["artifact_version"]
        assert schema["x-bpm-source"] == source["source_tag"]
        assert schema["x-bpm-artifact-id"] == artifact_id
        assert schema["x-bpm-line-id"] == row["line_id"]
        assert schema["x-bpm-firefox-line"] == row["line_number"]
        assert schema["x-bpm-firefox-version"] == row["support"]["browser_version"]
        assert schema["x-bpm-ui-label"] == row["label"]
        assert schema["x-bpm-source-provenance"]["source_tag"] == source["source_tag"]
        assert schema["x-bpm-source-provenance"]["upstream_tag"] == source["upstream_tag"]
        assert schema["x-bpm-generator"] == {
            "identity": "bpm-firefox-policy-schema-converter/v1",
            "entrypoint": "tools/convert_policies_from_upstream.py",
        }


def test_esr_115_is_generated_and_wired_as_a_runtime_artifact() -> None:
    catalog = _catalog()
    generated = next(row for row in catalog["channels"] if row["artifact_id"] == "esr-115.39")
    assert generated["line_id"] == "esr-115"
    assert generated["support"]["browser_version"] == "115.39.0esr"
    assert generated["source"]["source_tag"] == "mozilla-policy-templates-v5.12"
    assert (SCHEMAS_DIR / generated["source"]["filename"]).exists()
    assert "esr-115.39" in {channel.value for channel in SCHEMA_CHANNELS}

    target_channels = {target["channel"] for target in _load_json(TARGETS_PATH)["targets"]}
    input_tags = {
        input_spec["source_tag"] for input_spec in _load_json(INPUT_MANIFEST_PATH)["inputs"]
    }
    assert generated["artifact_id"] in target_channels
    assert generated["source"]["source_tag"] in input_tags

    provenance = PROVENANCE_PATH.read_text(encoding="utf-8")
    for required in (
        "`esr-115.39`",
        "`115.39.0esr`",
        "`mozilla-policy-templates-v5.12`",
        "`firefox-esr-115.39.json`",
        "March 2027",
    ):
        assert required in provenance


def test_contract_is_indexed_and_bounds_the_092_dual_esr_rules() -> None:
    assert (
        doc_path_from_index(
            "architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.md", status="active"
        )
        == CONTRACT_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json", status="active"
        )
        == CATALOG_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/firefox-153-dual-esr-schema-contract-0.9.2.md", status="archive"
        )
        == DUAL_ESR_PATH
    )

    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    for required in (
        "stable lifecycle identity",
        "exact persisted/public schema artifact identifier",
        "`esr-115` -> `esr-140` -> `esr-153`",
        "recommend an explicit, previewable user conversion",
        "never choose a successor by `max()`",
        "no singular current ESR controls persistence",
        "schema_channel_retired_requires_migration",
        "Automatic cross-ESR conversion is permitted only after the source line is retired",
        "No other 0.9.2 source-provenance, independent-generation, or supported-line",
    ):
        assert required.casefold() in contract.casefold()

    historical_contract = DUAL_ESR_PATH.read_text(encoding="utf-8")
    assert "Status: historical architecture evidence." in historical_contract
    assert "There is no automatic migration from any Firefox 140 ESR channel" in historical_contract
