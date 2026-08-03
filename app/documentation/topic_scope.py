"""Deterministic, fail-closed BPM topic admission before retrieval or generation."""

from __future__ import annotations

import json
import re
import unicodedata
from base64 import b64decode
from binascii import Error as BinasciiError
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote

import numpy as np

from app.documentation.conversation import ConversationRequest, ScopeDecision
from app.documentation.retrieval import SUPPORTED_LOCALES

_POLICY_SHAPED_IDENTIFIER = re.compile(
    r"\b(?:api-[a-z]+-\d+|cis:\d+(?:\.\d+)+|[a-z][a-z0-9-]*(?:policy|setting)-\d+)\b",
    re.IGNORECASE,
)
_PERCENT_ESCAPE = re.compile(r"%(?:[0-9a-f]{2})", re.IGNORECASE)
_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-f]{4})", re.IGNORECASE)
_BASE64_TOKEN = re.compile(r"(?:base64:)?([a-z0-9+/]{16,}={0,2})", re.IGNORECASE)
_HEX_TOKEN = re.compile(r"(?:hex:)?\b([0-9a-f]{32,1024})\b", re.IGNORECASE)
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
MAX_DECODED_CONTROL_BYTES = 512

_CONTROL_ACTION_WORDS = frozenset(
    {
        "ignore",
        "reveal",
        "override",
        "bypass",
        "disregard",
        "delete",
        "игнорируй",
        "раскрой",
        "покажи",
        "удали",
        "ignoriere",
        "zeige",
        "verrate",
        "lösche",
        "révèle",
        "montre",
        "supprime",
        "ignora",
        "revela",
        "muestra",
        "borra",
    }
)
_CONTROL_TARGET_WORDS = frozenset(
    {
        "instructions",
        "rules",
        "prompt",
        "tools",
        "shell",
        "network",
        "files",
        "инструкции",
        "правила",
        "промпт",
        "инструменты",
        "сеть",
        "файлы",
        "anweisungen",
        "regeln",
        "werkzeuge",
        "netzwerk",
        "dateien",
        "règles",
        "outils",
        "réseau",
        "fichiers",
        "instrucciones",
        "reglas",
        "herramientas",
        "red",
        "archivos",
    }
)


class ScopeSimilarity(Protocol):
    """Compact semantic score boundary, supplied by the approved local embedding owner."""

    def score(self, *, locale: str, query: str) -> float: ...


ContextEntityProvider = Callable[[ConversationRequest], tuple[str, ...]]
QueryEncoder = Callable[[str], np.ndarray]


@dataclass(frozen=True)
class ScopeLexicon:
    """Reviewed deterministic aliases and refusal terms for all supported locales."""

    allowed_aliases: Mapping[str, tuple[str, ...]]
    refusal_aliases: Mapping[str, tuple[str, ...]]
    clarification_aliases: Mapping[str, tuple[str, ...]]
    adversarial_patterns: tuple[re.Pattern[str], ...]
    semantic_allow_threshold: float
    semantic_clarify_threshold: float

    @classmethod
    def from_contract(cls, path: Path) -> ScopeLexicon:
        """Load only the fixed, reviewed scope data; malformed data leaves construction unavailable."""

        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("scope lexicon contract is unavailable") from error
        if not isinstance(value, dict):
            raise ValueError("scope lexicon contract is invalid")
        aliases = value.get("lexical_aliases")
        thresholds = value.get("semantic_thresholds")
        if not isinstance(aliases, dict) or not isinstance(thresholds, dict):
            raise ValueError("scope lexicon contract is invalid")
        allowed = cls._locale_terms(aliases.get("allowed"))
        refused = cls._locale_terms(aliases.get("refuse"))
        clarify = cls._locale_terms(aliases.get("clarify"))
        adversarial = cls._adversarial_patterns(value.get("adversarial_patterns"))
        allow_threshold = thresholds.get("allow")
        clarify_threshold = thresholds.get("clarify")
        if (
            not isinstance(allow_threshold, float)
            or not isinstance(clarify_threshold, float)
            or not 0.0 <= clarify_threshold < allow_threshold <= 1.0
        ):
            raise ValueError("scope semantic thresholds are invalid")
        return cls(allowed, refused, clarify, adversarial, allow_threshold, clarify_threshold)

    @staticmethod
    def _locale_terms(value: object) -> dict[str, tuple[str, ...]]:
        if not isinstance(value, dict) or set(value) != set(SUPPORTED_LOCALES):
            raise ValueError("scope locale aliases are invalid")
        result: dict[str, tuple[str, ...]] = {}
        for locale, terms in value.items():
            if (
                not isinstance(terms, list)
                or not terms
                or not all(isinstance(term, str) and term.strip() for term in terms)
            ):
                raise ValueError("scope locale aliases are invalid")
            result[locale] = tuple(_normalize(term) for term in terms)
        return result

    @staticmethod
    def _adversarial_patterns(value: object) -> tuple[re.Pattern[str], ...]:
        if (
            not isinstance(value, list)
            or not 1 <= len(value) <= 32
            or not all(isinstance(pattern, str) and 1 <= len(pattern) <= 160 for pattern in value)
        ):
            raise ValueError("scope adversarial patterns are invalid")
        try:
            return tuple(re.compile(pattern, re.IGNORECASE) for pattern in value)
        except re.error as error:
            raise ValueError("scope adversarial patterns are invalid") from error


