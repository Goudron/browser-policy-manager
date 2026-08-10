from __future__ import annotations

import json

from tools import locale_inventory


def _write_catalogs(i18n_dir):
    i18n_dir.mkdir()
    catalogs = {
        "en": {
            "a.title": "Title",
            "b.count": "Total: {count}",
            "c.long": "Long source text",
        },
        "ru": {
            "a.title": "Title",
            "b.count": "Всего: {total}",
            "c.long": "Длинный текст",
        },
        "de": {
            "a.title": "Titel",
            "b.count": "Gesamt: {count}",
            "c.long": "Langer Text",
        },
        "zh-CN": {
            "a.title": "标题",
            "b.count": "总计：{count}",
            "c.long": "长文本",
        },
        "fr": {
            "a.title": "Titre",
            "b.count": "Total : {count}",
            "c.long": "Texte long",
        },
        "es-ES": {
            "a.title": "Título",
            "b.count": "Total: {count}",
            "c.long": "Texto largo",
        },
    }
    for locale, catalog in catalogs.items():
        (i18n_dir / f"{locale}.json").write_text(
            json.dumps(catalog, ensure_ascii=False),
            encoding="utf-8",
        )


def test_locale_inventory_reports_key_placeholder_and_unchanged_metrics(tmp_path):
    i18n_dir = tmp_path / "i18n"
    _write_catalogs(i18n_dir)
    ownership = tmp_path / "ownership.md"
    ownership.write_text(
        "\n".join(
            [
                "There is no separate translator team.",
                "| Area | Owner | Current process |",
                "|---|---|---|",
                "| English source copy | Project maintainer | Source review. |",
                "| Russian localization | Project maintainer | Manual review. |",
            ]
        ),
        encoding="utf-8",
    )

    report = locale_inventory.build_locale_inventory(
        i18n_dir=i18n_dir,
        ownership_path=ownership,
        longest_limit=2,
    )

    assert report["source_locale"] == "en"
    assert report["source_key_count"] == 3
    assert report["active_locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert report["catalogs"]["en"]["key_count"] == 3
    assert report["catalogs"]["ru"]["placeholder_mismatch_count"] == 1
    assert report["catalogs"]["ru"]["placeholder_mismatches"] == {
        "b.count": {"source": ["{count}"], "target": ["{total}"]}
    }
    assert report["catalogs"]["ru"]["unchanged_from_source_keys"] == ["a.title"]
    assert report["catalogs"]["de"]["unchanged_from_source_count"] == 0
    assert report["catalogs"]["fr"]["longest_strings"][0]["key"] == "b.count"
    assert report["ownership"]["model"] == "single-maintainer"
    assert report["ownership"]["locales"]["en"] == "Source review."
    assert report["ownership"]["locales"]["ru"] == "Manual review."


def test_locale_inventory_reports_missing_ownership_document(tmp_path):
    i18n_dir = tmp_path / "i18n"
    _write_catalogs(i18n_dir)

    report = locale_inventory.build_locale_inventory(
        i18n_dir=i18n_dir,
        ownership_path=tmp_path / "missing.md",
    )

    assert report["ownership"] == {"document": None, "model": "unknown", "locales": {}}
