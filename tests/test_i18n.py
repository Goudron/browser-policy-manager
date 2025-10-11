from app.i18n import translate


def test_translate_fallback_to_en(monkeypatch):
    def fake_catalogs():
        return {
            "en": {"a": {"b": "Hello"}},
            "ru": {},
        }

    monkeypatch.setattr("app.i18n.catalogs", lambda: fake_catalogs())

    assert translate("a.b", lang="ru") == "Hello"
    assert translate("a.missing", lang="ru", default="X") == "X"
    assert translate("missing.key", lang="ru").endswith("missing.key")
