"""Run the BPM093 M3-03 lexical relevance comparison in an isolated temporary workspace.

The runner never downloads an artifact. Callers supply already verified Pagefind and Meilisearch
artifacts; measured candidate queries use only temporary loopback/static-site resources.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import html
import json
import os
import subprocess
import tarfile
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from .search_candidate_prototypes import build_compact_documents
except ImportError:  # Direct script execution keeps documentation/tools on sys.path.
    from search_candidate_prototypes import build_compact_documents

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = DOCUMENTATION_ROOT / "config"
BENCHMARK_CONFIG = CONFIG_ROOT / "search-relevance-benchmark-0.9.3.json"
EVALUATION_CORPUS = CONFIG_ROOT / "search-rag-evaluation-corpus-0.9.3.json"

CURRENT_CANDIDATE = "current-static-control"
PAGEFIND_CANDIDATE = "pagefind-1.5.2"
MEILISEARCH_CANDIDATE = "meilisearch-ce-1.45.1"
CANDIDATES = (CURRENT_CANDIDATE, PAGEFIND_CANDIDATE, MEILISEARCH_CANDIDATE)
MASTER_KEY = "bpm093-benchmark-local-private-key"


class BenchmarkError(RuntimeError):
    """Raised when a benchmark input or local candidate cannot be validated."""


@dataclass(frozen=True)
class QueryCase:
    query_id: str
    locale: str
    query: str
    query_class: str
    expected_topic_id: str | None
    expected_no_result: bool
    disposition: str | None
    scored: bool


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifact(path: Path, expected_name: str, expected_sha256: str) -> None:
    if path.name != expected_name:
        raise BenchmarkError(f"artifact name mismatch: expected {expected_name}, got {path.name}")
    if not path.is_file():
        raise BenchmarkError(f"artifact is missing: {path}")
    actual = _sha256(path)
    if actual != expected_sha256:
        raise BenchmarkError(f"artifact SHA-256 mismatch for {path.name}: {actual}")


def _normalized(text: str) -> str:
    folded = unicodedata.normalize("NFKC", str(text or "")).lower()
    decomposed = unicodedata.normalize("NFD", folded)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _current_tokens(query: str) -> list[str]:
    normalized = _normalized(query)
    safe = "".join(
        character if character.isalnum() or character in "._:/-" else " "
        for character in normalized
    )
    return safe.split()[:24]


def _current_searchable_text(document: dict[str, Any]) -> str:
    searchable = document["searchable"]
    return " ".join(
        [
            searchable["title"],
            searchable["shortdesc"],
            *searchable["headings"],
            searchable["body"],
            *searchable["keywords"],
            *searchable["identifiers"],
            *searchable["aliases"],
        ]
    )


def _current_control_topics(documents: list[dict[str, Any]], query: str) -> list[str]:
    """Mirror the current bpm-docs-search.js lexical scoring core, without DOM rendering."""
    tokens = _current_tokens(query)
    ranked: list[tuple[int, str, str]] = []
    for document in documents:
        searchable = document["searchable"]
        title = _normalized(searchable["title"])
        identifiers = _normalized(" ".join(searchable["identifiers"]))
        aliases = _normalized(" ".join(searchable["aliases"]))
        body = _normalized(_current_searchable_text(document))
        score = 0
        for token in tokens:
            if token in identifiers.split():
                score += 80
            if token in title:
                score += 40
            if token in aliases:
                score += 30
            if token in body:
                score += 10
        if score:
            ranked.append((score, _normalized(searchable["title"]), document["topic_id"]))
    return [topic_id for _, _, topic_id in sorted(ranked, key=lambda item: (-item[0], item[1]))[:5]]


def _remove_accents(text: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(character)
    )


def build_query_plan() -> list[QueryCase]:
    config = _read_json(BENCHMARK_CONFIG)
    corpus = _read_json(EVALUATION_CORPUS)
    cases: list[QueryCase] = []
    template_classes = (
        "technical_identifier",
        "canonical",
        "alias",
        "natural_language",
        "morphology",
        "typo",
        "compound",
        "natural_context",
    )
    for locale in corpus["locales"]:
        templates = corpus["search_templates"][locale]
        for domain in corpus["domains"]:
            terms = domain["terms"][locale]
            substitutions = {
                "identifier": domain["identifier"],
                "term": terms[0],
                "alias": terms[1],
                "inflection": terms[2],
                "typo": terms[3],
                "compound": terms[4],
            }
            for template, query_class in zip(templates, template_classes, strict=True):
                if locale == "de" and query_class == "compound":
                    query_class = "german_compound"
                elif locale == "ru" and query_class == "morphology":
                    query_class = "russian_inflection"
                elif locale == "zh-CN" and query_class in {"canonical", "compound"}:
                    query_class = "chinese_segmentation"
                cases.append(
                    QueryCase(
                        query_id=f"{locale}:{domain['id']}:{query_class}",
                        locale=locale,
                        query=template.format(**substitutions),
                        query_class=query_class,
                        expected_topic_id=domain["topic_id"],
                        expected_no_result=False,
                        disposition="answer",
                        scored=True,
                    )
                )
            if locale == "fr":
                cases.append(
                    QueryCase(
                        query_id=f"{locale}:{domain['id']}:accent",
                        locale=locale,
                        query=_remove_accents(terms[0]),
                        query_class="accent",
                        expected_topic_id=domain["topic_id"],
                        expected_no_result=False,
                        disposition="answer",
                        scored=True,
                    )
                )
        for case_id, query, disposition in corpus["boundary_cases"][locale]["search"]:
            expected_no_result = disposition in config["fixture_rules"]["no_result_dispositions"]
            cases.append(
                QueryCase(
                    query_id=f"{locale}:boundary:{case_id}",
                    locale=locale,
                    query=query,
                    query_class="no_result" if expected_no_result else "ambiguous",
                    expected_topic_id=None,
                    expected_no_result=expected_no_result,
                    disposition=disposition,
                    scored=expected_no_result,
                )
            )
    return cases


def _safe_extract(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, "r:gz") as contents:
        for member in contents.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise BenchmarkError(f"unsafe archive member: {member.name}")
        contents.extractall(destination, filter="data")


def _pagefind_html(document: dict[str, Any]) -> str:
    searchable = document["searchable"]
    facets = "".join(
        f'<span data-pagefind-filter="{html.escape(field)}">{html.escape(value)}</span>'
        for field, values in document["facets"].items()
        for value in values
    )
    return "".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(document["locale"])}"><head>',
            f'<meta charset="utf-8"><meta data-pagefind-meta="topic_id" content="{html.escape(document["topic_id"])}">',
            "</head><body>",
            f'<main data-pagefind-body><h1 data-pagefind-meta="title">{html.escape(searchable["title"])}</h1>',
            f"<p>{html.escape(searchable['shortdesc'])}</p>",
            f"<p>{html.escape(searchable['body'])}</p>{facets}</main></body></html>",
        ]
    )


def _prepare_pagefind_site(
    work_dir: Path,
    pagefind_package: Path,
    pagefind_linux_package: Path,
    documents: list[dict[str, Any]] | None = None,
) -> Path:
    node_modules = work_dir / "node_modules"
    _safe_extract(pagefind_package, node_modules)
    (node_modules / "package").rename(node_modules / "pagefind")
    (node_modules / "@pagefind").mkdir(parents=True, exist_ok=True)
    _safe_extract(pagefind_linux_package, node_modules / "@pagefind")
    (node_modules / "@pagefind" / "package").rename(node_modules / "@pagefind" / "linux-x64")
    binary = node_modules / "@pagefind" / "linux-x64/bin/pagefind_extended"
    binary.chmod(binary.stat().st_mode | 0o111)
    site_root = work_dir / "pagefind-site"
    site_root.mkdir()
    (site_root / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
    for document in documents or build_compact_documents():
        path = site_root / document["source"]["output_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_pagefind_html(document), encoding="utf-8")
    cli = node_modules / "pagefind/lib/runner/bin.cjs"
    for locale in _read_json(EVALUATION_CORPUS)["locales"]:
        completed = subprocess.run(
            ["node", str(cli), "--site", str(site_root / locale)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise BenchmarkError(
                f"Pagefind indexing failed for {locale}: {completed.stderr.strip()}"
            )
    return site_root


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


class _StaticServer:
    def __init__(self, root: Path) -> None:
        handler = functools.partial(_QuietStaticHandler, directory=str(root))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def origin(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> _StaticServer:
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


PAGEFIND_QUERY_CLIENT = r"""
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [siteRoot, origin, locale, inputPath, outputPath] = process.argv.slice(1);
const expectedOrigin = new URL(origin).origin;
const originalFetch = globalThis.fetch;
const fetches = [];
globalThis.fetch = async (input, init) => {
  const url = new URL(input instanceof Request ? input.url : String(input), origin);
  if (url.origin !== expectedOrigin) throw new Error(`unexpected Pagefind fetch origin: ${url.origin}`);
  const response = await originalFetch(input, init);
  fetches.push({ url: url.href, bytes: Number(response.headers.get("content-length") || 0) });
  return response;
};
const pagefindPath = pathToFileURL(path.join(siteRoot, locale, "pagefind", "pagefind.js")).href;
const pagefind = await import(pagefindPath);
await pagefind.options({ basePath: `${origin}/${locale}/pagefind/`, baseUrl: `${origin}/${locale}/`, noWorker: true });
const cases = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const output = [];
for (const item of cases) {
  const before = fetches.length;
  const started = performance.now();
  const response = await pagefind.search(item.query);
  const data = await Promise.all(response.results.slice(0, 5).map((result) => result.data()));
  output.push({
    query_id: item.query_id,
    result_data: data,
    elapsed_ms: performance.now() - started,
    fetched_bytes: fetches.slice(before).reduce((total, entry) => total + entry.bytes, 0),
  });
}
fs.writeFileSync(outputPath, JSON.stringify({ fetches, output }));
"""


def _pagefind_topics(
    site_root: Path, query_cases: list[QueryCase], documents: list[dict[str, Any]], work_dir: Path
) -> dict[str, list[str]]:
    document_by_filename = {
        Path(document["source"]["output_path"]).name: document["topic_id"] for document in documents
    }
    by_locale: dict[str, list[QueryCase]] = defaultdict(list)
    for case in query_cases:
        by_locale[case.locale].append(case)
    topics: dict[str, list[str]] = {}
    with _StaticServer(site_root) as server:
        for locale, cases in by_locale.items():
            input_path = work_dir / f"pagefind-input-{locale}.json"
            output_path = work_dir / f"pagefind-output-{locale}.json"
            input_path.write_text(
                json.dumps([case.__dict__ for case in cases], sort_keys=True), encoding="utf-8"
            )
            completed = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "--eval",
                    PAGEFIND_QUERY_CLIENT,
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
                raise BenchmarkError(
                    f"Pagefind query failed for {locale}: {completed.stderr.strip()}"
                )
            payload = _read_json(output_path)
            if not payload["fetches"] or any(
                not fetch["url"].startswith(server.origin) for fetch in payload["fetches"]
            ):
                raise BenchmarkError(f"Pagefind fetch boundary was not loopback-only for {locale}")
            for item in payload["output"]:
                resolved: list[str] = []
                for result in item["result_data"]:
                    metadata = result.get("meta", {})
                    topic_id = metadata.get("topic_id")
                    if not topic_id:
                        topic_id = document_by_filename.get(Path(result.get("url", "")).name)
                    if topic_id:
                        resolved.append(topic_id)
                topics[item["query_id"]] = resolved
    return topics


def _http_json(
    url: str, method: str = "GET", payload: dict[str, Any] | list[Any] | None = None
) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname != "127.0.0.1":
        raise BenchmarkError(f"non-loopback benchmark request rejected: {url}")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {MASTER_KEY}")
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310: loopback is checked above
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise BenchmarkError(f"Meilisearch HTTP {error.code} for {parsed.path}") from error


def _wait_for_meilisearch(origin: str, timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            health = _http_json(f"{origin}/health")
            if health.get("status") == "available":
                return
        except BenchmarkError, urllib.error.URLError:
            pass
        time.sleep(0.1)
    raise BenchmarkError("Meilisearch did not become healthy")


def _wait_task(origin: str, task_uid: int) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        task = _http_json(f"{origin}/tasks/{task_uid}")
        if task.get("status") == "succeeded":
            return
        if task.get("status") in {"failed", "canceled"}:
            raise BenchmarkError(f"Meilisearch task {task_uid} failed: {task}")
        time.sleep(0.05)
    raise BenchmarkError(f"Meilisearch task {task_uid} timed out")


def _task_uid(payload: dict[str, Any]) -> int:
    value = payload.get("taskUid", payload.get("uid"))
    if not isinstance(value, int):
        raise BenchmarkError(f"Meilisearch response does not contain task UID: {payload}")
    return value


def _meili_documents(documents: list[dict[str, Any]], locale: str) -> list[dict[str, Any]]:
    return [
        {
            "id": document["document_id"].replace(":", "-"),
            "locale": locale,
            "guide_id": document["guide_id"],
            "topic_id": document["topic_id"],
            "topic_kind": document["topic_kind"],
            "url": document["url"],
            "title": document["searchable"]["title"],
            "aliases": document["searchable"]["aliases"],
            "headings": document["searchable"]["headings"],
            "body": document["searchable"]["body"],
            "identifiers": document["searchable"]["identifiers"],
            **{field: values for field, values in document["facets"].items() if field != "locale"},
        }
        for document in documents
        if document["locale"] == locale
    ]


def _meilisearch_topics(
    binary: Path, query_cases: list[QueryCase], documents: list[dict[str, Any]], work_dir: Path
) -> dict[str, list[str]]:
    log_path = work_dir / "meilisearch.log"
    db_path = work_dir / "meilisearch-db"
    binary.chmod(binary.stat().st_mode | 0o111)
    process = subprocess.Popen(
        [
            str(binary),
            "--http-addr",
            "127.0.0.1:17703",
            "--master-key",
            MASTER_KEY,
            "--db-path",
            str(db_path),
            "--no-analytics",
        ],
        cwd=work_dir,
        env={**os.environ, "MEILI_NO_ANALYTICS": "true"},
        stdout=log_path.open("w", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        text=True,
    )
    origin = "http://127.0.0.1:17703"
    try:
        _wait_for_meilisearch(origin)
        for locale in _read_json(EVALUATION_CORPUS)["locales"]:
            index_uid = f"bpm093-{locale.lower()}".replace("-", "_")
            created = _http_json(
                f"{origin}/indexes", "POST", {"uid": index_uid, "primaryKey": "id"}
            )
            _wait_task(origin, _task_uid(created))
            settings = _http_json(
                f"{origin}/indexes/{index_uid}/settings",
                "PATCH",
                {
                    "searchableAttributes": ["identifiers", "title", "aliases", "headings", "body"],
                    "filterableAttributes": [
                        "guide_id",
                        "topic_kind",
                        "firefox_channel",
                        "policy_category",
                        "cis_level",
                        "cis_control_state",
                        "api_area",
                        "bpm_version",
                    ],
                },
            )
            _wait_task(origin, _task_uid(settings))
            added = _http_json(
                f"{origin}/indexes/{index_uid}/documents?primaryKey=id",
                "POST",
                _meili_documents(documents, locale),
            )
            _wait_task(origin, _task_uid(added))
        topics: dict[str, list[str]] = {}
        for case in query_cases:
            index_uid = f"bpm093-{case.locale.lower()}".replace("-", "_")
            response = _http_json(
                f"{origin}/indexes/{index_uid}/search", "POST", {"q": case.query, "limit": 5}
            )
            topics[case.query_id] = [hit["topic_id"] for hit in response.get("hits", [])]
        return topics
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def _rank_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    expected_topic = [record for record in records if record["expected_topic_id"]]
    no_result = [record for record in records if record["expected_no_result"]]
    scored = [record for record in records if record["scored"]]
    reciprocal_ranks = [record["reciprocal_rank"] for record in expected_topic]
    top_1 = sum(record["top_1_correct"] for record in expected_topic)
    recall_5 = sum(record["recall_at_5"] for record in expected_topic)
    correct_empty = sum(not record["result_topic_ids"] for record in no_result)
    returned_empty = [record for record in scored if not record["result_topic_ids"]]
    return {
        "expected_topic_queries": len(expected_topic),
        "top_1": top_1 / len(expected_topic) if expected_topic else None,
        "mrr": sum(reciprocal_ranks) / len(expected_topic) if expected_topic else None,
        "recall_at_5": recall_5 / len(expected_topic) if expected_topic else None,
        "expected_no_result_queries": len(no_result),
        "correct_empty": correct_empty,
        "no_result_precision": correct_empty / len(returned_empty) if returned_empty else None,
        "no_result_recall": correct_empty / len(no_result) if no_result else None,
    }


def _host_fingerprint() -> dict[str, Any]:
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8")
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
    model = next(
        (
            line.split(":", 1)[1].strip()
            for line in cpuinfo.splitlines()
            if line.startswith("model name")
        ),
        "unknown",
    )
    memory_kib = int(
        next(line.split()[1] for line in meminfo.splitlines() if line.startswith("MemTotal:"))
    )
    return {
        "cpu_model": model,
        "memory_bytes": memory_kib * 1024,
        "kernel": os.uname().release,
        "architecture": os.uname().machine,
    }


def run_benchmark(
    work_dir: Path,
    pagefind_package: Path,
    pagefind_linux_package: Path,
    meilisearch_binary: Path,
    output_dir: Path,
) -> dict[str, Any]:
    config = _read_json(BENCHMARK_CONFIG)
    artifacts = config["artifacts"]
    _validate_artifact(
        pagefind_package,
        artifacts["pagefind"]["npm_package"],
        artifacts["pagefind"]["npm_package_sha256"],
    )
    _validate_artifact(
        pagefind_linux_package,
        artifacts["pagefind"]["linux_x64_package"],
        artifacts["pagefind"]["linux_x64_package_sha256"],
    )
    _validate_artifact(
        meilisearch_binary,
        artifacts["meilisearch_ce"]["linux_amd64_binary"],
        artifacts["meilisearch_ce"]["linux_amd64_binary_sha256"],
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    documents = build_compact_documents()
    cases = build_query_plan()
    current_topics = {
        case.query_id: _current_control_topics(
            [doc for doc in documents if doc["locale"] == case.locale], case.query
        )
        for case in cases
    }
    pagefind_site = _prepare_pagefind_site(work_dir, pagefind_package, pagefind_linux_package)
    pagefind_topics = _pagefind_topics(pagefind_site, cases, documents, work_dir)
    meilisearch_topics = _meilisearch_topics(meilisearch_binary, cases, documents, work_dir)
    topic_sets = {
        CURRENT_CANDIDATE: current_topics,
        PAGEFIND_CANDIDATE: pagefind_topics,
        MEILISEARCH_CANDIDATE: meilisearch_topics,
    }
    fixture_hash = _sha256(EVALUATION_CORPUS)
    raw_records: list[dict[str, Any]] = []
    for candidate_id in CANDIDATES:
        for case in cases:
            result_topics = topic_sets[candidate_id][case.query_id]
            try:
                rank = (
                    result_topics.index(case.expected_topic_id) + 1
                    if case.expected_topic_id
                    else None
                )
            except ValueError:
                rank = None
            raw_records.append(
                {
                    "schema_version": 1,
                    "backlog_item": "BPM093-M3-03",
                    "candidate_id": candidate_id,
                    "fixture_sha256": fixture_hash,
                    "locale": case.locale,
                    "query_id": case.query_id,
                    "query": case.query,
                    "query_class": case.query_class,
                    "expected_topic_id": case.expected_topic_id,
                    "expected_no_result": case.expected_no_result,
                    "expected_disposition": case.disposition,
                    "scored": case.scored,
                    "result_topic_ids": result_topics,
                    "rank": rank,
                    "top_1_correct": bool(rank == 1),
                    "recall_at_5": bool(rank and rank <= 5),
                    "reciprocal_rank": 1 / rank if rank else 0,
                }
            )
    raw_path = output_dir / "bpm093-m3-03-search-relevance.raw.ndjson"
    raw_path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in raw_records
        ),
        encoding="utf-8",
    )
    summary = {
        "schema_version": 1,
        "backlog_item": "BPM093-M3-03",
        "status": "measured-no-selection",
        "fixture_sha256": fixture_hash,
        "host": _host_fingerprint(),
        "artifacts": {
            candidate: {"sha256": _sha256(path)}
            for candidate, path in {
                PAGEFIND_CANDIDATE: pagefind_package,
                "pagefind-linux-x64": pagefind_linux_package,
                MEILISEARCH_CANDIDATE: meilisearch_binary,
            }.items()
        },
        "candidate_execution": config["candidate_execution"],
        "raw_record_count": len(raw_records),
        "raw_path": str(raw_path),
        "candidates": {},
    }
    for candidate_id in CANDIDATES:
        candidate_records = [
            record for record in raw_records if record["candidate_id"] == candidate_id
        ]
        summary["candidates"][candidate_id] = {
            "all_locales": _rank_metrics(candidate_records),
            "locales": {
                locale: _rank_metrics(
                    [record for record in candidate_records if record["locale"] == locale]
                )
                for locale in _read_json(EVALUATION_CORPUS)["locales"]
            },
        }
    summary_path = output_dir / "bpm093-m3-03-search-relevance.summary.json"
    summary_path.write_text(
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
        json.dumps(
            {"raw_record_count": summary["raw_record_count"], "status": summary["status"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
