from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation" / "src" / "dita"
STYLE_POLICY = ROOT / "docs" / "architecture" / "documentation-locale-editorial-style-0.9.2.md"
RUSSIAN_REVIEW = ROOT / "docs" / "architecture" / "documentation-russian-heading-review-0.9.2.md"
GERMAN_REVIEW = ROOT / "docs" / "architecture" / "documentation-german-heading-review-0.9.2.md"
CHINESE_REVIEW = ROOT / "docs" / "architecture" / "documentation-zh-cn-heading-review-0.9.2.md"
FRENCH_REVIEW = ROOT / "docs" / "architecture" / "documentation-french-heading-review-0.9.2.md"
SPANISH_REVIEW = ROOT / "docs" / "architecture" / "documentation-spanish-heading-review-0.9.2.md"

pytestmark = pytest.mark.docs_contract

IMPERATIVE_PATTERNS = {
    "ru": re.compile(
        r"^(?:Изменить|Выбрать|Настроить|Открыть|Создать|Проверить|"
        r"Использовать|Добавить|Удалить|Сохранить|Экспортировать|"
        r"Импортировать|Восстановить|Записать|Подготовить|Запустить|"
        r"Перейти|Найти|Сравнить|Отформатировать|Применить|Переключить|"
        r"Отследить|Обновить|Устранить|Дублировать|Архивировать|"
        r"Проследить|Планировать|Оценить|Синхронизировать|"
        r"Измените|Выберите|Настройте|Откройте|Создайте|Проверьте|"
        r"Используйте|Добавьте|Удалите|Сохраните|Экспортируйте|"
        r"Импортируйте|Восстановите|Запишите|Подготовьте|Запустите|"
        r"Перейдите|Найдите|Сравните|Отформатируйте|Планируйте|"
        r"Извлекайте|Ознакомьтесь|Пройдите|Установите|Устраните|"
        r"Введите|Подтвердите|Примените)\b"
    ),
    "de": re.compile(r"\b(?:Sie|Ihnen)\b"),
    "fr": re.compile(
        r"^(?:Choisissez|Sélectionnez|Utilisez|Enregistrez|Commencez|"
        r"Modifiez|Ouvrez|Créez|Vérifiez|Ajoutez|Supprimez|Exportez|"
        r"Importez|Préparez|Exécutez|Accédez|Recherchez|Comparez)\b"
    ),
    "es-ES": re.compile(
        r"^(?:Elija|Seleccione|Utilice|Ejecute|Prepare|Comience|Verifique|"
        r"Cambie|Modifique|Abra|Cree|Compruebe|Agregue|Elimine|Guarde|"
        r"Exporte|Importe|Vaya|Busque|Compare)\b"
    ),
}


def _titles(locale: str) -> list[tuple[Path, str]]:
    titles: list[tuple[Path, str]] = []
    for path in sorted((DITA_ROOT / locale).rglob("*.dita")):
        root = ET.parse(path).getroot()
        for title in root.iter("title"):
            value = "".join(title.itertext()).strip()
            if value:
                titles.append((path.relative_to(ROOT), value))
    for path in sorted((DITA_ROOT / locale / "maps").glob("*.ditamap")):
        root = ET.parse(path).getroot()
        for element in (root.find("title"), *root.iter("navtitle")):
            if element is None:
                continue
            value = "".join(element.itertext()).strip()
            if value:
                titles.append((path.relative_to(ROOT), value))
    return titles


def test_locale_editorial_style_policy_records_independent_conventions() -> None:
    policy = STYLE_POLICY.read_text(encoding="utf-8")

    for required_fragment in (
        "`en`",
        "`ru`",
        "`de`",
        "`zh-CN`",
        "`fr`",
        "`es-ES`",
        "not a grammar or word-order template",
        "`Изменение языка интерфейса`",
        "`Einen Firefox-Schemakanal auswählen`",
        "`选择 Firefox 架构通道`",
        "`Changer la langue de l’interface`",
        "`Cambiar el idioma de la interfaz`",
        "locale-terminology-authority-0.9.1.json",
        "https://gramota.ru/",
        "https://www.duden.de/",
        "https://std.samr.gov.cn/",
        "https://www.academie-francaise.fr/",
        "https://www.rae.es/",
    ):
        assert required_fragment in policy


