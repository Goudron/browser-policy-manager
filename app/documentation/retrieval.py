"""Fail-closed exact retrieval from an activated local chat-RAG generation.

This module deliberately accepts an already encoded query vector.  Encoding, model loading, chat
API exposure, and answer generation belong to later backlog tasks.  It makes no network request and
does not import the documentation build tooling or the ordinary documentation search.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlsplit

if TYPE_CHECKING:
    import numpy as np

from app.documentation.assistant_contracts import SUPPORTED_LOCALES

GENERATION_ID: Final[re.Pattern[str]] = re.compile(r"raggen-v1-[0-9a-f]{20}")
STORAGE_BACKEND: Final[str] = "normalized-exact-f32-matrix-v1"
EMBEDDING_MODEL_ID: Final[str] = "intfloat/multilingual-e5-base"
EMBEDDING_ARTIFACT_SHA256: Final[str] = (
    "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703"
)
VECTOR_DIMENSION: Final[int] = 768
REQUIRED_CHUNK_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "chunk_id",
        "topic_id",
        "anchor_id_or_root",
        "ordinal",
        "guide_id",
        "published_url",
        "source_sha256",
        "identifiers",
        "documentation_version",
        "bpm_version",
        "provenance_class",
        "heading_path",
        "text",
    }
)


class RetrievalUnavailable(RuntimeError):
    """A verified local generation cannot safely answer this retrieval request."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _numpy() -> Any:
    """Load the optional vector backend only when a retrieval operation needs it."""

    try:
        import numpy
    except ModuleNotFoundError as error:
        raise RetrievalUnavailable("optional_ai_dependencies_unavailable") from error
    return numpy


@dataclass(frozen=True)
class LocalCitation:
    """A local, locale-private citation target retained with retrieved evidence."""

    citation_id: str
    published_url: str
    topic_id: str
    anchor_id_or_root: str
    source_kind: str = "local"


