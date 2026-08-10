from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from app.documentation import local_assistant_runtime as runtime
from app.documentation.retrieval import LocalCitation
from app.documentation.web_evidence import ExternalWebCitation


def _citation(locale: str = "en") -> LocalCitation:
    return LocalCitation("local-1", f"/help/{locale}/user/overview.html", "overview", "root")


def test_local_citation_resolver_returns_only_valid_reviewed_chunk(tmp_path: Path) -> None:
    resolver = runtime.LocalCitationResolver(tmp_path)
    assert resolver(_citation("xx")) is None
    generation = tmp_path / "generations/gen/en"
    generation.mkdir(parents=True)
    (tmp_path / "active-generation.json").write_text('{"generation_id":"gen"}', encoding="utf-8")
    (generation / "chunks.json").write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "topic_id": "overview",
                        "anchor_id_or_root": "root",
                        "heading_path": ["Overview"],
                        "text": "Reviewed text",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source = resolver(_citation())
    assert source is not None and source.title == "Overview" and source.excerpt == "Reviewed text"


def test_release_resolver_accepts_only_reviewed_citation_kinds(tmp_path: Path) -> None:
    resolver = runtime.ReleaseCitationResolver(tmp_path)
    assert resolver(object()) is None
    trusted = ExternalWebCitation(
        "web", "provider", "https://example.test", "Title", (), "now", locale="en"
    )
    unknown_locale = ExternalWebCitation(
        "web", "provider", "https://example.test", "Title", (), "now", locale="xx"
    )
    assert resolver(trusted) is not None
    assert resolver(unknown_locale) is None


class _Encoder:
    def __init__(self, vector: np.ndarray) -> None:
        self.vector = vector

    def encode_queries(self, values: list[str]) -> np.ndarray:
        return np.stack([self.vector for _ in values])

    def __call__(self, question: str) -> np.ndarray:
        return self.vector


def test_scope_centroids_and_verified_index_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    aliases = {locale: ("BPM",) for locale in runtime.SUPPORTED_LOCALES}
    lexicon = runtime.ScopeLexicon(aliases, aliases, aliases, (), 0.5, 0.2)
    centroids = runtime._scope_centroids(_Encoder(np.array([3.0, 4.0], dtype=np.float32)), lexicon)  # type: ignore[arg-type]
    assert all(np.isclose(np.linalg.norm(vector), 1.0) for vector in centroids.values())
    with pytest.raises(runtime.LocalAssistantAssemblyError, match="centroids"):
        runtime._scope_centroids(_Encoder(np.zeros(2, dtype=np.float32)), lexicon)  # type: ignore[arg-type]

    class Retriever:
        def retrieve(self, *, locale: str, query_vector: np.ndarray, limit: int):
            return type("Result", (), {"candidates": (locale,)})()

    assert runtime._verified_index(Retriever(), _Encoder(np.ones(2, dtype=np.float32)))  # type: ignore[arg-type]

    class BrokenRetriever:
        def retrieve(self, **kwargs: object) -> object:
            raise RuntimeError("broken")

    assert not runtime._verified_index(BrokenRetriever(), _Encoder(np.ones(2, dtype=np.float32)))  # type: ignore[arg-type]


