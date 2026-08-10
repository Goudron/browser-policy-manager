"""Locale-owned release notice while local-model training is deferred beyond 0.9.3."""

from __future__ import annotations

from typing import Final

from app.documentation.assistant_contracts import SUPPORTED_LOCALES

_NOTICES: Final[dict[str, str]] = {
    "en": (
        "The local model is currently being trained. This functionality will be available in one of the following versions."
    ),
    "ru": (
        "В настоящий момент происходит обучение локальной модели. Ожидайте данную функциональность в одной из следующих версий."
    ),
    "de": (
        "Das lokale Modell wird derzeit trainiert. Diese Funktion wird in einer der kommenden Versionen verfügbar sein."
    ),
    "zh-CN": "本地模型目前正在训练。该功能将在后续版本之一中提供。",
    "fr": (
        "Le modèle local est actuellement en cours d’entraînement. Cette fonctionnalité sera disponible dans l’une des prochaines versions."
    ),
    "es-ES": (
        "El modelo local se está entrenando actualmente. Esta funcionalidad estará disponible en una de las próximas versiones."
    ),
}


def training_notice(locale: str) -> str:
    """Return the reviewed release notice for one supported documentation locale."""

    if locale not in SUPPORTED_LOCALES:
        raise ValueError("assistant_unsupported_locale")
    return _NOTICES[locale]
