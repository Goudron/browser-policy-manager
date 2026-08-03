"""Strict model-output and server-side citation validation for local documentation chat."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Final
from urllib.parse import urlsplit

from app.ai.local_inference_worker import InferenceResult
from app.documentation.content_boundary import contains_active_content
from app.documentation.conversation import ParsedGeneration, QuotationRewriteCandidate
from app.documentation.evidence import EvidencePack
from app.documentation.retrieval import LocalCitation

MAX_MODEL_RESPONSE_BYTES: Final[int] = 16 * 1024
MAX_ANSWER_CHARACTERS: Final[int] = 4_000
MAX_ANSWER_SECTIONS: Final[int] = 6
MAX_SECTION_CHARACTERS: Final[int] = 1_200
# A model may use a product term or a short documented command verbatim, but it must not turn one
# of the retrieved chunks into the answer.  The comparison is deliberately Unicode/whitespace
# normalised so that reflowing an extract does not evade the boundary; it does not attempt to
# decide semantic entailment, which remains the responsibility of the reviewed evidence and the
# section-level citation binding below.
MAX_EXTRACTIVE_SPAN_CHARACTERS: Final[int] = 96
_CITATION_ID: Final[re.Pattern[str]] = re.compile(r"topic:[A-Za-z0-9._:-]+(?:#[A-Za-z0-9._:-]+)?")
_MARKUP: Final[re.Pattern[str]] = re.compile(r"<[^>\n]{1,256}>")
_CONTROL: Final[re.Pattern[str]] = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")


@dataclass(frozen=True)
class CitationResolution:
    """One exact source resolved only from the accepted active evidence pack."""

    citation_id: str
    citation: LocalCitation


@dataclass(frozen=True)
class _AnswerSections:
    """Private structural assessment before the extractive-span gate is applied."""

    text: str
    citation_ids: tuple[str, ...]
    contains_excessive_quote: bool


class GenerationResponseValidator:
    """Parse one fixed JSON response shape and fail closed to a terminal disposition."""

    def __call__(self, result: InferenceResult, evidence: EvidencePack) -> ParsedGeneration:
        return self.validate(result, evidence)

    def validate(self, result: InferenceResult, evidence: EvidencePack) -> ParsedGeneration:
        """Return only a citation-bound response or a safe terminal fallback."""

        approved = self._approved_citations(evidence)
        if result.locale != evidence.locale or not approved:
            return self._abstain("assistant_citation_context_invalid")
        payload = self._parse_object(result.text)
        if payload is None:
            return self._abstain("assistant_output_invalid")
        disposition = payload.get("disposition")
        sections = payload.get("sections")
        if disposition not in {"answer", "clarify", "abstain", "refuse"}:
            return self._abstain("assistant_output_invalid")
        if not isinstance(sections, list):
            return self._abstain("assistant_output_invalid")
        if disposition == "answer":
            return self._answer(sections, approved, evidence)
        if sections:
            return self._abstain("assistant_output_invalid")
        if disposition == "clarify":
            return ParsedGeneration("clarify", "", (), (), "assistant_clarify")
        if disposition == "abstain":
            return ParsedGeneration("abstain", "", (), (), "assistant_abstain")
        return ParsedGeneration("refuse", "", (), (), "assistant_refuse")

    def candidate_for_excessive_quote(
        self, result: InferenceResult, evidence: EvidencePack
    ) -> QuotationRewriteCandidate | None:
        """Return a private rewrite input only after every non-quotation check passes."""

        approved = self._approved_citations(evidence)
        if result.locale != evidence.locale or not approved:
            return None
        payload = self._parse_object(result.text)
        if payload is None or payload.get("disposition") != "answer":
            return None
        sections = payload.get("sections")
        if not isinstance(sections, list):
            return None
        assessed = self._assess_answer_sections(sections, approved, evidence)
        if assessed is None or not assessed.contains_excessive_quote:
            return None
        return QuotationRewriteCandidate(assessed.text, assessed.citation_ids)

    @staticmethod
    def _parse_object(raw: str) -> dict[str, object] | None:
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_MODEL_RESPONSE_BYTES:
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict) or set(value) != {"disposition", "sections"}:
            return None
        return value

    def _answer(
        self,
        sections: list[object],
        approved: dict[str, LocalCitation],
        evidence: EvidencePack,
    ) -> ParsedGeneration:
        assessed = self._assess_answer_sections(sections, approved, evidence)
        if assessed is None:
            return self._abstain("assistant_output_invalid")
        if assessed.contains_excessive_quote:
            return self._abstain("assistant_excessive_quotation")
        return ParsedGeneration(
            "answer", assessed.text, assessed.citation_ids, (), "assistant_citations_validated"
        )

    def _assess_answer_sections(
        self,
        sections: list[object],
        approved: dict[str, LocalCitation],
        evidence: EvidencePack,
    ) -> _AnswerSections | None:
        """Validate structure and citations, retaining only a private rewrite candidate if quoted."""

        if not 1 <= len(sections) <= MAX_ANSWER_SECTIONS:
            return None
        rendered_sections: list[str] = []
        citation_ids: list[str] = []
        contains_excessive_quote = False
        for section in sections:
            if not isinstance(section, dict) or set(section) != {"text", "citation_ids"}:
                return None
            text = section.get("text")
            raw_ids = section.get("citation_ids")
            if (
                not isinstance(text, str)
                or not text.strip()
                or len(text) > MAX_SECTION_CHARACTERS
                or not self._plain_text(text)
                or not isinstance(raw_ids, list)
                or not all(isinstance(item, str) for item in raw_ids)
            ):
                return None
            resolved = self._resolve_all(tuple(raw_ids), approved)
            if resolved is None:
                return None
            if self._contains_excessive_evidence_quote(text, resolved, evidence):
                contains_excessive_quote = True
            rendered_sections.append(text.strip())
            for citation in raw_ids:
                if citation not in citation_ids:
                    citation_ids.append(citation)
        answer = "\n\n".join(rendered_sections)
        if not answer or len(answer) > MAX_ANSWER_CHARACTERS:
            return None
        return _AnswerSections(answer, tuple(citation_ids), contains_excessive_quote)

    @staticmethod
    def _plain_text(text: str) -> bool:
        return (
            not _MARKUP.search(text)
            and not _CONTROL.search(text)
            and not contains_active_content(text)
        )

    def _approved_citations(self, evidence: EvidencePack) -> dict[str, LocalCitation]:
        approved: dict[str, LocalCitation] = {}
        for citation in evidence.citations:
            if not self._safe_local_citation(citation, evidence.locale):
                return {}
            if citation.citation_id in approved:
                return {}
            approved[citation.citation_id] = citation
        return approved

    @staticmethod
    def _safe_local_citation(citation: LocalCitation, locale: str) -> bool:
        if citation.source_kind != "local" or not _CITATION_ID.fullmatch(citation.citation_id):
            return False
        expected_id = f"topic:{citation.topic_id}"
        if citation.anchor_id_or_root != "root":
            expected_id = f"{expected_id}#{citation.anchor_id_or_root}"
        if citation.citation_id != expected_id:
            return False
        parsed = urlsplit(citation.published_url)
        return (
            not parsed.scheme
            and not parsed.netloc
            and not parsed.query
            and not parsed.fragment
            and parsed.path.startswith(f"/help/{locale}/")
            and ".." not in parsed.path.split("/")
            and "%" not in parsed.path
        )

    def _resolve_all(
        self, citation_ids: tuple[str, ...], approved: dict[str, LocalCitation]
    ) -> tuple[CitationResolution, ...] | None:
        if not citation_ids or len(set(citation_ids)) != len(citation_ids):
            return None
        resolved: list[CitationResolution] = []
        for citation_id in citation_ids:
            citation = approved.get(citation_id)
            if citation is None:
                return None
            resolved.append(CitationResolution(citation_id, citation))
        return tuple(resolved)

    @staticmethod
    def _contains_excessive_evidence_quote(
        text: str,
        citations: tuple[CitationResolution, ...],
        evidence: EvidencePack,
    ) -> bool:
        """Reject a long contiguous extract from an item supporting this answer section."""

        normalised_text = _WHITESPACE.sub(" ", text).strip().casefold()
        if len(normalised_text) < MAX_EXTRACTIVE_SPAN_CHARACTERS:
            return False
        supported_ids = {item.citation_id for item in citations}
        for item in evidence.evidence:
            if item.citation.citation_id not in supported_ids:
                continue
            source = _WHITESPACE.sub(" ", item.text).strip().casefold()
            for start in range(len(normalised_text) - MAX_EXTRACTIVE_SPAN_CHARACTERS + 1):
                span = normalised_text[start : start + MAX_EXTRACTIVE_SPAN_CHARACTERS]
                if span in source:
                    return True
        return False

    @staticmethod
    def _abstain(reason_code: str) -> ParsedGeneration:
        return ParsedGeneration("abstain", "", (), (), reason_code)