def test_local_citation_resolver_rejects_invalid_metadata_and_unmatched_chunks(
    tmp_path: Path,
) -> None:
    resolver = runtime.LocalCitationResolver(tmp_path)
    (tmp_path / "active-generation.json").write_text("not json", encoding="utf-8")
    assert resolver(_citation()) is None
    (tmp_path / "active-generation.json").write_text('{"generation_id":"gen"}', encoding="utf-8")
    generation = tmp_path / "generations/gen/en"
    generation.mkdir(parents=True)
    (generation / "chunks.json").write_text('{"chunks": []}', encoding="utf-8")
    assert resolver(_citation()) is None
    (generation / "chunks.json").write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "topic_id": "overview",
                        "anchor_id_or_root": "root",
                        "heading_path": [],
                        "text": "text",
                    },
                    {
                        "topic_id": "other",
                        "anchor_id_or_root": "root",
                        "heading_path": ["Other"],
                        "text": "text",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    assert resolver(_citation()) is None
    (generation / "chunks.json").write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "topic_id": "overview",
                        "anchor_id_or_root": "root",
                        "heading_path": [""],
                        "text": "text",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert resolver(_citation()) is None
    (generation / "chunks.json").write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "topic_id": "other",
                        "anchor_id_or_root": "root",
                        "heading_path": ["Other"],
                        "text": "text",
                    },
                    {
                        "topic_id": "overview",
                        "anchor_id_or_root": "root",
                        "heading_path": ["Overview"],
                        "text": "text",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    assert resolver(_citation()) is not None
    assert runtime.ReleaseCitationResolver(tmp_path)(_citation()) is not None


def test_runtime_assembly_wires_only_verified_local_dependencies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, object] = {}

    class Encoder:
        def __init__(self, path: Path) -> None:
            calls["encoder_path"] = path

        def count_tokens(self, value: str) -> int:
            return len(value)

        def __call__(self, _: str) -> np.ndarray:
            return np.ones(2, dtype=np.float32)

    class Worker:
        timing_profile = SimpleNamespace()

        def __init__(self) -> None:
            self.unloaded = 0

        @classmethod
        def for_default_installation(cls, *, enabled: bool) -> Worker:
            assert enabled is True
            worker = cls()
            calls["worker"] = worker
            return worker

        def cancel(self, _: str) -> bool:
            return True

        def health(self) -> object:
            return SimpleNamespace()

        def unload(self) -> None:
            self.unloaded += 1

    class Lexicon:
        @classmethod
        def from_contract(cls, path: Path) -> object:
            calls["contract"] = path
            return object()

    class ScopeGate:
        def __init__(self, **kwargs: object) -> None:
            calls["scope_gate"] = self
            calls["context_entities"] = kwargs["context_entities"]

    class WebConfiguration:
        availability_code = "assistant_web_available"

        @classmethod
        def from_settings(cls, settings: object) -> WebConfiguration:
            calls["web_settings"] = settings
            return cls()

    class VerifiedInstaller:
        def __init__(self, root: Path) -> None:
            calls.setdefault("installer_roots", []).append(root)  # type: ignore[union-attr]

        def verify(self) -> object:
            return SimpleNamespace(verified=True)

    class Capture:
        def __init__(self, *args: object, **kwargs: object) -> None:
            calls.setdefault("captures", []).append((args, kwargs))  # type: ignore[union-attr]

        def __call__(self, *_: object, **__: object) -> object:
            return self

        def clear_all(self) -> None:
            return None

    monkeypatch.setattr(runtime, "verify_model_directory", lambda _: None)
    monkeypatch.setattr(runtime, "E5QueryEncoder", Encoder)
    monkeypatch.setattr(runtime, "ExactLocaleRetriever", Capture)
    monkeypatch.setattr(runtime, "_verified_index", lambda *_: True)
    monkeypatch.setattr(runtime, "ScopeLexicon", Lexicon)
    monkeypatch.setattr(runtime, "_scope_centroids", lambda *_: {"en": np.ones(2)})
    monkeypatch.setattr(runtime, "CosineScopeSimilarity", Capture)
    monkeypatch.setattr(runtime, "TopicScopeGate", ScopeGate)
    monkeypatch.setattr(runtime, "LocalInferenceWorker", Worker)
    monkeypatch.setattr(runtime, "WebEvidenceConfiguration", WebConfiguration)
    monkeypatch.setattr(runtime, "WebEvidenceModeStore", Capture)
    monkeypatch.setattr(runtime, "ScopedWebEvidenceRetriever", Capture)
    monkeypatch.setattr(runtime, "WebEvidenceRateLimiter", Capture)
    monkeypatch.setattr(runtime, "GenerationResponseValidator", Capture)
    monkeypatch.setattr(runtime, "EvidencePacker", Capture)
    monkeypatch.setattr(runtime, "GroundedConversationOrchestrator", Capture)
    monkeypatch.setattr(runtime, "ConservativeEvidenceMerger", Capture)
    monkeypatch.setattr(runtime, "MergedGenerationResponseValidator", Capture)
    monkeypatch.setattr(runtime, "ConversationStreamController", Capture)
    monkeypatch.setattr(runtime, "LocalResponseTimeEstimator", Capture)
    monkeypatch.setattr(runtime, "ModelInstaller", VerifiedInstaller)
    monkeypatch.setattr(runtime, "RuntimeInstaller", VerifiedInstaller)
    monkeypatch.setattr(runtime, "AssistantDiagnosticsService", Capture)

    settings = SimpleNamespace(
        DATA_DIR=tmp_path / "data",
        ROOT_DIR=tmp_path / "root",
        APP_VERSION="0.9.3",
    )
    assembled = runtime.assemble_local_assistant(settings)  # type: ignore[arg-type]
    assert isinstance(assembled.service, runtime.ControllerDocumentationAssistantService)
    assert assembled.worker is calls["worker"]
    assert calls["encoder_path"] == tmp_path / "data/ai/embeddings/multilingual-e5-base-onnx-o4"
    context_store = next(
        kwargs["context_store"]
        for _, kwargs in calls["captures"]  # type: ignore[index]
        if "context_store" in kwargs
    )
    session_id = context_store.create(locale="en", bpm_version="0.9.3")  # type: ignore[union-attr]
    context_entities = calls["context_entities"]
    assert context_entities(SimpleNamespace()) == ()  # type: ignore[operator]
    assert context_entities(SimpleNamespace(session_id=session_id, locale="en")) == ()  # type: ignore[operator]
    assert context_entities(SimpleNamespace(session_id="missing", locale="en")) == ()  # type: ignore[operator]
    assembled.shutdown()
    assert assembled.worker.unloaded == 1  # type: ignore[union-attr]


