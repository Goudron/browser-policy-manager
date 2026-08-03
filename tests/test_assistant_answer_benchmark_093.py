from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

RUNNER_PATH = Path(__file__).resolve().parents[1] / "documentation/tools/run_assistant_answer_benchmark_0_9_3.py"

spec = importlib.util.spec_from_file_location("assistant_answer_benchmark", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def test_m13_06a_has_one_native_prompt_for_every_intent_and_active_locale() -> None:
    config = json.loads(runner.CONFIG_PATH.read_text(encoding="utf-8"))
    cases = runner._cases(config)

    assert len(cases) == 60
    assert [case.locale for case in cases[::10]] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert all(case.question.strip() for case in cases)
    assert all("\n" not in case.question for case in cases)
    execution_locales = runner._execution_locales(config)
    assert execution_locales == ("en", "ru")
    execution_cases = runner._execution_cases(cases, execution_locales)
    assert len(execution_cases) == 20
    representative = runner._representative_cases(execution_cases, list(execution_locales))
    assert [(case.locale, case.question_id) for case in representative] == [
        ("en", "local-ubuntu-install"),
        ("ru", "local-minimum-requirements"),
    ]


def test_m13_06a_classifies_fail_closed_outcomes_without_retaining_content() -> None:
    assert runner._failure_category("assistant_relevance_no_matching_evidence") == "retrieval_or_relevance"
    assert runner._failure_category("assistant_output_invalid") == "composition"
    assert runner._failure_category("assistant_generation_unavailable") == "model_quality"
    assert runner._hash_text("local answer") != "local answer"
