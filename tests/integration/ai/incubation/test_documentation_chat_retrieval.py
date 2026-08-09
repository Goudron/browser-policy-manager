from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from app.documentation.retrieval import (
    SUPPORTED_LOCALES,
    ExactLocaleRetriever,
    RetrievalUnavailable,
    _citation,
    _load_json,
    _normalize_query,
    _regular_file,
    _safe_generation_root,
    _validate_chunk,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _chunk(locale: str, ordinal: int, version: str) -> dict:
    guide_id = "user-guide" if ordinal == 0 else "administrator-guide"
    guide_path = "user" if ordinal == 0 else "admin"
    return {
        "chunk_id": f"ragc-v1:{locale}:topic-{ordinal}:root:0",
        "topic_id": f"topic-{ordinal}",
        "anchor_id_or_root": "root",
        "ordinal": 0,
        "guide_id": guide_id,
        "published_url": f"/help/{locale}/{guide_path}/topic-{ordinal}.html",
        "source_sha256": f"{ordinal + 1:064x}",
        "identifiers": [f"topic-{ordinal}"],
        "documentation_version": version,
        "bpm_version": version,
        "provenance_class": "published_reviewed_dita",
        "heading_path": [f"{locale} topic {ordinal}"],
        "text": f"Reviewed {locale} evidence {ordinal}.",
    }


def _create_active_generation(tmp_path: Path, version: str = "0.9.3") -> Path:
    index_root = tmp_path / "index"
    generation_id = "raggen-v1-0123456789abcdef0123"
    root = index_root / "generations" / generation_id
    entries = []
    for locale in SUPPORTED_LOCALES:
        directory = root / locale
        directory.mkdir(parents=True)
        vectors = np.zeros((2, 768), dtype="<f4")
        vectors[0, 0] = 1.0
        vectors[1, 1] = 1.0
        vector_path = directory / "vectors.f32"
        vector_path.write_bytes(vectors.tobytes())
        metadata_path = directory / "chunks.json"
        _write_json(
            metadata_path,
            {"locale": locale, "chunks": [_chunk(locale, 0, version), _chunk(locale, 1, version)]},
        )
        manifest_path = directory / "manifest.json"
        _write_json(
            manifest_path,
            {
                "schema_version": 1,
                "locale": locale,
                "compatibility_key": {
                    "locale": locale,
                    "embedding_model_id": "intfloat/multilingual-e5-base",
                    "embedding_model_revision_or_checksum": (
                        "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703"
                    ),
                    "embedding_dimension": 768,
                    "vector_normalization": "L2",
                    "distance_metric": "cosine via descending dot product",
                    "storage_backend_id": "normalized-exact-f32-matrix-v1",
                },
                "vector_shape": [2, 768],
                "vector_dtype": "little-endian float32",
                "files": {
                    "vectors.f32": {
                        "byte_count": vector_path.stat().st_size,
                        "sha256": _sha256(vector_path),
                    },
                    "chunks.json": {
                        "byte_count": metadata_path.stat().st_size,
                        "sha256": _sha256(metadata_path),
                    },
                },
            },
        )
        entries.append(
            {"locale": locale, "manifest_sha256": _sha256(manifest_path), "chunk_count": 2}
        )
    root_manifest = root / "generation-manifest.json"
    _write_json(
        root_manifest,
        {
            "schema_version": 1,
            "generation_id": generation_id,
            "storage_backend_id": "normalized-exact-f32-matrix-v1",
            "source_manifest_sha256": "a" * 64,
            "locales": entries,
            "network_calls": 0,
            "ordinary_search_calls": 0,
        },
    )
    _write_json(
        index_root / "active-generation.json",
        {"generation_id": generation_id, "manifest_sha256": _sha256(root_manifest)},
    )
    return index_root


def _query(axis: int) -> np.ndarray:
    query = np.zeros(768, dtype=np.float32)
    query[axis] = 1.0
    return query


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _refresh_active_pointer(index_root: Path) -> None:
    generation_root = index_root / "generations" / "raggen-v1-0123456789abcdef0123"
    root_manifest = generation_root / "generation-manifest.json"
    _write_json(
        index_root / "active-generation.json",
        {
            "generation_id": "raggen-v1-0123456789abcdef0123",
            "manifest_sha256": _sha256(root_manifest),
        },
    )


def _refresh_locale_integrity(index_root: Path, locale: str = "en") -> None:
    generation_root = index_root / "generations" / "raggen-v1-0123456789abcdef0123"
    locale_root = generation_root / locale
    locale_manifest_path = locale_root / "manifest.json"
    locale_manifest = _read_json(locale_manifest_path)
    for name in ("vectors.f32", "chunks.json"):
        path = locale_root / name
        locale_manifest["files"][name] = {
            "byte_count": path.stat().st_size,
            "sha256": _sha256(path),
        }
    _write_json(locale_manifest_path, locale_manifest)
    _refresh_locale_manifest_hash(index_root, locale)


def _refresh_locale_manifest_hash(index_root: Path, locale: str = "en") -> None:
    generation_root = index_root / "generations" / "raggen-v1-0123456789abcdef0123"
    locale_manifest_path = generation_root / locale / "manifest.json"
    root_manifest_path = generation_root / "generation-manifest.json"
    root_manifest = _read_json(root_manifest_path)
    entry = next(item for item in root_manifest["locales"] if item["locale"] == locale)
    entry["manifest_sha256"] = _sha256(locale_manifest_path)
    _write_json(root_manifest_path, root_manifest)
    _refresh_active_pointer(index_root)


def test_retrieval_uses_only_the_requested_locale_and_keeps_local_citations(tmp_path: Path) -> None:
    retriever = ExactLocaleRetriever(_create_active_generation(tmp_path), bpm_version="0.9.3")

    english = retriever.retrieve(locale="en", query_vector=_query(0))
    russian = retriever.retrieve(locale="ru", query_vector=_query(0))

    assert english.locale == "en"
    assert english.candidates[0].text == "Reviewed en evidence 0."
    assert english.candidates[0].citation == english.candidates[0].citation.__class__(
        "topic:topic-0", "/help/en/user/topic-0.html", "topic-0", "root"
    )
    assert russian.candidates[0].text == "Reviewed ru evidence 0."
    assert all(
        candidate.citation.published_url.startswith("/help/ru/") for candidate in russian.candidates
    )


def test_citation_separates_a_verified_anchor_from_the_safe_topic_url() -> None:
    chunk = _chunk("ru", 0, "0.9.3")
    chunk["anchor_id_or_root"] = "a-after-selection"
    chunk["published_url"] = "/help/ru/user/topic-0.html#a-after-selection"

    citation = _citation(chunk, "ru")

    assert citation.citation_id == "topic:topic-0#a-after-selection"
    assert citation.published_url == "/help/ru/user/topic-0.html"
    chunk["published_url"] = "/help/ru/user/topic-0.html#different-anchor"
    with pytest.raises(RetrievalUnavailable, match="invalid_citation_target"):
        _citation(chunk, "ru")


def test_retrieval_applies_guide_filter_and_returns_an_explicit_empty_evidence_set(
    tmp_path: Path,
) -> None:
    retriever = ExactLocaleRetriever(_create_active_generation(tmp_path), bpm_version="0.9.3")

    filtered = retriever.retrieve(
        locale="en", query_vector=_query(0), guide_ids={"administrator-guide"}
    )
    missing = retriever.retrieve(locale="en", query_vector=_query(0), guide_ids={"missing-guide"})

    assert [candidate.guide_id for candidate in filtered.candidates] == ["administrator-guide"]
    assert missing.candidates == ()


def test_retrieval_rejects_stale_tampered_or_invalid_requests_without_fallback(
    tmp_path: Path,
) -> None:
    stale = ExactLocaleRetriever(
        _create_active_generation(tmp_path / "stale", version="0.9.2"), bpm_version="0.9.3"
    )
    with pytest.raises(RetrievalUnavailable, match="incompatible_generation"):
        stale.retrieve(locale="en", query_vector=_query(0))

    root = _create_active_generation(tmp_path / "tampered")
    vector_path = root / "generations" / "raggen-v1-0123456789abcdef0123" / "en" / "vectors.f32"
    vector_path.write_bytes(b"tampered")
    tampered = ExactLocaleRetriever(root, bpm_version="0.9.3")
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        tampered.retrieve(locale="en", query_vector=_query(0))

    valid = ExactLocaleRetriever(_create_active_generation(tmp_path / "valid"), bpm_version="0.9.3")
    with pytest.raises(RetrievalUnavailable, match="unsupported_locale"):
        valid.retrieve(locale="ja", query_vector=_query(0))
    with pytest.raises(RetrievalUnavailable, match="invalid_query_vector"):
        valid.retrieve(locale="en", query_vector=np.zeros(768, dtype=np.float32))
    with pytest.raises(RetrievalUnavailable, match="invalid_guide_filter"):
        valid.retrieve(locale="en", query_vector=_query(0), guide_ids="user-guide")


def test_retrieval_low_level_guards_reject_unsafe_files_vectors_and_citations(
    tmp_path: Path,
) -> None:
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("[", encoding="utf-8")
    list_json = tmp_path / "list.json"
    list_json.write_text("[]", encoding="utf-8")
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)

    for path in (invalid_json, list_json):
        with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
            _load_json(path)
    with pytest.raises(RetrievalUnavailable, match="unsafe"):
        _regular_file(link, "unsafe")
    with pytest.raises(RetrievalUnavailable, match="missing"):
        _regular_file(tmp_path / "missing.json", "missing")
    for value in ("not-a-vector", np.zeros(767), np.full(768, np.nan), np.zeros(768)):
        with pytest.raises(RetrievalUnavailable, match="invalid_query_vector"):
            _normalize_query(value)

    chunk = _chunk("en", 0, "0.9.3")
    for field, value in (("topic_id", ""), ("anchor_id_or_root", ""), ("published_url", 1)):
        invalid = dict(chunk)
        invalid[field] = value
        with pytest.raises(RetrievalUnavailable, match="invalid_citation_target"):
            _citation(invalid, "en")
    for url in (
        "https://example.invalid/help/en/user/topic-0.html",
        "/help/en/user/topic-0.html?unsafe=true",
        "/help/en/user/../topic-0.html",
        "/help/en/user/%74opic-0.html",
    ):
        invalid = dict(chunk)
        invalid["published_url"] = url
        with pytest.raises(RetrievalUnavailable, match="invalid_citation_target"):
            _citation(invalid, "en")


