from __future__ import annotations

import importlib.util
import json
import queue
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/local-chat-target-laptop-benchmark-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/run_local_chat_target_laptop_benchmark_0_9_3.py"

pytestmark = pytest.mark.docs_contract

spec = importlib.util.spec_from_file_location("local_chat_target_laptop_benchmark", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_benchmark_rejects_resource_regressions_but_treats_swap_as_diagnostic() -> None:
    config = _config()
    records = []
    for locale in config["protocol"]["locale_order"]:
        for state, scenarios in config["protocol"]["selection_sample_counts"].items():
            for scenario, count in scenarios.items():
                for _attempt in range(count):
                    records.append(
                        {
                            "locale": locale,
                            "state": state,
                            "warmup": False,
                            "ttft_ns": 1_000_000,
                            "completion_ns": 2_000_000,
                            "tokens_per_second": 4.0,
                            "peak_rss_bytes": 1_000_000,
                            "peak_cpu_saturation_of_logical_capacity_percent": 25.0,
                            "scenario": scenario,
                        }
                    )
    records.append(
        {"locale": "en", "scenario": "cancellation", "status": "pass", "peak_rss_bytes": 1_000_000}
    )
    records.append(
        {
            "locale": "en",
            "scenario": "unload_restart",
            "status": "pass",
            "peak_rss_bytes": 1_000_000,
        }
    )

    status, failures, metrics = runner._status(records, config, artifact_bytes=1_000_000)

    assert status == "pass"
    assert failures == []
    assert metrics["process-cold"]["ttft_p95_ms"] == 1.0
    assert metrics["peak_cpu_saturation_of_logical_capacity_percent"] == 25.0
    assert config["acceptance"]["swap"].endswith("acceptance result.")

    status, failures, _metrics = runner._status(records, config, artifact_bytes=3 * 1024**3)
    assert status == "fail"
    assert "resource:artifact_disk" in failures


def test_selection_attempt_counts_do_not_expand_to_the_superseded_full_matrix() -> None:
    counts = _config()["protocol"]

    assert runner._attempt_count(counts, "process-cold", "first_answer", False) == 1
    assert runner._attempt_count(counts, "warm", "first_answer", False) == 2
    assert runner._attempt_count(counts, "warm", "follow_up", False) == 1
    assert runner._attempt_count(counts, "warm", "first_answer", True) == 0


def test_raw_records_durably_include_lifecycle_batches(tmp_path: Path) -> None:
    raw = runner.RawRecords(tmp_path / "raw-records.jsonl")
    raw.extend([{"scenario": "cancellation"}, {"scenario": "unload_restart"}])

    final_path = raw.promote()

    assert [json.loads(line) for line in final_path.read_text(encoding="utf-8").splitlines()] == [
        {"scenario": "cancellation"},
        {"scenario": "unload_restart"},
    ]


def test_raw_records_do_not_overwrite_a_quarantined_partial_run(tmp_path: Path) -> None:
    final_path = tmp_path / "raw-records.jsonl"
    final_path.with_suffix(".partial.jsonl").write_text('{"partial": true}\n', encoding="utf-8")

    with pytest.raises(runner.BenchmarkError, match="quarantined"):
        runner.RawRecords(final_path)


def test_clean_warm_session_replaces_a_stalled_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[FakeSession] = []

    class FakeSession:
        def __init__(self, *_args: object) -> None:
            self.index = len(created)
            self.closed_forcefully = False
            created.append(self)

        def ask(self, _prompt: str) -> dict[str, object]:
            return {}

        def clear(self, *, timeout_s: float = 30) -> None:
            assert timeout_s == 10
            if self.index == 0:
                raise runner.BenchmarkError("llama-cli clear prompt timed out")

        def close(self, *, force: bool = False) -> int:
            self.closed_forcefully = force
            return 0

    monkeypatch.setattr(runner, "CliSession", FakeSession)
    config = {"protocol": {"warm_session_reset": {"clear_timeout_seconds": 10, "retries": 2}}}

    request = {"dialogue_turns": [], "context_jsonl": "", "query": "test"}
    session, restart_count = runner._start_clean_warm_session(
        Path("runtime"), Path("model"), config, request
    )

    assert session is created[1]
    assert restart_count == 1
    assert created[0].closed_forcefully is True


def test_cli_prompt_is_one_physical_stdin_line_with_escaped_untrusted_newlines() -> None:
    prompt = runner._prompt(
        {
            "dialogue_turns": [{"role": "user", "content": "first\nsecond"}],
            "context_jsonl": '{"text":"line one\\nline two"}',
            "query": "question\nwith newline",
        }
    )

    assert "\n" not in prompt
    assert "\r" not in prompt
    assert prompt.endswith(" /no_think")
    payload = json.loads(prompt.removeprefix("BPM_CHAT_REQUEST_JSON=").removesuffix(" /no_think"))
    assert payload["prior_dialogue"][0]["content"] == "first\nsecond"
    assert payload["user_question"] == "question\nwith newline"


def test_cli_prompt_reader_ignores_an_embedded_markdown_quote_marker() -> None:
    session = object.__new__(runner.CliSession)
    session._output = queue.Queue()
    session.process = SimpleNamespace(poll=lambda: None)
    for character in "answer\n> quoted text\nactual prompt\n> ":
        session._output.put(character)

    received = session._wait_for_prompt(timeout_s=1, operation="clear")

    assert received == "answer\n> quoted text\nactual prompt"
