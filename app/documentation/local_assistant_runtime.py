"""Release assembly for the verified local documentation-assistant dependencies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

from app.ai.e5_runtime import E5QueryEncoder, E5RuntimeError, verify_model_directory
from app.ai.local_inference_worker import LocalInferenceWorker
from app.ai.model_installation import ModelInstaller
from app.ai.runtime_installation import RuntimeInstaller
from app.core.config import Settings
from app.documentation.answer_validation import GenerationResponseValidator
from app.documentation.assistant_service import (
    AssistantSource,
    ControllerDocumentationAssistantService,
)
from app.documentation.conversation import GroundedConversationOrchestrator
from app.documentation.conversation_context import (
    ConversationContextStore,
    ConversationContextUnavailable,
)
from app.documentation.conversation_diagnostics import (
    AssistantDiagnosticsService,
    CompatibilitySnapshot,
)
from app.documentation.conversation_stream import ConversationStreamController
from app.documentation.evidence import EvidencePacker
from app.documentation.response_timing import LocalResponseTimeEstimator
from app.documentation.retrieval import SUPPORTED_LOCALES, ExactLocaleRetriever, LocalCitation
from app.documentation.topic_scope import CosineScopeSimilarity, ScopeLexicon, TopicScopeGate
from app.documentation.web_evidence import (
    ExternalWebCitation,
    ScopedWebEvidenceRetriever,
    WebEvidenceRateLimiter,
)
from app.documentation.web_evidence_consent import (
    WebEvidenceConfiguration,
    WebEvidenceModeStore,
)
from app.documentation.web_evidence_merge import (
    ConservativeEvidenceMerger,
    MergedGenerationResponseValidator,
    merged_generation_payload,
)


class LocalAssistantAssemblyError(RuntimeError):
    """Verified local assistant dependencies cannot form one safe release service."""


@dataclass
class LocalAssistantRuntime:
    service: ControllerDocumentationAssistantService
    worker: LocalInferenceWorker
    web_evidence_retriever: object

    def shutdown(self) -> None:
        self.service.shutdown()
        shutdown = getattr(self.web_evidence_retriever, "shutdown", None)
        if callable(shutdown):
            shutdown()
        self.worker.unload()


class LocalCitationResolver:
    """Resolve a completed local citation to reviewed display data, never raw index internals."""

    def __init__(self, index_root: Path) -> None:
        self._index_root = Path(index_root)

    def __call__(self, citation: LocalCitation) -> AssistantSource | None:
        parsed = urlsplit(citation.published_url)
        parts = parsed.path.split("/")
        if len(parts) < 4 or parts[1] != "help" or parts[2] not in SUPPORTED_LOCALES:
            return None
        locale = parts[2]
        try:
            pointer = json.loads(
                (self._index_root / "active-generation.json").read_text(encoding="utf-8")
            )
            generation_id = pointer["generation_id"]
            chunks = json.loads(
                (
                    self._index_root / "generations" / generation_id / locale / "chunks.json"
                ).read_text(encoding="utf-8")
            )["chunks"]
        except KeyError, OSError, json.JSONDecodeError:
            return None
        for chunk in chunks:
            if (
                chunk.get("topic_id") == citation.topic_id
                and chunk.get("anchor_id_or_root") == citation.anchor_id_or_root
            ):
                heading = chunk.get("heading_path")
                text = chunk.get("text")
                if not isinstance(heading, list) or not heading or not isinstance(text, str):
                    return None
                title = heading[-1]
                if not isinstance(title, str) or not title:
                    return None
                return AssistantSource(
                    citation.citation_id,
                    title,
                    citation.published_url,
                    locale,
                    text[:1200],
                )
        return None


class ReleaseCitationResolver:
    """Resolve only reviewed local or fixed-provider external citation metadata."""

    def __init__(self, index_root: Path) -> None:
        self._local = LocalCitationResolver(index_root)

    def __call__(self, citation: object) -> AssistantSource | None:
        if isinstance(citation, LocalCitation):
            return self._local(citation)
        if not isinstance(citation, ExternalWebCitation):
            return None
        if citation.locale not in SUPPORTED_LOCALES:
            return None
        return AssistantSource(
            source_id=citation.citation_id,
            title=citation.source_title,
            published_url=citation.source_url,
            locale=citation.locale,
            excerpt="",
            source_kind=citation.source_kind,
            provider_id=citation.provider_id,
        )


def _scope_centroids(encoder: E5QueryEncoder, lexicon: ScopeLexicon) -> dict[str, np.ndarray]:
    centroids: dict[str, np.ndarray] = {}
    for locale in SUPPORTED_LOCALES:
        vectors = encoder.encode_queries(list(lexicon.allowed_aliases[locale]))
        average = np.mean(vectors, axis=0)
        norm = float(np.linalg.norm(average))
        if not np.isfinite(average).all() or norm == 0.0:
            raise LocalAssistantAssemblyError("assistant_scope_centroids_unavailable")
        centroids[locale] = (average / norm).astype(np.float32)
    return centroids


def _verified_index(retriever: ExactLocaleRetriever, encoder: E5QueryEncoder) -> bool:
    try:
        probe = encoder("Browser Policy Manager documentation")
        return all(
            retriever.retrieve(locale=locale, query_vector=probe, limit=1).candidates
            for locale in SUPPORTED_LOCALES
        )
    except Exception:
        return False


def assemble_local_assistant(settings: Settings) -> LocalAssistantRuntime:
    """Construct the only local runtime after all persistent artifacts already exist."""

    ai_root = settings.DATA_DIR / "ai"
    embedding_dir = ai_root / "embeddings" / "multilingual-e5-base-onnx-o4"
    index_root = ai_root / "rag" / "index"
    try:
        verify_model_directory(embedding_dir)
        encoder = E5QueryEncoder(embedding_dir)
        retriever = ExactLocaleRetriever(index_root, bpm_version=settings.APP_VERSION)
        index_ready = _verified_index(retriever, encoder)
        if not index_ready:
            raise LocalAssistantAssemblyError("assistant_rag_generation_unavailable")
        lexicon = ScopeLexicon.from_contract(
            settings.ROOT_DIR / "documentation/config/bpm-topic-scope-gate-contract-0.9.3.json"
        )
    except (E5RuntimeError, ValueError) as error:
        raise LocalAssistantAssemblyError(str(error)) from error

    context_store = ConversationContextStore()

    def context_entities(request: object) -> tuple[str, ...]:
        session_id = getattr(request, "session_id", None)
        locale = getattr(request, "locale", None)
        if not isinstance(session_id, str) or not isinstance(locale, str):
            return ()
        try:
            return context_store.snapshot(
                session_id=session_id, locale=locale, bpm_version=settings.APP_VERSION
            ).resolved_entities
        except ConversationContextUnavailable:
            return ()

    scope_gate = TopicScopeGate(
        lexicon=lexicon,
        similarity=CosineScopeSimilarity(
            query_encoder=encoder,
            intent_centroids=_scope_centroids(encoder, lexicon),
        ),
        context_entities=context_entities,
    )
    worker = LocalInferenceWorker.for_default_installation(enabled=True)
    web_configuration = WebEvidenceConfiguration.from_settings(settings)
    web_mode_store = WebEvidenceModeStore(configuration=web_configuration)
    web_retriever = ScopedWebEvidenceRetriever(
        configuration=web_configuration,
        mode_store=web_mode_store,
        scope_gate=scope_gate,
        rate_limiter=WebEvidenceRateLimiter(),
    )
    generation_validator = GenerationResponseValidator()
    orchestrator = GroundedConversationOrchestrator(
        scope_gate=scope_gate,
        query_encoder=encoder,
        retriever=retriever,
        evidence_packer=EvidencePacker(encoder.count_tokens, bpm_version=settings.APP_VERSION),
        worker=worker,
        generation_parser=generation_validator,
        quotation_rewriter=generation_validator,
        context_store=context_store,
        web_evidence_retriever=web_retriever,
        evidence_merger=ConservativeEvidenceMerger(),
        merged_generation_validator=MergedGenerationResponseValidator(),
        merged_generation_payload_builder=merged_generation_payload,
        bpm_version=settings.APP_VERSION,
    )
    controller = ConversationStreamController(
        orchestrator=orchestrator,
        cancel_generation=worker.cancel,
        time_preview_estimator=LocalResponseTimeEstimator(worker.timing_profile),
    )
    model_verified = ModelInstaller(ai_root / "models").verify().verified
    runtime_verified = RuntimeInstaller(ai_root / "runtime").verify().verified
    diagnostics = AssistantDiagnosticsService(
        compatibility_provider=lambda: CompatibilitySnapshot(
            configuration_compatible=True,
            model_compatible=model_verified and runtime_verified,
            index_compatible=index_ready,
        ),
        worker_health_provider=worker.health,
        queue_depth_provider=controller,
        web_availability_provider=lambda: (
            "available"
            if web_configuration.availability_code == "assistant_web_available"
            else "local_only"
        ),
    )
    return LocalAssistantRuntime(
        service=ControllerDocumentationAssistantService(
            controller=controller,
            context_store=context_store,
            diagnostics=diagnostics,
            bpm_version=settings.APP_VERSION,
            source_resolver=ReleaseCitationResolver(index_root),
            web_mode_store=web_mode_store,
        ),
        worker=worker,
        web_evidence_retriever=web_retriever,
    )
