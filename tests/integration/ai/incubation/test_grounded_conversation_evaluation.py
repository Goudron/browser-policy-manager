from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

RUNNER_PATH = (
    Path(__file__).resolve().parents[4]
    / "documentation/tools/run_grounded_conversation_evaluation_0_9_3.py"
)

spec = importlib.util.spec_from_file_location("grounded_conversation_evaluation", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def test_six_locale_evaluation_proves_m7_grounding_citations_continuity_and_terminals(
    capsys: object,
) -> None:
    report = runner.run()

    assert report["status"] == "pass"
    assert report["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert set(report["per_locale"]) == set(report["locales"])
    for metrics in report["per_locale"].values():
        assert metrics == {
            "grounded_answer_rate": 1.0,
            "citation_resolution_rate": 1.0,
            "dialogue_continuity_rate": 1.0,
            "abstention_rate": 1.0,
            "refusal_rate": 1.0,
            "answer_case_count": 2,
            "terminal_case_count": 2,
        }
    assert report["boundaries"] == {
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "cross_locale_retrieval_calls": 0,
        "chat_model_started": False,
        "fixture_conversation_content_retained": False,
    }
    assert "locale 4/6 zh-CN: 4/4 checks passed" in capsys.readouterr().out


def test_evaluation_report_is_content_free_and_cache_bounded(tmp_path: Path) -> None:
    report = runner.run()
    cache_root = tmp_path / ".cache"
    runner.DOCUMENTATION_ROOT = tmp_path
    output = cache_root / "bpm093-m7-07" / "evaluation.json"
    runner._write_report(report, output)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["status"] == "pass"
    serialized = output.read_text(encoding="utf-8")
    assert "Как настроить" not in serialized
    assert "How do I configure" not in serialized
