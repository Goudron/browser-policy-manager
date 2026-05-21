from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = REPO_ROOT / "docs" / "ui_locale_glossary_en_ru_2026-05-15.md"


def test_ui_locale_glossary_records_current_en_ru_terms():
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    required_terms = (
        "Browser Policy Manager",
        "Менеджер профилей браузера",
        "Guided editor",
        "Пошаговый редактор",
        "All settings",
        "Все настройки",
        "JSON editor",
        "JSON-редактор",
        "Profile library",
        "Библиотека профилей",
        "Mozilla account",
        "аккаунт Mozilla",
        "Cookies",
        "Куки",
        "Add-ons",
        "Дополнения",
        "Address bar",
        "Адресная строка",
        "Site permissions",
        "Разрешения сайтов",
        "Managed preferences",
        "Управляемые параметры",
        "Outside Guided editor",
        "Вне Пошагового редактора",
        "policies.json",
        "ИИ и умные функции",
    )
    for term in required_terms:
        assert term in glossary

    assert "Do not use `Расширенные настройки`" in glossary
    assert "Mozilla Pontoon and SUMO" in glossary
