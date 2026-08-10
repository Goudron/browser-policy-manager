"""Inert-data boundaries for retrieved documentation and model display text."""

from __future__ import annotations

import re
import unicodedata
from base64 import b64decode
from binascii import Error as BinasciiError
from urllib.parse import unquote

MAX_EVIDENCE_ITEM_BYTES = 8 * 1024
MAX_PACKED_EVIDENCE_BYTES = 24 * 1024
MAX_DECODED_CONTROL_BYTES = 512
EVIDENCE_DATA_BEGIN = "<BPM_UNTRUSTED_EVIDENCE_DATA>"
EVIDENCE_DATA_END = "</BPM_UNTRUSTED_EVIDENCE_DATA>"

_SCRIPT_OR_STYLE = re.compile(
    r"<(?:script|style)\b[^>]{0,512}>.*?</(?:script|style)\s*>", re.IGNORECASE | re.DOTALL
)
_HTML_TAG = re.compile(r"</?[a-z][^>\n]{0,512}>", re.IGNORECASE)
_MARKDOWN_LINK = re.compile(r"!?\[([^\]\n]{0,512})\]\([^\)\n]{0,2048}\)")
_ACTIVE_SCHEME = re.compile(r"\b(?:javascript|data|vbscript)\s*:", re.IGNORECASE)
_CONTROL_OR_BIDI = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]")
_PERCENT_ESCAPE = re.compile(r"%(?:[0-9a-f]{2})", re.IGNORECASE)
_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-f]{4})", re.IGNORECASE)
_BASE64_TOKEN = re.compile(r"(?:base64:)?([a-z0-9+/]{16,}={0,2})", re.IGNORECASE)
_CONTROL_OVERRIDE = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:ignore|disregard|override) (?:all |previous |bpm )?(?:instructions|rules)\b",
        r"\b(?:reveal|show) (?:the )?(?:system prompt|instructions)\b",
        r"\b(?:you are now|act as)\b",
        r"\b(?:enable|call|use) (?:tools|shell|network|web)\b",
        r"игнорируй (?:предыдущие )?(?:инструкции|правила)",
        r"(?:раскрой|покажи) (?:системный промпт|инструкции)",
        r"ты теперь",
        r"ignoriere (?:vorherige )?(?:anweisungen|regeln)",
        r"(?:zeige|verrate) (?:den )?(?:system-prompt|anweisungen)",
        r"du bist jetzt",
        r"忽略(?:之前|先前)?(?:指令|规则)",
        r"(?:透露|显示).{0,20}(?:系统提示|指令)",
        r"你现在是",
        r"ignore (?:les )?(?:instructions|règles)(?: précédentes)?",
        r"(?:révèle|montre) (?:le )?(?:prompt système|instructions)",
        r"tu es maintenant",
        r"ignora (?:las )?(?:instrucciones|reglas)(?: anteriores)?",
        r"(?:revela|muestra) (?:el )?(?:prompt del sistema|instrucciones)",
        r"ahora eres",
    )
)


def contains_active_content(value: str) -> bool:
    """Recognize markup or URL schemes that must never become active display content."""

    return bool(
        _SCRIPT_OR_STYLE.search(value)
        or _HTML_TAG.search(value)
        or _MARKDOWN_LINK.search(value)
        or _ACTIVE_SCHEME.search(value)
        or _CONTROL_OR_BIDI.search(value)
    )


def sanitize_evidence_text(value: str) -> str | None:
    """Return bounded inert text, or reject a hostile/oversized untrusted evidence field."""

    if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_EVIDENCE_ITEM_BYTES:
        return None
    unescaped = unicodedata.normalize("NFKC", unquote(value))
    inert = _SCRIPT_OR_STYLE.sub("", unescaped)
    inert = _MARKDOWN_LINK.sub(r"\1", inert)
    inert = _HTML_TAG.sub("", inert)
    inert = _ACTIVE_SCHEME.sub("", inert)
    inert = _CONTROL_OR_BIDI.sub("", inert)
    inert = " ".join(inert.split())
    candidates = (_normalized(inert), *_decoded_control_candidates(value))
    if any(_is_control_override(candidate) for candidate in candidates):
        return None
    if (
        not inert
        or EVIDENCE_DATA_BEGIN.casefold() in inert.casefold()
        or EVIDENCE_DATA_END.casefold() in inert.casefold()
        or len(inert.encode("utf-8")) > MAX_EVIDENCE_ITEM_BYTES
    ):
        return None
    return inert


def delimit_evidence_jsonl(value: str) -> str:
    """Mark canonical JSON Lines as data in the worker packet without reparsing it."""

    return f"{EVIDENCE_DATA_BEGIN}\n{value}\n{EVIDENCE_DATA_END}"


def _is_control_override(value: str) -> bool:
    return any(pattern.search(value) for pattern in _CONTROL_OVERRIDE)


def _decoded_control_candidates(value: str) -> tuple[str, ...]:
    candidates: list[str] = []
    if _PERCENT_ESCAPE.search(value):
        candidates.append(_normalized(unquote(value)))
    if _UNICODE_ESCAPE.search(value):
        candidates.append(_normalized(_UNICODE_ESCAPE.sub(_unicode_escape, value)))
    for token in _BASE64_TOKEN.findall(value):
        try:
            decoded = b64decode(token, validate=True)
        except BinasciiError, ValueError:
            continue
        if 0 < len(decoded) <= MAX_DECODED_CONTROL_BYTES:
            try:
                candidates.append(_normalized(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                continue
    normalized = _normalized(value)
    return tuple(candidate for candidate in candidates if candidate and candidate != normalized)


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _unicode_escape(match: re.Match[str]) -> str:
    return chr(int(match.group(1), 16))