def test_runtime_assembly_translates_model_and_contract_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = SimpleNamespace(DATA_DIR=tmp_path, ROOT_DIR=tmp_path, APP_VERSION="0.9.3")
    monkeypatch.setattr(
        runtime,
        "verify_model_directory",
        lambda _: (_ for _ in ()).throw(runtime.E5RuntimeError("missing_model")),
    )
    with pytest.raises(runtime.LocalAssistantAssemblyError, match="missing_model"):
        runtime.assemble_local_assistant(settings)  # type: ignore[arg-type]

    monkeypatch.setattr(runtime, "verify_model_directory", lambda _: None)
    monkeypatch.setattr(runtime, "E5QueryEncoder", lambda _: object())
    monkeypatch.setattr(runtime, "ExactLocaleRetriever", lambda *_, **__: object())
    monkeypatch.setattr(runtime, "_verified_index", lambda *_: False)
    with pytest.raises(runtime.LocalAssistantAssemblyError, match="rag_generation"):
        runtime.assemble_local_assistant(settings)  # type: ignore[arg-type]

    monkeypatch.setattr(runtime, "_verified_index", lambda *_: True)
    monkeypatch.setattr(
        runtime.ScopeLexicon,
        "from_contract",
        lambda _: (_ for _ in ()).throw(ValueError("invalid_contract")),
    )
    with pytest.raises(runtime.LocalAssistantAssemblyError, match="invalid_contract"):
        runtime.assemble_local_assistant(settings)  # type: ignore[arg-type]


def test_runtime_shutdown_releases_service_web_state_and_worker_in_order() -> None:
    calls: list[str] = []

    class Service:
        def shutdown(self) -> None:
            calls.append("service")

    class Retriever:
        def shutdown(self) -> None:
            calls.append("web")

    class Worker:
        def unload(self) -> None:
            calls.append("worker")

    assembled = runtime.LocalAssistantRuntime(Service(), Worker(), Retriever())  # type: ignore[arg-type]
    assembled.shutdown()

    assert calls == ["service", "web", "worker"]
