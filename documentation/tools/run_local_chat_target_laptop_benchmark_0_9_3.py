"""Measure the checksum-pinned local chat candidates on the BPM 0.9.3 target laptop.

The runner starts only a direct, offline ``llama-cli`` child process. It writes raw timing/resource
records and a deterministic summary under the ignored M6-03 cache; it is not a production worker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import queue
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/local-chat-target-laptop-benchmark-0.9.3.json"
TOOLS_ROOT = Path(__file__).resolve().parent

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import run_grounded_answer_benchmark_0_9_3 as grounded  # noqa: E402

RUNTIME_THROUGHPUT = re.compile(r"\[ Prompt:\s*([0-9.]+) t/s \| Generation:\s*([0-9.]+) t/s \]")


class BenchmarkError(RuntimeError):
    """Raised when measurement would be incomplete, incomparable, or unsafe."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkError(f"invalid JSON input: {path}") from error
    if not isinstance(value, dict):
        raise BenchmarkError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        values = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
        ]
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkError(f"invalid JSON Lines input: {path}") from error
    if any(not isinstance(value, dict) for value in values):
        raise BenchmarkError(f"JSON Lines object required: {path}")
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _cache_path(path: Path) -> None:
    cache_root = (DOCUMENTATION_ROOT / ".cache").resolve()
    resolved = path.resolve()
    if cache_root not in (resolved, *resolved.parents):
        raise BenchmarkError("M6-03 benchmark artifacts must remain under documentation/.cache")


