from __future__ import annotations

import json
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = DOCUMENTATION_ROOT / "config" / "topic-section-taxonomy-0.9.1.json"
LABELS = DOCUMENTATION_ROOT / "config" / "topic-section-labels-0.9.1.json"
LOCALES = ["en", "ru", "de", "zh-CN", "fr", "es-ES"]

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _taxonomy_sections() -> dict[str, dict]:
    return {
        section["label_key"]: section
        for document in _json(TAXONOMY)["documents"]
        for section in document["sections"]
    }


def test_topic_section_label_catalog_declares_m8_04_scope() -> None:
    catalog = _json(LABELS)

    assert catalog["schema_version"] == 1
    assert catalog["catalog_id"] == "bpm-0.9.1-topic-section-labels"
    assert catalog["target_bpm_version"] == "0.9.1"
    assert catalog["backlog_item"] == "BPM091-M8-04"
    assert catalog["status"] == "accepted"
    assert catalog["locales"] == LOCALES
    assert "must never use the English value as a runtime fallback" in catalog[
        "fallback_policy"
    ]


def test_every_taxonomy_section_owns_every_locale_label() -> None:
    catalog = _json(LABELS)
    sections = _taxonomy_sections()

    assert set(catalog["labels"]) == set(sections)
    assert len(sections) == 19
    for label_key, localized in catalog["labels"].items():
        assert list(localized) == LOCALES
        assert all(value.strip() for value in localized.values())
        assert localized["en"] == sections[label_key]["canonical_label"]
        assert all(localized[locale] != localized["en"] for locale in LOCALES[1:])


def test_section_labels_use_product_locale_terminology() -> None:
    labels = _json(LABELS)["labels"]

    assert labels["navigation.section.user-guide.guided-editor"] == {
        "en": "Configure profiles in Guided editor",
        "ru": "Настройка профиля в режиме «Пошаговый редактор»",
        "de": "Profile im Modus „Geführter Editor“ konfigurieren",
        "zh-CN": "使用引导式编辑器进行配置",
        "fr": "Configurer des profils dans l’« Éditeur guidé »",
        "es-ES": "Configurar perfiles en «Editor guiado»",
    }
    assert labels["navigation.section.administrator-guide.requirements-and-scope"] == {
        "en": "System requirements and delivery scope",
        "ru": "Системные требования и границы поставки",
        "de": "Systemanforderungen und Lieferumfang",
        "zh-CN": "系统要求和交付范围",
        "fr": "Configuration requise et périmètre de livraison",
        "es-ES": "Requisitos del sistema y alcance de la entrega",
    }


def test_non_english_section_labels_do_not_contain_canonical_english_phrases() -> None:
    catalog = _json(LABELS)
    forbidden = (
        "profile work",
        "create and start",
        "configure with",
        "review and filter",
        "edit setting",
        "handle advanced",
        "work with",
        "find and manage",
        "compare profiles",
        "recover safely",
        "source deployment",
        "update from source",
        "integration foundations",
        "health and scenarios",
        "control product workflows",
        "troubleshooting",
        "production readiness",
    )

    for localized in catalog["labels"].values():
        for locale in LOCALES[1:]:
            value = localized[locale].casefold()
            assert not any(fragment in value for fragment in forbidden)