def test_chunk_validation_rejects_every_untrusted_metadata_class() -> None:
    valid = _chunk("en", 0, "0.9.3")
    assert _validate_chunk(valid, "en", "0.9.3") is valid

    invalid_cases = (
        {},
        {**valid, "text": ""},
        {**valid, "provenance_class": "unreviewed"},
        {**valid, "ordinal": -1},
        {**valid, "source_sha256": "too-short"},
        {**valid, "bpm_version": "0.9.2", "documentation_version": "0.9.2"},
        {**valid, "heading_path": ["", "safe"]},
        {**valid, "identifiers": ["safe", 1]},
    )
    expected_codes = (
        "invalid_chunk_metadata",
        "invalid_chunk_metadata",
        "invalid_chunk_metadata",
        "invalid_chunk_metadata",
        "invalid_chunk_metadata",
        "incompatible_generation",
        "invalid_chunk_metadata",
        "invalid_chunk_metadata",
    )
    for invalid, expected_code in zip(invalid_cases, expected_codes, strict=True):
        with pytest.raises(RetrievalUnavailable, match=expected_code):
            _validate_chunk(invalid, "en", "0.9.3")


def test_generation_root_validation_rejects_symlinked_missing_and_tampered_pointers(
    tmp_path: Path,
) -> None:
    target = _create_active_generation(tmp_path / "target")
    link = tmp_path / "linked-index"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(RetrievalUnavailable, match="unsafe_generation_root"):
        _safe_generation_root(link)

    root = _create_active_generation(tmp_path / "generation")
    pointer = root / "active-generation.json"
    for value, expected_code in (
        ({"generation_id": "invalid", "manifest_sha256": "a" * 64}, "invalid_active_generation"),
        (
            {"generation_id": "raggen-v1-0123456789abcdef0123", "manifest_sha256": "short"},
            "invalid_active_generation",
        ),
        (
            {"generation_id": "raggen-v1-11111111111111111111", "manifest_sha256": "a" * 64},
            "invalid_active_generation",
        ),
        (
            {"generation_id": "raggen-v1-0123456789abcdef0123", "manifest_sha256": "0" * 64},
            "invalid_active_generation",
        ),
    ):
        _write_json(pointer, value)
        with pytest.raises(RetrievalUnavailable, match=expected_code):
            _safe_generation_root(root)