def _verify_pins(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, pin in config["pins"].items():
        path = REPOSITORY_ROOT / pin["path"]
        if _sha256(path) != pin["sha256"]:
            raise BenchmarkError(f"{name} contract drifted")
        if path.suffix == ".json":
            result[name] = _read_json(path)
    return result


def _memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        name, value, *_ = line.split()
        values[name.rstrip(":")] = int(value) * 1024
    return {
        "memory_total_bytes": values["MemTotal"],
        "memory_available_bytes": values["MemAvailable"],
        "swap_total_bytes": values["SwapTotal"],
        "swap_free_bytes": values["SwapFree"],
        "swap_used_bytes": values["SwapTotal"] - values["SwapFree"],
    }


def _host_fingerprint() -> dict[str, Any]:
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8")
    models = [
        line.split(":", 1)[1].strip()
        for line in cpuinfo.splitlines()
        if line.startswith("model name")
    ]
    physical = {
        (block.get("physical id", "0"), block.get("core id", "0"))
        for block in (
            {
                key.strip(): value.strip()
                for key, value in (
                    line.split(":", 1) for line in section.splitlines() if ":" in line
                )
            }
            for section in cpuinfo.strip().split("\n\n")
        )
    }
    return {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "cpu_model": models[0] if models else "unknown",
        "logical_threads": len(models),
        "physical_cores": len(physical),
        "memory": _memory_snapshot(),
    }


def _validate_host(config: dict[str, Any]) -> dict[str, Any]:
    host = _host_fingerprint()
    expected = config["target_host"]
    for field in ("cpu_model", "architecture", "physical_cores", "logical_threads"):
        if host[field] != expected[field]:
            raise BenchmarkError(f"target host mismatch: {field}")
    return host


def _directory_bytes(path: Path) -> int:
    return sum(
        item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink()
    )


def _candidate(shortlist: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    matches = [item for item in shortlist["admitted_models"] if item["id"] == candidate_id]
    if len(matches) != 1:
        raise BenchmarkError("candidate is not admitted by the M6-01 shortlist")
    return matches[0]


def _validate_artifacts(candidate: dict[str, Any], runtime_path: Path, model_path: Path) -> None:
    if not runtime_path.is_file() or runtime_path.is_symlink() or runtime_path.name != "llama-cli":
        raise BenchmarkError("verified llama-cli executable is required")
    if not os.access(runtime_path, os.X_OK):
        raise BenchmarkError("llama-cli is not executable")
    if (
        not model_path.is_file()
        or model_path.is_symlink()
        or model_path.name != candidate["artifact"]["filename"]
    ):
        raise BenchmarkError("candidate GGUF path is invalid")
    if (
        model_path.stat().st_size != candidate["artifact"]["byte_count"]
        or _sha256(model_path) != candidate["artifact"]["sha256"]
    ):
        raise BenchmarkError("candidate GGUF integrity mismatch")


def _validate_retrieval_artifacts(e5_model_dir: Path, retrieval_root: Path) -> None:
    if not e5_model_dir.is_dir() or e5_model_dir.is_symlink():
        raise BenchmarkError("checksum-verified E5-base model directory is required")
    if not retrieval_root.is_dir() or retrieval_root.is_symlink():
        raise BenchmarkError("active exact-generation root is required")
    pointer = retrieval_root / "active-generation.json"
    if not pointer.is_file() or pointer.is_symlink():
        raise BenchmarkError("active exact-generation pointer is missing")
    generation_id = _read_json(pointer).get("generation_id")
    manifest = retrieval_root / "generations" / str(generation_id) / "generation-manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise BenchmarkError("active exact-generation manifest is missing")


def _load_workload(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    manifest_path = root / "workload-manifest.json"
    request_path = root / "requests.jsonl"
    oracle_path = root / "oracle.jsonl"
    manifest = _read_json(manifest_path)
    if manifest.get("backlog_item") != "BPM093-M6-02":
        raise BenchmarkError("M6-03 requires an M6-02 workload")
    if manifest.get("requests_sha256") != _sha256(request_path) or manifest.get(
        "oracle_sha256"
    ) != _sha256(oracle_path):
        raise BenchmarkError("workload artifact hash drifted")
    requests = _read_jsonl(request_path)
    oracle = _read_jsonl(oracle_path)
    if any(not isinstance(record.get("request_id"), str) for record in requests + oracle):
        raise BenchmarkError("workload identity is incomplete")
    requests_by_id: dict[str, dict[str, Any]] = {
        record["request_id"]: record for record in requests
    }
    oracle_by_id: dict[str, dict[str, Any]] = {record["request_id"]: record for record in oracle}
    if len(requests_by_id) != len(requests) or set(requests_by_id) != set(oracle_by_id):
        raise BenchmarkError("workload identity is incomplete")
    locales = config["protocol"]["locale_order"]
    if manifest.get("locale_case_counts") != {locale: 32 for locale in locales}:
        raise BenchmarkError("workload is not the frozen 32-case six-locale corpus")
    return manifest, requests_by_id, oracle_by_id


def build_workload_from_reviewed_chunks(
    chunks_path: Path, output_root: Path, config_path: Path = CONFIG_PATH
) -> dict[str, Any]:
    """Freeze small, citable same-locale evidence packets for lifecycle measurement.

    M6-03 compares chat generation, not retrieval relevance. Every answer packet therefore uses one
    already-reviewed chunk from the frozen M5 source snapshot, selected by the corpus's expected
    topic, while terminal cases remain pre-inference. The later M7 service owns live retrieval.
    """

    _cache_path(output_root)
    config = _read_json(config_path)
    _verify_pins(config)
    chunks = _read_json(chunks_path)
    if chunks.get("chunk_schema_version") != "rag-chunk-v1" or not isinstance(
        chunks.get("chunks"), list
    ):
        raise BenchmarkError("a complete reviewed rag-chunk-v1 manifest is required")
    harness_config_path = REPOSITORY_ROOT / config["pins"]["grounded_answer_harness"]["path"]
    harness_config = _read_json(harness_config_path)
    corpus = _read_json(REPOSITORY_ROOT / harness_config["pins"]["evaluation_corpus"]["path"])
    cases = grounded._oracle_cases(corpus, harness_config)
    by_topic_locale: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks["chunks"]:
        if not isinstance(chunk, dict):
            raise BenchmarkError("reviewed chunk is malformed")
        locale = chunk.get("locale")
        topic = chunk.get("topic_id")
        if (
            isinstance(locale, str)
            and locale in config["protocol"]["locale_order"]
            and isinstance(topic, str)
        ):
            by_topic_locale[(locale, topic)].append(chunk)
    evidence: list[dict[str, Any]] = []
    for case in cases:
        citations = case["expected_citation_ids"]
        if case["expected_disposition"] == "answer":
            topic_id = citations[0].removeprefix("topic:")
            candidates = by_topic_locale.get((case["locale"], topic_id), [])
            if not candidates:
                raise BenchmarkError(f"{case['locale']}: reviewed evidence topic is unavailable")
            chunk = min(
                candidates,
                key=lambda item: (len(str(item.get("text", ""))), str(item.get("chunk_id", ""))),
            )
            context = {
                "citation_id": citations[0],
                "published_url": chunk["published_url"],
                "topic_id": topic_id,
                "anchor_id_or_root": chunk["anchor_id_or_root"],
                "source_kind": "local",
                "text": chunk["text"],
            }
            context_jsonl = _canonical_json(context).rstrip("\n")
        else:
            context_jsonl = ""
            citations = []
        dialogue_turns = (
            [{"role": "user", "content": f"I need BPM help about {case['query']}"}]
            if case["requires_dialogue"]
            else []
        )
        evidence.append(
            {
                "request_id": case["request_id"],
                "locale": case["locale"],
                "evidence_disposition": case["expected_disposition"],
                "context_jsonl": context_jsonl,
                "citation_ids": citations,
                "dialogue_turns": dialogue_turns,
                "model_invocation_count": 0,
            }
        )
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_path = output_root / "prepared-evidence.jsonl"
    grounded._write_jsonl(evidence_path, evidence)
    print(
        "M6-03: frozen reviewed evidence packets; building candidate-neutral workload", flush=True
    )
    return grounded.build_workload(evidence_path, output_root, harness_config_path)


def _request_for(
    requests: dict[str, dict[str, Any]], oracle: dict[str, dict[str, Any]], locale: str, kind: str
) -> dict[str, Any]:
    matches = [
        requests[request_id]
        for request_id, entry in oracle.items()
        if entry.get("locale") == locale
        and entry.get("case_kind") == kind
        and entry.get("expected_disposition") == "answer"
    ]
    if not matches:
        raise BenchmarkError(f"{locale}: workload has no {kind} answer")
    return matches[0]


def _prompt(request: dict[str, Any]) -> str:
    # ``llama-cli --simple-io`` reads exactly one stdin line for one turn. Keep all user-controlled
    # text inside a canonical JSON string so embedded newlines cannot become unscheduled turns.
    payload = {
        "instruction": (
            "Answer only BPM documentation questions using local evidence. Do not invent facts. "
            "Cite applicable citation IDs literally in square brackets. Do not expose reasoning."
        ),
        "local_evidence_jsonl": request["context_jsonl"],
        "prior_dialogue": request["dialogue_turns"],
        "user_question": request["query"],
    }
    return f"BPM_CHAT_REQUEST_JSON={_canonical_json(payload)} /no_think"


def _children(pid: int) -> set[int]:
    result = {pid}
    pending = [pid]
    while pending:
        current = pending.pop()
        path = Path(f"/proc/{current}/task/{current}/children")
        if not path.is_file():
            continue
        for value in path.read_text(encoding="utf-8").split():
            child = int(value)
            if child not in result:
                result.add(child)
                pending.append(child)
    return result


def _rss_bytes(pid: int) -> int:
    total = 0
    for child in _children(pid):
        status = Path(f"/proc/{child}/status")
        if not status.is_file():
            continue
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                total += int(line.split()[1]) * 1024
                break
    return total


def _cpu_ticks(pid: int) -> int:
    """Return cumulative user+kernel ticks for the direct worker and its children."""

    total = 0
    for child in _children(pid):
        stat = Path(f"/proc/{child}/stat")
        try:
            # ``comm`` may contain spaces and parentheses, so split only after its final ')'.
            fields = stat.read_text(encoding="utf-8").rsplit(")", 1)[1].split()
            total += int(fields[11]) + int(fields[12])  # proc fields 14 (utime) and 15 (stime)
        except IndexError, OSError, ValueError:
            continue
    return total


class RssSampler:
    def __init__(self, pid: int, interval_ms: int) -> None:
        self._pid = pid
        self._interval = interval_ms / 1000
        self._running = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self.samples: list[int] = []
        self.cpu_saturation_of_logical_capacity_percent: list[float] = []
        self._last_cpu_sample: tuple[float, int] | None = None

    def _sample(self) -> None:
        while self._running.is_set():
            self.samples.append(_rss_bytes(self._pid))
            now = time.monotonic()
            ticks = _cpu_ticks(self._pid)
            if self._last_cpu_sample is not None:
                previous_time, previous_ticks = self._last_cpu_sample
                elapsed = now - previous_time
                if elapsed > 0:
                    logical_capacity = max(1, os.cpu_count() or 1)
                    used_cores = (ticks - previous_ticks) / os.sysconf("SC_CLK_TCK") / elapsed
                    self.cpu_saturation_of_logical_capacity_percent.append(
                        100 * used_cores / logical_capacity
                    )
            self._last_cpu_sample = (now, ticks)
            time.sleep(self._interval)

    def __enter__(self) -> RssSampler:
        self._running.set()
        self._thread.start()
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self._running.clear()
        self._thread.join(timeout=2)
        self.samples.append(_rss_bytes(self._pid))


def _sampler_peaks(sampler: RssSampler) -> tuple[int, float]:
    return (
        max(sampler.samples, default=0),
        max(sampler.cpu_saturation_of_logical_capacity_percent, default=0.0),
    )


class RawRecords(list[dict[str, Any]]):
    """Append raw facts durably; an interrupted run remains quarantined as ``.partial``."""

    def __init__(self, final_path: Path) -> None:
        super().__init__()
        self._final_path = final_path
        self._partial_path = final_path.with_suffix(".partial.jsonl")
        if self._final_path.exists() or self._partial_path.exists():
            raise BenchmarkError(
                "benchmark output already exists; preserve completed or quarantined raw records in"
                " a new output root"
            )
        self._handle = self._partial_path.open("w", encoding="utf-8")

    def append(self, record: dict[str, Any]) -> None:
        super().append(record)
        self._handle.write(_canonical_json(record) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def extend(self, records: Iterable[dict[str, Any]]) -> None:
        for record in records:
            self.append(record)

    def promote(self) -> Path:
        self._handle.close()
        os.replace(self._partial_path, self._final_path)
        return self._final_path


class CliSession:
    """One direct stdin/stdout llama-cli conversation, with no listener or server."""

    def __init__(self, runtime_path: Path, model_path: Path, config: dict[str, Any]) -> None:
        generation = config["runtime"]["generation"]
        self._output: queue.Queue[str | None] = queue.Queue()
        self.process = subprocess.Popen(
            [
                str(runtime_path),
                "--offline",
                "--model",
                str(model_path),
                "--device",
                "none",
                "--threads",
                str(generation["threads"]),
                "--threads-batch",
                str(generation["threads_batch"]),
                "--ctx-size",
                str(generation["context_tokens"]),
                "--batch-size",
                str(generation["batch_size"]),
                "--ubatch-size",
                str(generation["ubatch_size"]),
                "--n-predict",
                str(generation["output_tokens_max"]),
                "--temperature",
                str(generation["temperature"]),
                "--top-p",
                str(generation["top_p"]),
                "--top-k",
                str(generation["top_k"]),
                "--seed",
                str(generation["seed"]),
                "--jinja",
                "--reasoning",
                generation["reasoning"],
                "--conversation",
                "--simple-io",
                "--no-display-prompt",
                "--show-timings",
                "--log-colors",
                "off",
                "--log-verbosity",
                "1",
                "--no-warmup",
                "--system-prompt",
                (
                    "You are the BPM documentation assistant. Follow the user only within BPM"
                    " documentation."
                ),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self.process.stdout is not None
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()
        self.started_ns = time.monotonic_ns()
        self._wait_for_prompt(timeout_s=120, operation="readiness")
        self.ready_ns = time.monotonic_ns()

    def _read(self) -> None:
        assert self.process.stdout is not None
        while True:
            character = self.process.stdout.read(1)
            if not character:
                self._output.put(None)
                return
            self._output.put(character)

    def _has_idle_prompt(self, received: str) -> tuple[bool, str]:
        """Distinguish the CLI prompt from a Markdown quote generated by the model."""

        if not received.endswith("\n> "):
            return False, received
        try:
            following = self._output.get(timeout=0.05)
        except queue.Empty:
            return True, received
        if following is None:
            return True, received
        return False, received + following

    def _wait_for_prompt(self, timeout_s: float, *, operation: str) -> str:
        deadline = time.monotonic() + timeout_s
        received = ""
        while time.monotonic() < deadline:
            try:
                character = self._output.get(timeout=0.1)
            except queue.Empty as error:
                if self.process.poll() is not None:
                    raise BenchmarkError("llama-cli exited before becoming ready") from error
                continue
            if character is None:
                raise BenchmarkError("llama-cli output ended before ready prompt")
            received += character
            has_prompt, received = self._has_idle_prompt(received)
            if has_prompt:
                return received.removesuffix("\n> ")
        raise BenchmarkError(f"llama-cli {operation} prompt timed out")

    def ask(self, prompt: str, *, cancel_at_first_token: bool = False) -> dict[str, Any]:
        if self.process.stdin is None:
            raise BenchmarkError("llama-cli stdin is unavailable")
        started = time.monotonic_ns()
        self.process.stdin.write(prompt + "\n")
        self.process.stdin.flush()
        received = ""
        first_token_ns: int | None = None
        cancellation_ns: int | None = None
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            try:
                character = self._output.get(timeout=0.1)
            except queue.Empty as error:
                if self.process.poll() is not None:
                    raise BenchmarkError("llama-cli exited while answering") from error
                continue
            if character is None:
                raise BenchmarkError("llama-cli output ended while answering")
            received += character
            if first_token_ns is None and not character.isspace() and character != ">":
                first_token_ns = time.monotonic_ns()
                if cancel_at_first_token:
                    self.process.send_signal(signal.SIGINT)
                    cancellation_ns = time.monotonic_ns()
            has_prompt, received = self._has_idle_prompt(received)
            if has_prompt:
                completed = time.monotonic_ns()
                body = received.removesuffix("\n> ")
                throughput_match = RUNTIME_THROUGHPUT.search(body)
                return {
                    "answer_text": body[: throughput_match.start()] if throughput_match else body,
                    "ttft_ns": (first_token_ns or completed) - started,
                    "completion_ns": completed - started,
                    "prompt_ingestion_tokens_per_second": (
                        float(throughput_match.group(1)) if throughput_match else None
                    ),
                    "decoded_tokens_per_second": (
                        float(throughput_match.group(2)) if throughput_match else None
                    ),
                    "cancel_requested_ns": cancellation_ns,
                    "prompt_bytes": len(prompt.encode("utf-8")),
                }
        raise BenchmarkError("llama-cli response timed out")

    def clear(self, *, timeout_s: float = 30) -> None:
        if self.process.stdin is None:
            raise BenchmarkError("llama-cli stdin is unavailable")
        self.process.stdin.write("/clear\n")
        self.process.stdin.flush()
        self._wait_for_prompt(timeout_s=timeout_s, operation="clear")

    def close(self, *, force: bool = False) -> int:
        if force and self.process.poll() is None:
            self.process.terminate()
            try:
                return self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                return self.process.wait(timeout=5)
        if self.process.poll() is None and self.process.stdin is not None:
            self.process.stdin.write("/exit\n")
            self.process.stdin.flush()
        try:
            return self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                return self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                return self.process.wait(timeout=5)


def _nearest_p95(samples: list[int]) -> float:
    return sorted(samples)[max(0, (95 * len(samples) + 99) // 100 - 1)] / 1_000_000


def _sample_record(
    *,
    candidate_id: str,
    locale: str,
    state: str,
    scenario: str,
    attempt: int,
    warmup: bool,
    sample: dict[str, Any],
    rss_bytes: int,
    cpu_saturation_of_logical_capacity_percent: float,
) -> dict[str, Any]:
    throughput = sample["decoded_tokens_per_second"]
    return {
        "candidate_id": candidate_id,
        "locale": locale,
        "state": state,
        "scenario": scenario,
        "attempt": attempt,
        "warmup": warmup,
        **sample,
        "tokens_per_second": throughput,
        "peak_rss_bytes": rss_bytes,
        "peak_cpu_saturation_of_logical_capacity_percent": (
            cpu_saturation_of_logical_capacity_percent
        ),
        "network_calls": 0,
    }


def _attempt_count(counts: dict[str, Any], state: str, scenario: str, warmup: bool) -> int:
    if warmup:
        return counts["warmup_attempts_per_locale_state_scenario"]
    return counts["selection_sample_counts"][state][scenario]


def _start_clean_warm_session(
    runtime_path: Path, model_path: Path, config: dict[str, Any], prime: dict[str, Any]
) -> tuple[CliSession, int]:
    """Start a loaded session with no retained benchmark dialogue.

    Some direct ``llama-cli`` sessions can stop printing a prompt after ``/clear``. A replacement
    remains sequential and is primed then cleared before any later warm sample is timed, so the
    measured response is still from a loaded model with no prior benchmark conversation.
    """

    reset = config["protocol"]["warm_session_reset"]
    last_error: BenchmarkError | None = None
    for restart_count in range(reset["retries"] + 1):
        session = CliSession(runtime_path, model_path, config)
        try:
            session.ask(_prompt(prime))
            session.clear(timeout_s=reset["clear_timeout_seconds"])
            return session, restart_count
        except BenchmarkError as error:
            last_error = error
            session.close(force=True)
    raise BenchmarkError(
        "llama-cli could not establish a clean warm session after stalled /clear recovery"
    ) from last_error


def _run_cold(
    runtime_path: Path,
    model_path: Path,
    config: dict[str, Any],
    request: dict[str, Any],
    candidate_id: str,
    locale: str,
    raw: RawRecords,
) -> None:
    counts = config["protocol"]
    prompt = _prompt(request)
    for warmup in (True, False):
        total = _attempt_count(counts, "process-cold", "first_answer", warmup)
        for attempt in range(1, total + 1):
            session = CliSession(runtime_path, model_path, config)
            with RssSampler(session.process.pid, counts["rss_sample_interval_ms"]) as sampler:
                sample = session.ask(prompt)
            exit_code = session.close(force=True)
            sample["startup_ns"] = session.ready_ns - session.started_ns
            sample["exit_code"] = exit_code
            rss_bytes, cpu_saturation = _sampler_peaks(sampler)
            raw.append(
                _sample_record(
                    candidate_id=candidate_id,
                    locale=locale,
                    state="process-cold",
                    scenario="first_answer",
                    attempt=attempt,
                    warmup=warmup,
                    sample=sample,
                    rss_bytes=rss_bytes,
                    cpu_saturation_of_logical_capacity_percent=cpu_saturation,
                )
            )
            if not warmup and (
                attempt % config["progress"]["measured_sample_update"] == 0 or attempt == total
            ):
                print(
                    f"M6-03: {candidate_id} {locale} process-cold first_answer: {attempt}/{total}"
                    " measured",
                    flush=True,
                )


def _run_warm(
    runtime_path: Path,
    model_path: Path,
    config: dict[str, Any],
    first: dict[str, Any],
    follow_up: dict[str, Any],
    candidate_id: str,
    locale: str,
    scenario: str,
    raw: RawRecords,
) -> None:
    counts = config["protocol"]
    session: CliSession | None = None
    warm_session_restart_count = 0
    try:
        session, initial_restarts = _start_clean_warm_session(
            runtime_path, model_path, config, first
        )
        warm_session_restart_count += initial_restarts
        for warmup in (True, False):
            total = _attempt_count(counts, "warm", scenario, warmup)
            for attempt in range(1, total + 1):
                if scenario == "follow_up":
                    session.ask(_prompt(first))
                with RssSampler(session.process.pid, counts["rss_sample_interval_ms"]) as sampler:
                    sample = session.ask(_prompt(follow_up if scenario == "follow_up" else first))
                rss_bytes, cpu_saturation = _sampler_peaks(sampler)
                sample["warm_session_restart_count"] = warm_session_restart_count
                raw.append(
                    _sample_record(
                        candidate_id=candidate_id,
                        locale=locale,
                        state="warm",
                        scenario=scenario,
                        attempt=attempt,
                        warmup=warmup,
                        sample=sample,
                        rss_bytes=rss_bytes,
                        cpu_saturation_of_logical_capacity_percent=cpu_saturation,
                    )
                )
                try:
                    session.clear(timeout_s=counts["warm_session_reset"]["clear_timeout_seconds"])
                except BenchmarkError:
                    session.close(force=True)
                    session, restart_count = _start_clean_warm_session(
                        runtime_path, model_path, config, first
                    )
                    warm_session_restart_count += 1 + restart_count
                    print(
                        f"M6-03: {candidate_id} {locale} warm {scenario}: replaced session after"
                        " stalled /clear",
                        flush=True,
                    )
                if not warmup and (
                    attempt % config["progress"]["measured_sample_update"] == 0 or attempt == total
                ):
                    print(
                        f"M6-03: {candidate_id} {locale} warm {scenario}: {attempt}/{total}"
                        " measured",
                        flush=True,
                    )
    finally:
        if session is not None:
            session.close(force=True)


def _lifecycle_records(
    runtime_path: Path,
    model_path: Path,
    config: dict[str, Any],
    first: dict[str, Any],
    oracle: dict[str, dict[str, Any]],
    candidate_id: str,
    locale: str,
) -> list[dict[str, Any]]:
    terminal = [
        entry
        for entry in oracle.values()
        if entry["locale"] == locale and entry["expected_disposition"] != "answer"
    ]
    records: list[dict[str, Any]] = [
        {
            "candidate_id": candidate_id,
            "locale": locale,
            "state": "pre-inference",
            "scenario": "abstain_refuse",
            "terminal_case_count": len(terminal),
            "model_invocations": 0,
            "network_calls": 0,
            "status": "pass",
        }
    ]
    session = CliSession(runtime_path, model_path, config)
    try:
        with RssSampler(
            session.process.pid, config["protocol"]["rss_sample_interval_ms"]
        ) as sampler:
            sample = session.ask(_prompt(first), cancel_at_first_token=True)
    finally:
        cancelled_exit_code = session.close()

    recovered = False
    recovery_exit_code: int | None = None
    recovery_session: CliSession | None = None
    try:
        recovery_session = CliSession(runtime_path, model_path, config)
        recovery_session.ask(_prompt(first))
        recovered = True
    except BenchmarkError:
        recovered = False
    finally:
        if recovery_session is not None:
            recovery_exit_code = recovery_session.close()

    unload_session = CliSession(runtime_path, model_path, config)
    unload_exit_code = unload_session.close()

    records.append(
        {
            "candidate_id": candidate_id,
            "locale": locale,
            "state": "warm",
            "scenario": "cancellation",
            "cancel_requested_ns": sample["cancel_requested_ns"],
            "completion_ns": sample["completion_ns"],
            "peak_rss_bytes": _sampler_peaks(sampler)[0],
            "peak_cpu_saturation_of_logical_capacity_percent": _sampler_peaks(sampler)[1],
            "cancelled_worker_exit_code": cancelled_exit_code,
            "recovered_by_restart": recovered,
            "recovery_exit_code": recovery_exit_code,
            "network_calls": 0,
            "status": "pass" if sample["cancel_requested_ns"] and recovered else "fail",
        }
    )
    records.append(
        {
            "candidate_id": candidate_id,
            "locale": locale,
            "state": "process-cold",
            "scenario": "unload_restart",
            "exit_code": unload_exit_code,
            "remaining_processes": (
                len(_children(unload_session.process.pid))
                if Path(f"/proc/{unload_session.process.pid}").exists()
                else 0
            ),
            "network_calls": 0,
            "status": "pass" if unload_exit_code == 0 else "fail",
        }
    )
    return records


def _status(
    raw: list[dict[str, Any]], config: dict[str, Any], artifact_bytes: int
) -> tuple[str, list[str], dict[str, Any]]:
    acceptance = config["acceptance"]
    measured = [record for record in raw if record.get("warmup") is False]
    failures: list[str] = []
    metrics: dict[str, Any] = {
        "artifact_disk_gib": artifact_bytes / 1024**3,
        "peak_rss_bytes": max(record.get("peak_rss_bytes", 0) for record in raw),
        "peak_cpu_saturation_of_logical_capacity_percent": max(
            record.get("peak_cpu_saturation_of_logical_capacity_percent", 0.0) for record in raw
        ),
    }
    if metrics["artifact_disk_gib"] > acceptance["artifact_disk_gib_max"]:
        failures.append("resource:artifact_disk")
    if metrics["peak_rss_bytes"] / 1024**3 > acceptance["worker_and_retrieval_rss_gib_max"]:
        failures.append("resource:peak_rss")
    selection_counts = config["protocol"]["selection_sample_counts"]
    for locale in config["protocol"]["locale_order"]:
        for state, scenarios in selection_counts.items():
            for scenario, expected_count in scenarios.items():
                actual_count = sum(
                    record.get("locale") == locale
                    and record.get("state") == state
                    and record.get("scenario") == scenario
                    for record in measured
                )
                if actual_count != expected_count:
                    failures.append(f"{locale}:{state}:{scenario}:missing_samples")
    for state, ttft_max in (
        ("process-cold", acceptance["cold_ttft_p95_ms_max"]),
        ("warm", acceptance["warm_ttft_p95_ms_max"]),
    ):
        subset = [record for record in measured if record["state"] == state]
        if not subset:
            failures.append(f"{state}:missing_samples")
            continue
        ttft = _nearest_p95([record["ttft_ns"] for record in subset])
        completion = _nearest_p95([record["completion_ns"] for record in subset])
        throughputs = [
            record["tokens_per_second"]
            for record in subset
            if record["tokens_per_second"] is not None
        ]
        metrics[state] = {
            "ttft_p95_ms": ttft,
            "completion_p95_ms": completion,
            "throughput_median_tokens_per_second": (
                statistics.median(throughputs) if throughputs else None
            ),
        }
        for record in subset:
            if record["ttft_ns"] / 1_000_000 > ttft_max:
                failures.append(f"{record['locale']}:{state}:ttft")
            if record["completion_ns"] / 1_000_000 > acceptance["completion_p95_ms_max"]:
                failures.append(f"{record['locale']}:{state}:completion")
            if (
                record["tokens_per_second"] is None
                or record["tokens_per_second"]
                < acceptance["throughput_median_tokens_per_second_min"]
            ):
                failures.append(f"{record['locale']}:{state}:throughput")
    if any(
        record.get("status") == "fail"
        for record in raw
        if record.get("scenario") in config["protocol"]["lifecycle_scenarios"]
    ):
        failures.append("lifecycle")
    return ("pass" if not failures else "fail"), failures, metrics


def run_candidate(
    candidate_id: str,
    runtime_path: Path,
    model_path: Path,
    e5_model_dir: Path,
    retrieval_root: Path,
    workload_root: Path,
    output_root: Path,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    """Run the accepted compact M2 comparative-selection matrix for one candidate."""

    _cache_path(output_root)
    config = _read_json(config_path)
    pinned = _verify_pins(config)
    host = _validate_host(config)
    candidate = _candidate(pinned["runtime_shortlist"], candidate_id)
    _validate_artifacts(candidate, runtime_path, model_path)
    _validate_retrieval_artifacts(e5_model_dir, retrieval_root)
    workload, requests, oracle = _load_workload(workload_root, config)
    output_root.mkdir(parents=True, exist_ok=True)
    raw = RawRecords(output_root / "raw-records.jsonl")
    print(f"M6-03: verified {candidate_id}; beginning target-laptop measurements", flush=True)
    lifecycle_locale = config["protocol"]["lifecycle_locale"]
    for locale in config["protocol"]["locale_order"]:
        first = _request_for(requests, oracle, locale, "answer_question")
        follow_up = _request_for(requests, oracle, locale, "dialogue")
        if locale == lifecycle_locale:
            print(f"M6-03: {candidate_id} {locale}: lifecycle checks", flush=True)
            raw.extend(
                _lifecycle_records(
                    runtime_path, model_path, config, first, oracle, candidate_id, locale
                )
            )
        print(f"M6-03: {candidate_id} {locale}: comparative selection samples", flush=True)
        _run_cold(runtime_path, model_path, config, first, candidate_id, locale, raw)
        _run_warm(
            runtime_path,
            model_path,
            config,
            first,
            follow_up,
            candidate_id,
            locale,
            "first_answer",
            raw,
        )
        _run_warm(
            runtime_path,
            model_path,
            config,
            first,
            follow_up,
            candidate_id,
            locale,
            "follow_up",
            raw,
        )
    artifact_bytes = (
        model_path.stat().st_size
        + _directory_bytes(runtime_path.parent)
        + _directory_bytes(e5_model_dir)
        + _directory_bytes(retrieval_root)
    )
    status, failures, metrics = _status(raw, config, artifact_bytes)
    report = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "benchmark_contract_sha256": _sha256(config_path),
        "candidate_id": candidate_id,
        "candidate_artifact_sha256": _sha256(model_path),
        "runtime_path": str(runtime_path),
        "runtime_revision": pinned["runtime_shortlist"]["runtime"]["revision"],
        "e5_model_dir": str(e5_model_dir),
        "active_retrieval_root": str(retrieval_root),
        "workload_manifest_sha256": _sha256(workload_root / "workload-manifest.json"),
        "host": host,
        "swap": {
            "before": host["memory"]["swap_used_bytes"],
            "after": _memory_snapshot()["swap_used_bytes"],
            "release_condition": "diagnostic_only",
        },
        "raw_record_count": len(raw),
        "metrics": metrics,
        "status": status,
        "failures": failures,
        "boundaries": {
            "network_calls": 0,
            "ordinary_search_calls": 0,
            "cross_locale_retrieval_calls": 0,
            "one_active_conversation": True,
        },
    }
    raw_path = raw.promote()
    report["raw_records_sha256"] = _sha256(raw_path)
    (output_root / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"M6-03: {candidate_id}: complete; status={status}", flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-workload")
    build.add_argument("--chunks", required=True, type=Path)
    build.add_argument("--output-root", required=True, type=Path)
    build.add_argument("--config", default=CONFIG_PATH, type=Path)
    run = commands.add_parser("run")
    run.add_argument("--candidate", required=True)
    run.add_argument("--runtime", required=True, type=Path)
    run.add_argument("--model", required=True, type=Path)
    run.add_argument("--e5-model-dir", required=True, type=Path)
    run.add_argument("--retrieval-root", required=True, type=Path)
    run.add_argument("--workload-root", required=True, type=Path)
    run.add_argument("--output-root", required=True, type=Path)
    run.add_argument("--config", default=CONFIG_PATH, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build-workload":
            build_workload_from_reviewed_chunks(args.chunks, args.output_root, args.config)
        else:
            run_candidate(
                args.candidate,
                args.runtime,
                args.model,
                args.e5_model_dir,
                args.retrieval_root,
                args.workload_root,
                args.output_root,
                args.config,
            )
    except BenchmarkError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