def test_russian_heading_review_records_normalized_titles_and_no_exceptions() -> None:
    review = RUSSIAN_REVIEW.read_text(encoding="utf-8")

    for required_fragment in (
        "Accepted exceptions: none.",
        "`Настройка раздела «Идентификация профиля» и канала схемы`",
        "`Рекомендации CIS в BPM`",
        "`Шесть шагов режима «Пошаговый редактор»`",
        "`Устранение несоответствия схемы`",
        "Russian-language product-owner review",
    ):
        assert required_fragment in review

    violations = [(str(path), title) for path, title in _titles("ru") if title.endswith(".")]
    assert violations == []


def test_german_heading_review_records_native_titles_and_ui_names() -> None:
    review = GERMAN_REVIEW.read_text(encoding="utf-8")

    for required_fragment in (
        "Accepted exceptions: none.",
        "`Prüfstatus in „Alle Einstellungen“`",
        "`Einstellungen im Modus „Geführter Editor“ durchsuchen`",
        "`Einen Schema-Konflikt beheben`",
        "German-language product-owner review",
    ):
        assert required_fragment in review

    titles = _titles("de")
    violations = [
        (str(path), title)
        for path, title in titles
        if title.endswith(".")
        or any(
            fragment in title
            for fragment in ("Rohrichtlinien", "Suchgeführte", "Schemainkongruenz")
        )
    ]
    assert violations == []


def test_simplified_chinese_heading_review_preserves_terms_and_compact_titles() -> None:
    review = CHINESE_REVIEW.read_text(encoding="utf-8")

    for required_fragment in (
        "Accepted exceptions: none.",
        "`选择 Firefox 架构通道`",
        "`“所有设置”中的审核状态`",
        "`浏览“引导式编辑器”的六个步骤`",
        "Simplified-Chinese product-owner review",
    ):
        assert required_fragment in review

    chinese_word_spacing = re.compile(r"[\u4e00-\u9fff]\s+[\u4e00-\u9fff]")
    violations = [
        (str(path), title)
        for path, title in _titles("zh-CN")
        if chinese_word_spacing.search(title) or title.endswith("。") or "个人资料" in title
    ]
    assert violations == []


def test_french_heading_review_preserves_infinitives_and_ui_names() -> None:
    review = FRENCH_REVIEW.read_text(encoding="utf-8")

    for required_fragment in (
        "Accepted exceptions: none.",
        "`Choix de l’interface BPM adaptée`",
        "`États de revue dans « Tous les paramètres »`",
        "`Parcourir les six étapes de l’« Éditeur guidé »`",
        "French-language product-owner review",
    ):
        assert required_fragment in review

    titles = _titles("fr")
    violations = [
        (str(path), title)
        for path, title in titles
        if title.endswith(".")
        or any(
            fragment in title
            for fragment in (
                "Tous les paramètres états",
                "Tous les paramètres éléments",
                "Paramètres guidés de recherche",
                "Parcourez les six étapes",
                "Règles et Préférences gérées",
            )
        )
    ]
    assert violations == []


def test_spanish_heading_review_preserves_infinitives_and_ui_names() -> None:
    review = SPANISH_REVIEW.read_text(encoding="utf-8")

    for required_fragment in (
        "Accepted exceptions: none.",
        "`Elección de la interfaz de BPM adecuada`",
        "`Estados de revisión en «Todos los ajustes»`",
        "`Navegar por los seis pasos del «Editor guiado»`",
        "Spanish-language product-owner review",
    ):
        assert required_fragment in review

    titles = _titles("es-ES")
    violations = [
        (str(path), title)
        for path, title in titles
        if title.endswith(".")
        or any(
            fragment in title
            for fragment in (
                "Todos los ajustes estados",
                "Todos los ajustes elementos",
                "Navega por los seis pasos",
                "Búsqueda de configuraciones guiadas",
                "Políticas y Preferencias gestionadas",
            )
        )
    ]
    assert violations == []


@pytest.mark.parametrize("locale", sorted(IMPERATIVE_PATTERNS))
def test_localized_dita_headings_use_the_locale_standard(locale: str) -> None:
    pattern = IMPERATIVE_PATTERNS[locale]
    violations = [(str(path), title) for path, title in _titles(locale) if pattern.search(title)]

    assert violations == []