@dataclass(frozen=True)
class RetrievedEvidence:
    """One eligible local chunk with an exact citation and deterministic similarity score."""

    chunk_id: str
    ordinal: int
    guide_id: str
    documentation_version: str
    bpm_version: str
    source_sha256: str
    heading_path: tuple[str, ...]
    text: str
    score: float
    citation: LocalCitation
    identifiers: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    """A same-locale result set from one verified active generation."""

    generation_id: str
    locale: str
    candidates: tuple[RetrievedEvidence, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RetrievalUnavailable("invalid_generation_metadata") from error
    if not isinstance(value, dict):
        raise RetrievalUnavailable("invalid_generation_metadata")
    return value


def _regular_file(path: Path, code: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise RetrievalUnavailable(code)
    return path


def _safe_generation_root(index_root: Path) -> tuple[str, Path]:
    if index_root.is_symlink():
        raise RetrievalUnavailable("unsafe_generation_root")
    pointer_path = _regular_file(index_root / "active-generation.json", "no_active_generation")
    pointer = _load_json(pointer_path)
    generation_id = pointer.get("generation_id")
    manifest_sha256 = pointer.get("manifest_sha256")
    if not isinstance(generation_id, str) or not GENERATION_ID.fullmatch(generation_id):
        raise RetrievalUnavailable("invalid_active_generation")
    if not isinstance(manifest_sha256, str) or len(manifest_sha256) != 64:
        raise RetrievalUnavailable("invalid_active_generation")
    generation_root = index_root / "generations" / generation_id
    if not generation_root.is_dir() or generation_root.is_symlink():
        raise RetrievalUnavailable("invalid_active_generation")
    manifest_path = _regular_file(
        generation_root / "generation-manifest.json", "invalid_active_generation"
    )
    if _sha256(manifest_path) != manifest_sha256:
        raise RetrievalUnavailable("invalid_active_generation")
    return generation_id, generation_root


def _normalize_query(query_vector: np.ndarray | Collection[float]) -> np.ndarray:
    numpy = _numpy()
    try:
        vector = numpy.asarray(query_vector, dtype=numpy.float32)
    except (TypeError, ValueError) as error:
        raise RetrievalUnavailable("invalid_query_vector") from error
    if vector.shape != (VECTOR_DIMENSION,) or not numpy.isfinite(vector).all():
        raise RetrievalUnavailable("invalid_query_vector")
    norm = float(numpy.linalg.norm(vector))
    if not numpy.isclose(norm, 1.0, atol=1e-4):
        raise RetrievalUnavailable("invalid_query_vector")
    return vector


def _citation(chunk: dict[str, Any], locale: str) -> LocalCitation:
    topic_id = chunk.get("topic_id")
    anchor = chunk.get("anchor_id_or_root")
    published_url = chunk.get("published_url")
    if not isinstance(topic_id, str) or not topic_id or not isinstance(anchor, str) or not anchor:
        raise RetrievalUnavailable("invalid_citation_target")
    if not isinstance(published_url, str):
        raise RetrievalUnavailable("invalid_citation_target")
    parsed = urlsplit(published_url)
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or not parsed.path.startswith(f"/help/{locale}/")
        or ".." in parsed.path.split("/")
        or "%" in parsed.path
        or (anchor == "root" and parsed.fragment)
        or (anchor != "root" and parsed.fragment != anchor)
    ):
        raise RetrievalUnavailable("invalid_citation_target")
    citation_id = f"topic:{topic_id}" if anchor == "root" else f"topic:{topic_id}#{anchor}"
    return LocalCitation(citation_id, parsed.path, topic_id, anchor)


def _validate_chunk(chunk: Any, locale: str, expected_bpm_version: str) -> dict[str, Any]:
    if not isinstance(chunk, dict) or set(chunk) != REQUIRED_CHUNK_FIELDS:
        raise RetrievalUnavailable("invalid_chunk_metadata")
    required_text = (
        "chunk_id",
        "guide_id",
        "documentation_version",
        "bpm_version",
        "provenance_class",
        "text",
    )
    if any(not isinstance(chunk[field], str) or not chunk[field] for field in required_text):
        raise RetrievalUnavailable("invalid_chunk_metadata")
    if chunk["provenance_class"] != "published_reviewed_dita":
        raise RetrievalUnavailable("invalid_chunk_metadata")
    if not isinstance(chunk["ordinal"], int) or chunk["ordinal"] < 0:
        raise RetrievalUnavailable("invalid_chunk_metadata")
    if not isinstance(chunk["source_sha256"], str) or len(chunk["source_sha256"]) != 64:
        raise RetrievalUnavailable("invalid_chunk_metadata")
    if (
        chunk["bpm_version"] != expected_bpm_version
        or chunk["documentation_version"] != expected_bpm_version
    ):
        raise RetrievalUnavailable("incompatible_generation")
    if not isinstance(chunk["heading_path"], list) or not all(
        isinstance(value, str) and value for value in chunk["heading_path"]
    ):
        raise RetrievalUnavailable("invalid_chunk_metadata")
    if not isinstance(chunk["identifiers"], list) or not all(
        isinstance(value, str) for value in chunk["identifiers"]
    ):
        raise RetrievalUnavailable("invalid_chunk_metadata")
    _citation(chunk, locale)
    return chunk


class ExactLocaleRetriever:
    """Read and exact-scan one locale from the atomically selected local generation."""

    def __init__(self, index_root: Path, *, bpm_version: str) -> None:
        self._index_root = Path(index_root)
        self._bpm_version = bpm_version

    def retrieve(
        self,
        *,
        locale: str,
        query_vector: np.ndarray | Collection[float],
        guide_ids: Collection[str] | None = None,
        limit: int = 5,
    ) -> RetrievalResult:
        if locale not in SUPPORTED_LOCALES:
            raise RetrievalUnavailable("unsupported_locale")
        if not isinstance(limit, int) or not 1 <= limit <= 5:
            raise RetrievalUnavailable("invalid_retrieval_limit")
        if isinstance(guide_ids, (bytes, str)) or (
            guide_ids is not None
            and any(not isinstance(guide_id, str) or not guide_id for guide_id in guide_ids)
        ):
            raise RetrievalUnavailable("invalid_guide_filter")
        query = _normalize_query(query_vector)
        generation_id, root = _safe_generation_root(self._index_root)
        root_manifest = _load_json(
            _regular_file(root / "generation-manifest.json", "invalid_active_generation")
        )
        if (
            root_manifest.get("generation_id") != generation_id
            or root_manifest.get("storage_backend_id") != STORAGE_BACKEND
        ):
            raise RetrievalUnavailable("incompatible_generation")
        entries = root_manifest.get("locales")
        if not isinstance(entries, list) or [
            entry.get("locale") for entry in entries if isinstance(entry, dict)
        ] != list(SUPPORTED_LOCALES):
            raise RetrievalUnavailable("invalid_generation_metadata")
        entry = next((item for item in entries if item["locale"] == locale), None)
        if not isinstance(entry, dict) or not isinstance(entry.get("manifest_sha256"), str):
            raise RetrievalUnavailable("invalid_generation_metadata")
        locale_root = root / locale
        if not locale_root.is_dir() or locale_root.is_symlink():
            raise RetrievalUnavailable("invalid_generation_metadata")
        locale_manifest_path = _regular_file(
            locale_root / "manifest.json", "invalid_generation_metadata"
        )
        if _sha256(locale_manifest_path) != entry["manifest_sha256"]:
            raise RetrievalUnavailable("invalid_generation_metadata")
        locale_manifest = _load_json(locale_manifest_path)
        compatibility = locale_manifest.get("compatibility_key")
        rows_and_dimension = locale_manifest.get("vector_shape")
        if (
            locale_manifest.get("locale") != locale
            or not isinstance(compatibility, dict)
            or compatibility.get("locale") != locale
            or compatibility.get("embedding_model_id") != EMBEDDING_MODEL_ID
            or compatibility.get("embedding_model_revision_or_checksum")
            != EMBEDDING_ARTIFACT_SHA256
            or compatibility.get("embedding_dimension") != VECTOR_DIMENSION
            or compatibility.get("vector_normalization") != "L2"
            or compatibility.get("distance_metric") != "cosine via descending dot product"
            or compatibility.get("storage_backend_id") != STORAGE_BACKEND
            or not isinstance(rows_and_dimension, list)
            or len(rows_and_dimension) != 2
            or not isinstance(rows_and_dimension[0], int)
            or rows_and_dimension[0] < 1
            or rows_and_dimension[1] != VECTOR_DIMENSION
        ):
            raise RetrievalUnavailable("incompatible_generation")
        files = locale_manifest.get("files")
        if not isinstance(files, dict) or set(files) != {"vectors.f32", "chunks.json"}:
            raise RetrievalUnavailable("invalid_generation_metadata")
        vector_path = _regular_file(locale_root / "vectors.f32", "invalid_generation_metadata")
        chunks_path = _regular_file(locale_root / "chunks.json", "invalid_generation_metadata")
        for path, name in ((vector_path, "vectors.f32"), (chunks_path, "chunks.json")):
            expected = files[name]
            if (
                not isinstance(expected, dict)
                or path.stat().st_size != expected.get("byte_count")
                or _sha256(path) != expected.get("sha256")
            ):
                raise RetrievalUnavailable("invalid_generation_metadata")
        rows = rows_and_dimension[0]
        raw = vector_path.read_bytes()
        if len(raw) != rows * VECTOR_DIMENSION * 4:
            raise RetrievalUnavailable("invalid_generation_metadata")
        numpy = _numpy()
        vectors = numpy.frombuffer(raw, dtype="<f4").reshape(rows, VECTOR_DIMENSION)
        if not numpy.isfinite(vectors).all() or not numpy.allclose(
            numpy.linalg.norm(vectors, axis=1), 1.0, atol=1e-4
        ):
            raise RetrievalUnavailable("invalid_generation_metadata")
        metadata = _load_json(chunks_path)
        chunks = metadata.get("chunks")
        if metadata.get("locale") != locale or not isinstance(chunks, list) or len(chunks) != rows:
            raise RetrievalUnavailable("invalid_chunk_metadata")
        checked_chunks = [_validate_chunk(chunk, locale, self._bpm_version) for chunk in chunks]
        chunk_ids = [chunk["chunk_id"] for chunk in checked_chunks]
        if chunk_ids != sorted(chunk_ids) or len(chunk_ids) != len(set(chunk_ids)):
            raise RetrievalUnavailable("invalid_chunk_metadata")
        allowed_guides = frozenset(guide_ids) if guide_ids is not None else None
        eligible = [
            index
            for index, chunk in enumerate(checked_chunks)
            if allowed_guides is None or chunk["guide_id"] in allowed_guides
        ]
        scores = vectors @ query
        ordered = sorted(
            eligible, key=lambda index: (-float(scores[index]), checked_chunks[index]["chunk_id"])
        )[:limit]
        candidates = tuple(
            RetrievedEvidence(
                chunk_id=checked_chunks[index]["chunk_id"],
                ordinal=checked_chunks[index]["ordinal"],
                guide_id=checked_chunks[index]["guide_id"],
                documentation_version=checked_chunks[index]["documentation_version"],
                bpm_version=checked_chunks[index]["bpm_version"],
                source_sha256=checked_chunks[index]["source_sha256"],
                heading_path=tuple(checked_chunks[index]["heading_path"]),
                text=checked_chunks[index]["text"],
                score=float(scores[index]),
                citation=_citation(checked_chunks[index], locale),
                identifiers=tuple(checked_chunks[index]["identifiers"]),
            )
            for index in ordered
        )
        return RetrievalResult(generation_id, locale, candidates)