def test_retrieval_rejects_invalid_limit_and_generation_manifest_layers(tmp_path: Path) -> None:
    invalid_limit = ExactLocaleRetriever(
        _create_active_generation(tmp_path / "limit"), bpm_version="0.9.3"
    )
    with pytest.raises(RetrievalUnavailable, match="invalid_retrieval_limit"):
        invalid_limit.retrieve(locale="en", query_vector=_query(0), limit=0)

    root = _create_active_generation(tmp_path / "root")
    manifest_path = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "generation-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["storage_backend_id"] = "unexpected"
    _write_json(manifest_path, manifest)
    _refresh_active_pointer(root)
    with pytest.raises(RetrievalUnavailable, match="incompatible_generation"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "entries")
    manifest_path = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "generation-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["locales"] = []
    _write_json(manifest_path, manifest)
    _refresh_active_pointer(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "entry")
    manifest_path = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "generation-manifest.json"
    )
    manifest = _read_json(manifest_path)
    manifest["locales"][0]["manifest_sha256"] = 1
    _write_json(manifest_path, manifest)
    _refresh_active_pointer(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )


def test_retrieval_rejects_invalid_locale_artifacts_after_verified_manifest_chain(
    tmp_path: Path,
) -> None:
    root = _create_active_generation(tmp_path / "symlink")
    generation_root = root / "generations" / "raggen-v1-0123456789abcdef0123"
    locale_root = generation_root / "en"
    replacement = generation_root / "ru"
    shutil.rmtree(locale_root)
    locale_root.symlink_to(replacement, target_is_directory=True)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "locale-manifest")
    locale_manifest = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "en" / "manifest.json"
    )
    locale_manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "compatibility")
    locale_manifest = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "en" / "manifest.json"
    )
    manifest = _read_json(locale_manifest)
    manifest["compatibility_key"]["storage_backend_id"] = "unexpected"
    _write_json(locale_manifest, manifest)
    _refresh_locale_integrity(root)
    with pytest.raises(RetrievalUnavailable, match="incompatible_generation"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "files")
    locale_manifest = (
        root / "generations" / "raggen-v1-0123456789abcdef0123" / "en" / "manifest.json"
    )
    manifest = _read_json(locale_manifest)
    manifest["files"] = {}
    _write_json(locale_manifest, manifest)
    _refresh_locale_manifest_hash(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )


def test_retrieval_rejects_verified_but_invalid_vector_and_chunk_payloads(tmp_path: Path) -> None:
    root = _create_active_generation(tmp_path / "raw")
    generation_root = root / "generations" / "raggen-v1-0123456789abcdef0123" / "en"
    (generation_root / "vectors.f32").write_bytes(b"x")
    _refresh_locale_integrity(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "vectors")
    generation_root = root / "generations" / "raggen-v1-0123456789abcdef0123" / "en"
    invalid_vectors = np.full((2, 768), np.nan, dtype="<f4")
    (generation_root / "vectors.f32").write_bytes(invalid_vectors.tobytes())
    _refresh_locale_integrity(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_generation_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "chunks")
    generation_root = root / "generations" / "raggen-v1-0123456789abcdef0123" / "en"
    _write_json(generation_root / "chunks.json", {"locale": "en", "chunks": []})
    _refresh_locale_integrity(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_chunk_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )

    root = _create_active_generation(tmp_path / "ordered")
    generation_root = root / "generations" / "raggen-v1-0123456789abcdef0123" / "en"
    chunks = _read_json(generation_root / "chunks.json")
    chunks["chunks"].reverse()
    _write_json(generation_root / "chunks.json", chunks)
    _refresh_locale_integrity(root)
    with pytest.raises(RetrievalUnavailable, match="invalid_chunk_metadata"):
        ExactLocaleRetriever(root, bpm_version="0.9.3").retrieve(
            locale="en", query_vector=_query(0)
        )
