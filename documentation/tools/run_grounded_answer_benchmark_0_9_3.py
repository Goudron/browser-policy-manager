"""Build and score candidate-neutral grounded-answer benchmark artifacts for BPM 0.9.3.

This documentation-only tool neither downloads nor starts a model. It turns prepared local
EvidencePack-shaped records into byte-identical candidate request packets, then validates raw
candidate responses and mandatory human review. All produced artifacts are ignored local evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/grounded-answer-benchmark-harness-0.9.3.json"


class HarnessError(RuntimeError):
    """Raised for an incomplete, incomparable, or unsafe benchmark artifact."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HarnessError(f"invalid JSON input: {path}") from error
    if not isinstance(value, dict):
        raise HarnessError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as error:
        raise HarnessError(f"invalid JSON Lines input: {path}") from error
    if any(not isinstance(record, dict) for record in records):
        raise HarnessError(f"JSON Lines object required: {path}")
    return records


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(value))


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_canonical_json(value) for value in values))


def _verify_pins(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pinned: dict[str, dict[str, Any]] = {}
    for name, entry in config["pins"].items():
        path = REPOSITORY_ROOT / entry["path"]
        if _sha256(path) != entry["sha256"]:
            raise HarnessError(f"{name} contract drifted")
        pinned[name] = _read_json(path)
    return pinned["model_runtime_shortlist"], pinned["evaluation_corpus"]


def _case_id(locale: str, kind: str, identifier: str) -> str:
    return f"{locale}:{kind}:{identifier}"


def _oracle_cases(corpus: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    locales = config["locales"]
    if corpus.get("locales") != locales:
        raise HarnessError("evaluation corpus locale set drifted")
    topic_by_corpus_citation = {domain["citation_id"]: domain["topic_id"] for domain in corpus["domains"]}
    cases: list[dict[str, Any]] = []
    for locale in locales:
        answer_count = 0
        terminal_counts: dict[str, int] = defaultdict(int)
        for domain in corpus["domains"]:
            term = domain["terms"][locale][0]
            for ordinal, template in enumerate(corpus["answer_templates"][locale]):
                cases.append(
                    {
                        "request_id": _case_id(locale, "answer", f"{domain['id']}:{ordinal}"),
                        "locale": locale,
                        "case_kind": "answer_question",
                        "query": template.format(term=term),
                        "expected_disposition": "answer",
                        "expected_citation_ids": [f"topic:{domain['topic_id']}"],
                        "requires_dialogue": False,
                    }
                )
                answer_count += 1
        for case_id, query, disposition in corpus["boundary_cases"][locale]["search"]:
            cases.append(
                {
                    "request_id": _case_id(locale, "search", case_id),
                    "locale": locale,
                    "case_kind": "boundary_search",
                    "query": query,
                    "expected_disposition": disposition,
                    "expected_citation_ids": [],
                    "requires_dialogue": False,
                }
            )
            if disposition != "answer":
                terminal_counts[disposition] += 1
        for case_id, query, disposition, citation_id in corpus["boundary_cases"][locale]["dialogue"]:
            cases.append(
                {
                    "request_id": _case_id(locale, "dialogue", case_id),
                    "locale": locale,
                    "case_kind": "dialogue",
                    "query": query,
                    "expected_disposition": disposition,
                    "expected_citation_ids": [f"topic:{topic_by_corpus_citation[citation_id]}"] if disposition == "answer" else [],
                    "requires_dialogue": True,
                }
            )
            if disposition == "answer":
                answer_count += 1
            else:
                terminal_counts[disposition] += 1
        required_answers = config["workload"]["answer_questions_per_locale"] + config["workload"]["dialogue_answer_cases_per_locale"]
        if answer_count != required_answers:
            raise HarnessError(f"{locale}: answer case count drifted")
        if dict(terminal_counts) != config["workload"]["terminal_cases_per_locale"]:
            raise HarnessError(f"{locale}: terminal case count drifted")
    by_locale: dict[str, int] = defaultdict(int)
    for case in cases:
        by_locale[case["locale"]] += 1
    if any(by_locale[locale] != config["workload"]["total_cases_per_locale"] for locale in locales):
        raise HarnessError("total workload case count drifted")
    return cases


def _evidence_by_request(
    records: list[dict[str, Any]], cases: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    fields = set(config["prepared_evidence_packet"]["required_fields"])
    expected = {case["request_id"]: case for case in cases}
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if set(record) != fields:
            raise HarnessError("prepared evidence packet fields drifted")
        request_id = record["request_id"]
        if request_id not in expected or request_id in result:
            raise HarnessError("prepared evidence request identity is unknown or duplicated")
        case = expected[request_id]
        if record["locale"] != case["locale"] or record["evidence_disposition"] != case["expected_disposition"]:
            raise HarnessError("prepared evidence disposition or locale drifted")
        if (
            not isinstance(record["context_jsonl"], str)
            or not isinstance(record["citation_ids"], list)
            or not all(isinstance(citation, str) for citation in record["citation_ids"])
        ):
            raise HarnessError("prepared evidence content is malformed")
        if not isinstance(record["dialogue_turns"], list) or not isinstance(record["model_invocation_count"], int):
            raise HarnessError("prepared dialogue or invocation count is malformed")
        if record["model_invocation_count"] != 0:
            raise HarnessError("prepared evidence must precede every model invocation")
        if case["expected_disposition"] == "answer":
            if not record["context_jsonl"] or set(case["expected_citation_ids"]) - set(record["citation_ids"]):
                raise HarnessError("answer evidence is not citable and ready")
        elif record["context_jsonl"] or record["citation_ids"]:
            raise HarnessError("terminal evidence must not expose answer context or citations")
        if case["requires_dialogue"] and not record["dialogue_turns"]:
            raise HarnessError("dialogue case lacks locale-native prior turns")
        if not case["requires_dialogue"] and record["dialogue_turns"]:
            raise HarnessError("non-dialogue case unexpectedly has prior turns")
        result[request_id] = record
    if set(result) != set(expected):
        raise HarnessError("prepared evidence does not cover the complete frozen workload")
    return result


def build_workload(evidence_path: Path, output_root: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Build candidate-neutral request and oracle artifacts from prepared evidence packets."""

    print("Grounded-answer benchmark: verifying contracts and prepared evidence", flush=True)
    config = _read_json(config_path)
    shortlist, corpus = _verify_pins(config)
    cases = _oracle_cases(corpus, config)
    evidence = _evidence_by_request(_read_jsonl(evidence_path), cases, config)
    requests: list[dict[str, Any]] = []
    oracle: list[dict[str, Any]] = []
    by_locale: dict[str, int] = defaultdict(int)
    for case in cases:
        packet = evidence[case["request_id"]]
        requests.append(
            {
                "request_id": case["request_id"],
                "locale": case["locale"],
                "query": case["query"],
                "dialogue_turns": packet["dialogue_turns"],
                "context_jsonl": packet["context_jsonl"],
                "generation_settings": config["measurement"]["fixed_generation_settings"],
            }
        )
        oracle.append(
            {
                "request_id": case["request_id"],
                "locale": case["locale"],
                "case_kind": case["case_kind"],
                "expected_disposition": case["expected_disposition"],
                "expected_citation_ids": case["expected_citation_ids"],
                "requires_dialogue": case["requires_dialogue"],
            }
        )
        by_locale[case["locale"]] += 1
        if by_locale[case["locale"]] % config["progress"]["locale_case_update"] == 0:
            print(
                f"Grounded-answer benchmark: {case['locale']}: {by_locale[case['locale']]}/"
                f"{config['workload']['total_cases_per_locale']} workload packets",
                flush=True,
            )
    output_root.mkdir(parents=True, exist_ok=True)
    request_path = output_root / "requests.jsonl"
    oracle_path = output_root / "oracle.jsonl"
    _write_jsonl(request_path, requests)
    _write_jsonl(oracle_path, oracle)
    manifest = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "harness_contract_sha256": _sha256(config_path),
        "shortlist_contract_sha256": config["pins"]["model_runtime_shortlist"]["sha256"],
        "evaluation_corpus_sha256": config["pins"]["evaluation_corpus"]["sha256"],
        "prepared_evidence_sha256": _sha256(evidence_path),
        "requests_sha256": _sha256(request_path),
        "oracle_sha256": _sha256(oracle_path),
        "candidate_ids": [candidate["id"] for candidate in shortlist["admitted_models"]],
        "locale_case_counts": dict(by_locale),
        "ordinary_search_calls": 0,
        "cross_locale_retrieval_calls": 0,
        "network_calls": 0,
        "model_invocations": 0,
    }
    _write_json(output_root / "workload-manifest.json", manifest)
    print("Grounded-answer benchmark: candidate-neutral workload complete", flush=True)
    return manifest


def _load_workload(
    root: Path, config: dict[str, Any], config_path: Path
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest_path = root / "workload-manifest.json"
    requests_path = root / "requests.jsonl"
    oracle_path = root / "oracle.jsonl"
    manifest = _read_json(manifest_path)
    if manifest.get("harness_contract_sha256") != _sha256(config_path):
        raise HarnessError("workload harness contract drifted")
    if manifest.get("requests_sha256") != _sha256(requests_path) or manifest.get("oracle_sha256") != _sha256(oracle_path):
        raise HarnessError("workload request or oracle hash drifted")
    requests = _read_jsonl(requests_path)
    oracle = _read_jsonl(oracle_path)
    if any(not isinstance(record.get("request_id"), str) for record in requests + oracle):
        raise HarnessError("workload case identity is malformed")
    oracle_by_id: dict[str, dict[str, Any]] = {record["request_id"]: record for record in oracle}
    if len(oracle_by_id) != len(oracle) or len(requests) != len(oracle):
        raise HarnessError("workload case identity is malformed")
    if {record["request_id"] for record in requests} != set(oracle_by_id):
        raise HarnessError("workload request and oracle identities drifted")
    admitted = {candidate["id"] for candidate in _verify_pins(config)[0]["admitted_models"]}
    if set(manifest.get("candidate_ids", [])) != admitted:
        raise HarnessError("workload candidate admission drifted")
    return manifest, oracle_by_id


def _response_by_request(
    records: list[dict[str, Any]], candidate_id: str, oracle: dict[str, dict[str, Any]], config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    fields = set(config["candidate_response"]["required_fields"])
    answers = {request_id: entry for request_id, entry in oracle.items() if entry["expected_disposition"] == "answer"}
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if set(record) != fields:
            raise HarnessError("candidate response fields drifted")
        request_id = record["request_id"]
        if record["candidate_id"] != candidate_id or request_id not in answers or request_id in result:
            raise HarnessError("candidate response identity is invalid")
        citations = record["citation_ids"]
        if (
            not isinstance(record["answer_text"], str)
            or "<think" in record["answer_text"].casefold()
            or not isinstance(citations, list)
            or not all(isinstance(citation, str) for citation in citations)
            or not citations
            or len(citations) != len(set(citations))
            or not set(citations) <= set(answers[request_id]["expected_citation_ids"])
        ):
            raise HarnessError("candidate response is uncited or exposes thought content")
        if not isinstance(record["output_tokens"], int) or not 1 <= record["output_tokens"] <= config["workload"]["answer_output_tokens_max"]:
            raise HarnessError("candidate response output token count is invalid")
        measurements = ("ttft_ns", "completion_ns", "worker_peak_rss_bytes", "network_calls")
        if any(not isinstance(record[field], int) or record[field] < 0 for field in measurements):
            raise HarnessError("candidate response measurement is invalid")
        if record["network_calls"] != 0:
            raise HarnessError("candidate response made a network call")
        result[request_id] = record
    if set(result) != set(answers):
        raise HarnessError("candidate responses do not cover exactly the answer cases")
    return result


def _review_by_request(
    records: list[dict[str, Any]],
    candidate_id: str,
    oracle: dict[str, dict[str, Any]],
    responses: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fields = set(config["human_review"]["required_fields"])
    accepted = config["human_review"]["accepted_value"]
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if set(record) != fields:
            raise HarnessError("human review fields drifted")
        request_id = record["request_id"]
        if record["candidate_id"] != candidate_id or request_id not in responses or request_id in result:
            raise HarnessError("human review identity is invalid")
        expected_continuity = (
            config["human_review"]["dialogue_continuity_value"]
            if oracle[request_id]["requires_dialogue"]
            else config["human_review"]["normal_continuity_value"]
        )
        if record["language"] != accepted or record["instruction_following"] != accepted or record["continuity"] != expected_continuity:
            raise HarnessError("human review did not accept language, instructions, or continuity")
        claims = record["claims"]
        if not isinstance(claims, list) or not claims:
            raise HarnessError("human review has no factual claims")
        for claim in claims:
            if (
                not isinstance(claim, dict)
                or set(claim) != {"claim_id", "supported", "citation_ids"}
                or claim["supported"] is not True
            ):
                raise HarnessError("human review found an unsupported claim")
            if (
                not isinstance(claim["claim_id"], str)
                or not isinstance(claim["citation_ids"], list)
                or not claim["citation_ids"]
                or not all(isinstance(citation, str) for citation in claim["citation_ids"])
                or not set(claim["citation_ids"]) <= set(responses[request_id]["citation_ids"])
            ):
                raise HarnessError("human review claim does not resolve to a displayed citation")
        result[request_id] = record
    if set(result) != set(responses):
        raise HarnessError("human review does not cover exactly the answer cases")
    return result


def _nearest_p95_ms(samples_ns: list[int]) -> float:
    if not samples_ns:
        raise HarnessError("no timing samples")
    return sorted(samples_ns)[max(0, (95 * len(samples_ns) + 99) // 100 - 1)] / 1_000_000


def score_candidate(
    workload_root: Path,
    candidate_id: str,
    responses_path: Path,
    reviews_path: Path,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    """Score one candidate's response and review files against a candidate-neutral workload."""

    print("Grounded-answer benchmark: verifying workload, candidate responses, and human review", flush=True)
    config = _read_json(config_path)
    _shortlist, _corpus = _verify_pins(config)
    manifest, oracle = _load_workload(workload_root, config, config_path)
    if candidate_id not in manifest["candidate_ids"]:
        raise HarnessError("candidate is not admitted by this workload")
    responses = _response_by_request(_read_jsonl(responses_path), candidate_id, oracle, config)
    reviews = _review_by_request(_read_jsonl(reviews_path), candidate_id, oracle, responses, config)
    per_locale: dict[str, dict[str, float | int]] = {}
    for locale in config["locales"]:
        locale_oracle = [entry for entry in oracle.values() if entry["locale"] == locale]
        locale_answers = [entry for entry in locale_oracle if entry["expected_disposition"] == "answer"]
        locale_terminals = [entry for entry in locale_oracle if entry["expected_disposition"] != "answer"]
        answer_ids = [entry["request_id"] for entry in locale_answers]
        dialogue_ids = [entry["request_id"] for entry in locale_answers if entry["requires_dialogue"]]
        per_locale[locale] = {
            "answer_case_count": len(answer_ids),
            "grounded_answer_rate": sum(request_id in reviews for request_id in answer_ids) / len(answer_ids),
            "citation_selection_rate": sum(bool(responses[request_id]["citation_ids"]) for request_id in answer_ids) / len(answer_ids),
            "terminal_case_count": len(locale_terminals),
            "terminal_disposition_rate": sum(entry["request_id"] not in responses for entry in locale_terminals) / len(locale_terminals),
            "language_rate": sum(reviews[request_id]["language"] == config["human_review"]["accepted_value"] for request_id in answer_ids) / len(answer_ids),
            "instruction_following_rate": sum(reviews[request_id]["instruction_following"] == config["human_review"]["accepted_value"] for request_id in answer_ids) / len(answer_ids),
            "dialogue_case_count": len(dialogue_ids),
            "dialogue_continuity_rate": sum(reviews[request_id]["continuity"] == config["human_review"]["dialogue_continuity_value"] for request_id in dialogue_ids) / len(dialogue_ids),
        }
        print(
            f"Grounded-answer benchmark: {locale}: {len(answer_ids)}/{len(answer_ids)} reviewed answers; "
            f"{len(locale_terminals)}/{len(locale_terminals)} terminal dispositions",
            flush=True,
        )
    values = list(responses.values())
    report = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "candidate_id": candidate_id,
        "harness_contract_sha256": _sha256(config_path),
        "workload_manifest_sha256": _sha256(workload_root / "workload-manifest.json"),
        "responses_sha256": _sha256(responses_path),
        "reviews_sha256": _sha256(reviews_path),
        "candidate_neutral_requests_sha256": manifest["requests_sha256"],
        "per_locale": per_locale,
        "measurement": {
            "ttft_p95_ms": _nearest_p95_ms([value["ttft_ns"] for value in values]),
            "completion_p95_ms": _nearest_p95_ms([value["completion_ns"] for value in values]),
            "output_tokens_median": statistics.median(value["output_tokens"] for value in values),
            "worker_peak_rss_bytes": max(value["worker_peak_rss_bytes"] for value in values),
            "network_calls": sum(value["network_calls"] for value in values),
        },
        "boundaries": {
            "ordinary_search_calls": 0,
            "cross_locale_retrieval_calls": 0,
            "tools_or_function_calls": 0,
            "terminal_model_invocations": 0,
        },
        "status": "pass",
        "failures": [],
    }
    print("Grounded-answer benchmark: candidate score complete; status=pass", flush=True)
    return report


def _cache_path(path: Path) -> None:
    cache_root = (DOCUMENTATION_ROOT / ".cache").resolve()
    if cache_root not in (path.resolve(), *path.resolve().parents):
        raise HarnessError("benchmark output must remain under documentation/.cache")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser("build-workload")
    build.add_argument("--evidence", type=Path, required=True)
    build.add_argument("--output-root", type=Path, required=True)
    build.add_argument("--config", type=Path, default=CONFIG_PATH)
    score = subcommands.add_parser("score")
    score.add_argument("--workload-root", type=Path, required=True)
    score.add_argument("--candidate-id", required=True)
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--reviews", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    try:
        if args.command == "build-workload":
            _cache_path(args.output_root)
            build_workload(args.evidence, args.output_root, args.config)
        else:
            _cache_path(args.output)
            report = score_candidate(args.workload_root, args.candidate_id, args.responses, args.reviews, args.config)
            _write_json(args.output, report)
    except HarnessError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
