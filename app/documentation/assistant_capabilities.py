"""Reviewed deterministic answers about the BPM documentation assistant's scope."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from app.documentation.conversation import ConversationOutcome, ConversationRequest
from app.documentation.retrieval import SUPPORTED_LOCALES, LocalCitation

_WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")
_OVERVIEW_TOPIC_ID: Final[str] = "ug-concept-browser-policy-manager-overview"


@dataclass(frozen=True)
class CapabilityAnswer:
    """Locale-owned deterministic copy with its reviewed same-locale source."""

    aliases: tuple[str, ...]
    text: str


_ANSWERS: Final[dict[str, CapabilityAnswer]] = {
    "en": CapabilityAnswer(
        ("what questions can you answer", "what can you answer", "what can i ask", "what can you help with"),
        "I can answer questions about BPM settings, policies, profiles, and documented workflows. I use current documentation sources and may ask for clarification, abstain when evidence is insufficient, or refuse off-topic questions.",
    ),
    "ru": CapabilityAnswer(
        ("на какие вопросы ты можешь отвечать", "на какие вопросы вы можете отвечать", "что ты умеешь", "что вы умеете", "о чем можно спросить", "о чём можно спросить"),
        "Я отвечаю на вопросы о настройках, политиках, профилях и описанных рабочих процессах BPM. Использую актуальную документацию; могу попросить уточнение, воздержаться при недостатке сведений или отказать на вопрос не по теме.",
    ),
    "de": CapabilityAnswer(
        ("welche fragen kannst du beantworten", "welche fragen können sie beantworten", "wobei kannst du helfen", "was kann ich fragen"),
        "Ich beantworte Fragen zu BPM-Einstellungen, Richtlinien, Profilen und dokumentierten Arbeitsabläufen. Ich nutze aktuelle Dokumentationsquellen und kann um Präzisierung bitten, mich bei unzureichenden Belegen enthalten oder fachfremde Fragen ablehnen.",
    ),
    "zh-CN": CapabilityAnswer(
        ("你能回答哪些问题", "您能回答哪些问题", "你能帮什么", "我可以问什么"),
        "我可以回答有关 BPM 设置、策略、配置文件和已记录工作流的问题。我使用当前文档来源；信息不足时会请求澄清或暂不作答，并会拒绝与 BPM 无关的问题。",
    ),
    "fr": CapabilityAnswer(
        ("à quelles questions pouvez-vous répondre", "quelles questions peux-tu répondre", "avec quoi peux-tu m'aider", "que puis-je demander"),
        "Je peux répondre aux questions sur les paramètres, règles, profils et procédures documentées de BPM. J’utilise la documentation actuelle ; je peux demander une précision, m’abstenir si les preuves sont insuffisantes ou refuser les questions hors sujet.",
    ),
    "es-ES": CapabilityAnswer(
        ("qué preguntas puedes responder", "qué preguntas puede responder", "en qué puedes ayudar", "qué puedo preguntar"),
        "Puedo responder preguntas sobre la configuración, las políticas, los perfiles y los flujos de trabajo documentados de BPM. Uso fuentes de documentación actuales; puedo pedir una aclaración, abstenerme si faltan pruebas o rechazar preguntas ajenas al tema.",
    ),
}


def capability_answer(request: ConversationRequest) -> ConversationOutcome | None:
    """Return an exact reviewed answer without retrieval, inference or network activity."""

    if request.locale not in SUPPORTED_LOCALES or not isinstance(request.question, str):
        return None
    answer = _ANSWERS.get(request.locale)
    if answer is None:
        return None
    question = _normalize(request.question)
    if not question or not any(alias in question for alias in answer.aliases):
        return None
    citation = LocalCitation(
        f"topic:{_OVERVIEW_TOPIC_ID}#assistant",
        f"/help/{request.locale}/user/{_OVERVIEW_TOPIC_ID}.html",
        _OVERVIEW_TOPIC_ID,
        "assistant",
    )
    return ConversationOutcome(
        "answer", "assistant_capability_answer", request.locale, answer.text, (citation,)
    )


def _normalize(value: str) -> str:
    return _WHITESPACE.sub(" ", value.casefold()).strip()