class CosineScopeSimilarity:
    """Score a query against fixed local intent centroids without retrieval or an LLM."""

    def __init__(
        self, *, query_encoder: QueryEncoder, intent_centroids: Mapping[str, np.ndarray]
    ) -> None:
        if set(intent_centroids) != set(SUPPORTED_LOCALES):
            raise ValueError("scope intent centroids must cover every supported locale")
        self._query_encoder = query_encoder
        self._intent_centroids = {
            locale: self._normalized(vector) for locale, vector in intent_centroids.items()
        }

    def score(self, *, locale: str, query: str) -> float:
        if locale not in self._intent_centroids:
            return 0.0
        vector = self._normalized(self._query_encoder(query))
        return max(0.0, float(np.dot(vector, self._intent_centroids[locale])))

    @staticmethod
    def _normalized(value: np.ndarray) -> np.ndarray:
        vector = np.asarray(value, dtype=np.float32)
        if vector.shape != (768,) or not np.isfinite(vector).all():
            raise ValueError("scope semantic vector is invalid")
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            raise ValueError("scope semantic vector is invalid")
        return vector / norm


class TopicScopeGate:
    """Resolve deterministic safeguards before consulting an injected local semantic score."""

    def __init__(
        self,
        *,
        lexicon: ScopeLexicon,
        similarity: ScopeSimilarity,
        context_entities: ContextEntityProvider = lambda _: (),
    ) -> None:
        self._lexicon = lexicon
        self._similarity = similarity
        self._context_entities = context_entities

    def __call__(self, request: ConversationRequest) -> ScopeDecision:
        """Return only allow/clarify/refuse; retrieval, inference and web access remain downstream."""

        if request.locale not in SUPPORTED_LOCALES or not isinstance(request.question, str):
            return ScopeDecision("refuse", "scope_invalid_request")
        query = _normalize(request.question)
        if not query:
            return ScopeDecision("refuse", "scope_invalid_request")
        if self._must_refuse(request.question):
            return ScopeDecision("refuse", "scope_off_topic_or_forbidden")
        if _POLICY_SHAPED_IDENTIFIER.search(query):
            return ScopeDecision("allow", "scope_policy_identifier")
        if self._contains(query, self._lexicon.allowed_aliases[request.locale]):
            return ScopeDecision("allow", "scope_bpm_anchor")
        entities = self._context_entities(request)
        if self._is_underspecified(query):
            if len(entities) == 1 and all(
                isinstance(entity, str) and entity for entity in entities
            ):
                return ScopeDecision("allow", "scope_context_follow_up")
            return ScopeDecision("clarify", "scope_clarify_context")
        if self._contains(query, self._lexicon.clarification_aliases[request.locale]):
            return ScopeDecision("clarify", "scope_clarify_bpm_boundary")
        try:
            score = self._similarity.score(locale=request.locale, query=request.question)
        except Exception:
            return ScopeDecision("refuse", "scope_similarity_unavailable")
        if not isinstance(score, float) or not np.isfinite(score) or not 0.0 <= score <= 1.0:
            return ScopeDecision("refuse", "scope_similarity_unavailable")
        if score >= self._lexicon.semantic_allow_threshold:
            return ScopeDecision("allow", "scope_semantic_bpm")
        if score >= self._lexicon.semantic_clarify_threshold:
            return ScopeDecision("clarify", "scope_clarify_bpm_boundary")
        return ScopeDecision("refuse", "scope_off_topic")

    def _must_refuse(self, raw_query: str) -> bool:
        if _has_unsafe_format_character(raw_query):
            return True
        candidates = (_normalize(raw_query), *self._decoded_control_candidates(raw_query))
        refusal_terms = self._all_terms(self._lexicon.refusal_aliases)
        return any(
            self._contains(candidate, refusal_terms)
            or any(pattern.search(candidate) for pattern in self._lexicon.adversarial_patterns)
            or _has_typoglycemia_override(candidate)
            for candidate in candidates
        )

    @staticmethod
    def _decoded_control_candidates(query: str) -> tuple[str, ...]:
        """Decode one bounded transport encoding layer solely to detect control-override content."""

        candidates: list[str] = []
        percent_candidate = query
        for _ in range(2):
            if not _PERCENT_ESCAPE.search(percent_candidate):
                break
            decoded_percent = unquote(percent_candidate)
            if decoded_percent == percent_candidate:
                break
            candidates.append(_normalize(decoded_percent))
            percent_candidate = decoded_percent
        if _UNICODE_ESCAPE.search(query):
            candidates.append(_normalize(_UNICODE_ESCAPE.sub(_unicode_escape, query)))
        for token in _BASE64_TOKEN.findall(query):
            try:
                decoded = b64decode(token, validate=True)
            except (BinasciiError, ValueError):
                continue
            if 0 < len(decoded) <= MAX_DECODED_CONTROL_BYTES:
                try:
                    candidates.append(_normalize(decoded.decode("utf-8")))
                except UnicodeDecodeError:
                    continue
        for token in _HEX_TOKEN.findall(query):
            if len(token) % 2:
                continue
            try:
                decoded = bytes.fromhex(token)
            except ValueError:
                continue
            if 0 < len(decoded) <= MAX_DECODED_CONTROL_BYTES:
                try:
                    candidates.append(_normalize(decoded.decode("utf-8")))
                except UnicodeDecodeError:
                    continue
        return tuple(candidate for candidate in candidates if candidate and candidate != query)

    @staticmethod
    def _contains(query: str, terms: tuple[str, ...]) -> bool:
        return any(term in query for term in terms)

    @staticmethod
    def _all_terms(aliases: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
        return tuple(term for terms in aliases.values() for term in terms)

    @staticmethod
    def _is_underspecified(query: str) -> bool:
        return query.rstrip("?.!。？！") in {
            "can i enable it",
            "does it support this",
            "можно ли это включить",
            "поддерживает ли это",
            "kann ich es aktivieren",
            "unterstützt es das",
            "我可以启用它吗",
            "它支持这个吗",
            "puis-je l’activer",
            "puis-je l'activer",
            "est-ce qu’il le prend en charge",
            "puedo activarlo",
            "lo admite",
        }


def _normalize(value: str) -> str:
    """Normalize without using ordinary-search code or changing its ranking behavior."""

    folded = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(folded.split())


def _unicode_escape(match: re.Match[str]) -> str:
    return chr(int(match.group(1), 16))


def _has_unsafe_format_character(value: str) -> bool:
    """Reject invisible/bidi control shaping before it can split an override token."""

    return any(
        unicodedata.category(character) == "Cf"
        or (unicodedata.category(character) == "Cc" and not character.isspace())
        for character in value
    )


def _has_typoglycemia_override(value: str) -> bool:
    """Catch a bounded scrambled action+target pair without fuzzy-admitting normal questions."""

    action = _word_set_match(_WORD.findall(value), _CONTROL_ACTION_WORDS)
    target = _word_set_match(_WORD.findall(value), _CONTROL_TARGET_WORDS)
    return action[0] and target[0] and (action[1] or target[1])


def _word_set_match(words: list[str], expected: frozenset[str]) -> tuple[bool, bool]:
    matched = False
    obfuscated = False
    for word in words:
        for candidate in expected:
            if word == candidate:
                matched = True
                continue
            if (
                len(word) == len(candidate)
                and len(word) >= 4
                and word[0] == candidate[0]
                and word[-1] == candidate[-1]
                and sorted(word[1:-1]) == sorted(candidate[1:-1])
            ):
                matched = True
                obfuscated = True
    return matched, obfuscated
