"""Deterministic pre-generation relevance filtering for local RAG candidates."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from app.documentation.retrieval import SUPPORTED_LOCALES, RetrievalResult, RetrievedEvidence

if TYPE_CHECKING:
    from app.documentation.conversation import ConversationRequest

_WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")
_WORD: Final[re.Pattern[str]] = re.compile(r"[^\W\d_]+", re.UNICODE)
_MIXED_IDENTIFIER: Final[re.Pattern[str]] = re.compile(
    r"\b(?:[A-Z]{2,}[A-Za-z0-9_-]*|[A-Z][a-z]+[A-Z][A-Za-z0-9_-]*)\b"
)
_BPM_VERSION: Final[re.Pattern[str]] = re.compile(
    r"\bbpm\s+(?:version\s+)?(\d+(?:\.\d+){1,3})\b", re.IGNORECASE
)

_PLATFORM_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "ubuntu": ("ubuntu",),
    "debian": ("debian",),
    "linux_mint": ("linux mint", "mint"),
    "windows": ("windows",),
    "macos": ("macos", "mac os"),
    "fedora": ("fedora",),
    "rhel": ("rhel", "red hat", "redhat"),
}
_ROLE_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "administrator": (
        "administrator",
        "admin",
        "devops",
        "администратор",
        "админ",
        "разработчик",
        "管理员",
        "运维",
        "administrateur",
        "administrador",
    ),
    "user": ("user", "reader", "пользователь", "用户", "utilisateur", "usuario"),
}
_GUIDE_MARKERS: Final[dict[str, tuple[str, ...]]] = {
    "administrator": ("admin",),
    "user": ("user",),
}
_STOP_WORDS: Final[dict[str, frozenset[str]]] = {
    "en": frozenset(
        {
            "about",
            "and",
            "are",
            "can",
            "for",
            "from",
            "how",
            "i",
            "in",
            "is",
            "my",
            "of",
            "on",
            "question",
            "the",
            "to",
            "what",
            "with",
            "you",
        }
    ),
    "ru": frozenset(
        {"в", "вы", "и", "как", "ли", "на", "о", "по", "про", "с", "ты", "у", "что", "это"}
    ),
    "de": frozenset(
        {
            "auf",
            "das",
            "der",
            "die",
            "du",
            "ein",
            "eine",
            "für",
            "ich",
            "im",
            "ist",
            "kann",
            "mit",
            "und",
            "was",
            "wie",
            "zu",
        }
    ),
    "zh-CN": frozenset(),
    "fr": frozenset(
        {
            "avec",
            "comment",
            "des",
            "en",
            "et",
            "je",
            "la",
            "le",
            "les",
            "peux",
            "pour",
            "quel",
            "que",
            "sur",
            "un",
            "une",
            "vous",
        }
    ),
    "es-ES": frozenset(
        {
            "con",
            "cómo",
            "de",
            "el",
            "en",
            "la",
            "las",
            "los",
            "me",
            "para",
            "puedo",
            "qué",
            "una",
            "un",
            "y",
        }
    ),
}
_ZH_TOPIC_TERMS: Final[tuple[str, ...]] = (
    "安装",
    "配置",
    "策略",
    "配置文件",
    "工作流",
    "验证",
    "导入",
    "导出",
    "搜索",
)


@dataclass(frozen=True)
class RelevanceDecision:
    """A filtered same-locale result, or a terminal reason before evidence packing."""

    result: RetrievalResult
    reason_code: str


@dataclass(frozen=True)
class _Constraints:
    topic_terms: tuple[str, ...]
    identifiers: tuple[str, ...]
    platforms: tuple[str, ...]
    platform_releases: tuple[tuple[str, str], ...]
    roles: tuple[str, ...]
    bpm_versions: tuple[str, ...]


class EvidenceRelevanceGate:
    """Reject candidates that conflict with explicit request context before generation."""

    def filter(self, request: ConversationRequest, result: RetrievalResult) -> RelevanceDecision:
        if request.locale not in SUPPORTED_LOCALES or result.locale != request.locale:
            return RelevanceDecision(
                replace(result, candidates=()), "assistant_relevance_locale_mismatch"
            )
        if not result.candidates:
            return RelevanceDecision(result, "assistant_relevance_ready")
        constraints = _constraints(request.locale, request.question)
        candidates = tuple(
            candidate for candidate in result.candidates if _matches(candidate, constraints)
        )
        if not candidates:
            return RelevanceDecision(
                replace(result, candidates=()), "assistant_relevance_no_matching_evidence"
            )
        return RelevanceDecision(
            replace(result, candidates=candidates), "assistant_relevance_ready"
        )


def _constraints(locale: str, question: str) -> _Constraints:
    normalized = _normalize(question)
    platforms = tuple(
        platform
        for platform, aliases in _PLATFORM_ALIASES.items()
        if any(alias in normalized for alias in aliases)
    )
    releases = tuple(
        (platform, match.group(1))
        for platform in platforms
        for match in (
            re.search(rf"\b{re.escape(alias)}\s+(\d+(?:\.\d+){{1,3}})\b", normalized)
            for alias in _PLATFORM_ALIASES[platform]
        )
        if match is not None
    )
    roles = tuple(
        role
        for role, aliases in _ROLE_ALIASES.items()
        if any(alias in normalized for alias in aliases)
    )
    versions = tuple(dict.fromkeys(_BPM_VERSION.findall(normalized)))
    identifiers = tuple(
        identifier.casefold()
        for identifier in _MIXED_IDENTIFIER.findall(question)
        if identifier.casefold() not in {"bpm", *platforms}
    )
    return _Constraints(
        _topic_terms(locale, normalized, platforms, roles, versions, identifiers),
        identifiers,
        platforms,
        releases,
        roles,
        versions,
    )


def _matches(candidate: RetrievedEvidence, constraints: _Constraints) -> bool:
    haystack = _haystack(candidate)
    words = frozenset(_WORD.findall(haystack))
    if any(
        not _contains_any(haystack, _PLATFORM_ALIASES[platform])
        for platform in constraints.platforms
    ):
        return False
    if any(
        not any(f"{alias} {release}" in haystack for alias in _PLATFORM_ALIASES[platform])
        for platform, release in constraints.platform_releases
    ):
        return False
    if any(
        not any(marker in _normalize(candidate.guide_id) for marker in _GUIDE_MARKERS[role])
        for role in constraints.roles
    ):
        return False
    candidate_versions = tuple(dict.fromkeys(_BPM_VERSION.findall(haystack)))
    if any(
        (candidate_versions and version not in candidate_versions)
        or (not candidate_versions and candidate.bpm_version != version)
        for version in constraints.bpm_versions
    ):
        return False
    identifiers = frozenset(_normalize(identifier) for identifier in candidate.identifiers)
    if any(
        identifier not in identifiers and identifier not in haystack
        for identifier in constraints.identifiers
    ):
        return False
    return not constraints.topic_terms or any(
        _topic_term_matches(term, words, haystack) for term in constraints.topic_terms
    )


def _topic_terms(
    locale: str,
    normalized: str,
    platforms: tuple[str, ...],
    roles: tuple[str, ...],
    versions: tuple[str, ...],
    identifiers: tuple[str, ...],
) -> tuple[str, ...]:
    if locale == "zh-CN":
        return tuple(term for term in _ZH_TOPIC_TERMS if term in normalized)
    excluded = {"bpm", *platforms, *roles, *versions, *identifiers}
    excluded.update(alias for aliases in _PLATFORM_ALIASES.values() for alias in aliases)
    excluded.update(alias for aliases in _ROLE_ALIASES.values() for alias in aliases)
    return tuple(
        word
        for word in _WORD.findall(normalized)
        if len(word) >= 4 and word not in _STOP_WORDS[locale] and word not in excluded
    )


def _topic_term_matches(term: str, words: frozenset[str], haystack: str) -> bool:
    if term in words or term in haystack:
        return True
    return len(term) >= 5 and any(
        word.startswith(term[:5]) or term.startswith(word[:5]) for word in words if len(word) >= 5
    )


def _haystack(candidate: RetrievedEvidence) -> str:
    return _normalize(
        " ".join(
            (
                candidate.guide_id,
                candidate.citation.topic_id,
                *candidate.heading_path,
                *candidate.identifiers,
                candidate.text,
            )
        )
    )


def _contains_any(value: str, aliases: tuple[str, ...]) -> bool:
    return any(alias in value for alias in aliases)


def _normalize(value: str) -> str:
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", value).casefold()).strip()
