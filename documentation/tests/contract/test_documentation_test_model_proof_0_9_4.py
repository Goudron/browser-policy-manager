"""Fail closed on the BPM094-M11A-06 layered documentation proof."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from documentation.buildlib import sources

ROOT = Path(__file__).resolve().parents[3]
PROOF_PATH = ROOT / "documentation/config/documentation-test-model-proof-0.9.4.json"
SNAPSHOT_GENERATOR_PATH = ROOT / "documentation/tools/generate_subsystem_snapshot.py"
SPEC = importlib.util.spec_from_file_location("m11a06_snapshot_generator", SNAPSHOT_GENERATOR_PATH)
assert SPEC and SPEC.loader
snapshot_generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot_generator)

pytestmark = pytest.mark.docs_contract


def _proof() -> dict[str, object]:
    return json.loads(PROOF_PATH.read_text(encoding="utf-8"))


def _minimal_topic(topic_id: str, title: str, paragraph: str) -> str:
    return f'<topic id="{topic_id}"><title>{title}</title><body><p>{paragraph}</p></body></topic>'


def _patch_fast_roots(monkeypatch: pytest.MonkeyPatch, repository: Path) -> Path:
    documentation = repository / "documentation"
    monkeypatch.setattr(sources, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(sources, "DOCUMENTATION_ROOT", documentation)
    return documentation


def test_proof_record_is_complete_truthful_and_release_clean() -> None:
    proof = _proof()

    assert proof["schema_version"] == 1
    assert proof["evidence_id"] == "bpm-0.9.4-documentation-test-model-proof"
    assert proof["backlog_item"] == "BPM094-M11A-06"
    assert proof["target_bpm_version"] == "0.9.4"
    assert proof["status"] in {"release-handoff-pending", "proven-clean"}
    assert proof["mutation_isolation"]["maintained_documentation_mutated"] is False
    assert all((ROOT / path).is_file() for path in proof["authority_records"])

    executions = {entry["id"]: entry for entry in proof["executions"]}
    assert set(executions) == {
        "m11a-prerequisite-contracts",
        "english-editorial-fast",
        "russian-localization-fast",
        "false-blocker-replay",
        "meaningful-negative-regressions",
        "isolated-benign-mutation-and-snapshot-scope",
        "authoritative-release-handoff",
        "post-handoff-evidence-seal",
    }
    for execution in executions.values():
        assert execution["command"]
        assert execution["passed"] >= 0
        assert execution["deselected"] >= 0
    handoff = executions["authoritative-release-handoff"]
    completed = proof["status"] == "proven-clean"
    for execution in executions.values():
        if execution is handoff and not completed:
            assert execution["result"] == "pending"
            assert execution["wall_duration_seconds"] is None
        else:
            assert execution["result"] != "pending"
            assert execution["wall_duration_seconds"] > 0
    if completed:
        assert handoff["result"] == "passed"
        assert handoff["completed_chain"] == [
            "docs-snapshot",
            "docs-release-check",
            "docs-pdf-build",
            "docs-pdf-verify",
            "docs-pdf-deliver",
            "docs-pdf-delivery-verify",
            "docs-reproducibility-check",
            "docs-package",
            "docs-package-verify",
            "docs-install-dev",
        ]
    else:
        assert handoff["completed_chain"] == []

    assert proof["skipped_by_design"]["authoritative_release_handoff"] == []
    assert len(proof["skipped_by_design"]["fast_authoring"]) == 4
    assert all(
        audit["status"] == "approved-separate-owner" for audit in proof["approved_separate_audits"]
    )
    if completed:
        assert proof["conclusion"].startswith("Benign scoped edits pass")
    else:
        assert proof["conclusion"] == "Pending the authoritative release handoff execution."


def test_benign_editorial_rephrase_passes_fast_layer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation = _patch_fast_roots(monkeypatch, tmp_path)
    topic = documentation / "src/dita/en/user/editorial.dita"
    topic.parent.mkdir(parents=True)
    topic.write_text(
        _minimal_topic(
            "ug-concept-editorial-proof",
            "Editorial proof",
            "This sentence is a valid benign rephrase with unchanged reader semantics.",
        ),
        encoding="utf-8",
    )

    report = sources.fast_check(["documentation/src/dita/en/user/editorial.dita"], emit=False)

    assert report["checked"] == ["documentation/src/dita/en/user/editorial.dita"]
    assert report["locales"] == ["en"]
    assert report["checked_guards"] == [
        "schema and direct links",
        "semantic UI/admonition and figures",
    ]
    assert report["recommended_next_checks"] == ["make docs-release-handoff"]
    assert "binary PDF build, verification, and delivery" in report["skipped_release_only_checks"]


def test_benign_localized_rephrase_passes_shape_aware_fast_layer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation = _patch_fast_roots(monkeypatch, tmp_path)
    english = documentation / "src/dita/en/user/localized.dita"
    russian = documentation / "src/dita/ru/user/localized.dita"
    english.parent.mkdir(parents=True)
    russian.parent.mkdir(parents=True)
    english.write_text(
        _minimal_topic("ug-concept-localized-proof", "Localized proof", "English source text."),
        encoding="utf-8",
    )
    russian.write_text(
        _minimal_topic(
            "ug-concept-localized-proof",
            "Проверка локализации",
            "Корректная редакционная формулировка сохраняет структуру темы.",
        ),
        encoding="utf-8",
    )

    report = sources.fast_check(["documentation/src/dita/ru/user/localized.dita"], emit=False)

    assert report["locales"] == ["ru"]
    assert "localized structural shape when a locale topic changed" in report["checked_guards"]
    assert report["recommended_next_checks"] == ["make docs-release-handoff"]


def test_snapshot_scope_ignores_undeclared_input_but_tracks_declared_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path
    documentation = repository / "documentation"
    declared = documentation / "config/authority.json"
    undeclared = documentation / "src/dita/en/user/editorial.dita"
    declared.parent.mkdir(parents=True)
    undeclared.parent.mkdir(parents=True)
    declared.write_text('{"state":"accepted"}', encoding="utf-8")

    monkeypatch.setattr(snapshot_generator, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(snapshot_generator, "DOCUMENTATION_ROOT", documentation)
    monkeypatch.setattr(
        snapshot_generator,
        "SOURCE_OWNERS",
        (("Proof authority", "snapshot proof owner", ("documentation/config/authority.json",)),),
    )
    monkeypatch.setattr(snapshot_generator, "ARCHITECTURE_ENTRY_POINTS", ())
    monkeypatch.setattr(snapshot_generator, "_product_version", lambda: "0.9.4")

    before = snapshot_generator.generate_snapshot()
    undeclared.write_text(
        _minimal_topic("ug-concept-snapshot-proof", "Snapshot proof", "Benign rephrase."),
        encoding="utf-8",
    )
    after_undeclared_change = snapshot_generator.generate_snapshot()
    declared.write_text('{"state":"changed"}', encoding="utf-8")
    after_declared_change = snapshot_generator.generate_snapshot()

    assert before == after_undeclared_change
    assert after_declared_change != before


def test_malformed_source_fails_in_fast_layer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation = _patch_fast_roots(monkeypatch, tmp_path)
    broken = documentation / "src/dita/en/user/broken.dita"
    broken.parent.mkdir(parents=True)
    broken.write_text('<topic id="broken"><title>Broken</topic>', encoding="utf-8")

    with pytest.raises(sources.BuildError, match="focused source link validation failed"):
        sources.fast_check(["documentation/src/dita/en/user/broken.dita"], emit=False)


def test_false_blocker_replay_and_runtime_comparison_are_exact() -> None:
    proof = _proof()
    comparison = proof["false_blocker_comparison"]
    baseline = proof["m11_baseline"]["false_blocker_population"]
    runtime = proof["runtime_comparison"]

    assert baseline["cases"] == [
        "M11-FB-001",
        "M11-FB-002",
        "M11-FB-003",
        "M11-FB-004",
        "M11-FB-005",
        "M11-FB-006",
    ]
    assert comparison == {
        "population_size": 6,
        "m11_false_blocks": 6,
        "m11_rate": 1.0,
        "m11a_false_blocks": 0,
        "m11a_rate": 0.0,
        "absolute_rate_reduction": 1.0,
        "replay_result": (
            "All six current positive authorities passed; their negative counterparts continue to fail closed."
        ),
    }
    assert runtime["slowest_fast_wall_seconds"] <= runtime["slowest_fast_within_budget_seconds"]
    assert runtime["broad_to_slowest_fast_ratio"] == pytest.approx(
        runtime["broad_comparator_wall_seconds"] / runtime["slowest_fast_wall_seconds"],
        abs=0.01,
    )


def test_scenarios_name_existing_proof_owners_and_earliest_layers() -> None:
    proof = _proof()
    scenarios = proof["scenarios"]
    expected_layers = {
        "benign-editorial-rephrase": "fast-authoring",
        "benign-localized-rephrase": "fast-authoring",
        "undeclared-topic-snapshot-change": "scheduled-audit",
        "malformed-changed-source": "fast-authoring",
        "release-chain-package-proof-removed": "release-gate-semantic-contract",
        "corrupt-pdf-cache": "pdf-build-owner",
        "incomplete-pdf-figure-inventory": "pdf-build-owner",
        "package-missing-locale-root": "package-verification-owner",
    }

    assert {scenario["id"]: scenario["expected_layer"] for scenario in scenarios} == expected_layers
    assert all(scenario["false_block"] is False for scenario in scenarios)
    test_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path(__file__),
            ROOT / "documentation/tests/contract/test_documentation_semantic_contracts_0_9_4.py",
            ROOT / "documentation/tests/unit/test_build_docs.py",
            ROOT / "documentation/tests/unit/test_buildlib_artifacts.py",
        )
    )
    assert all(f"def {scenario['proof_test']}" in test_sources for scenario in scenarios)
