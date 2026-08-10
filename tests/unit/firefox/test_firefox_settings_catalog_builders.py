from app.web.firefox_settings_catalog import builders


def test_known_pref_includes_value_when_explicitly_provided():
    item = builders.known_pref(
        "browser.test.pref",
        "Browser Test Pref",
        "Helpful description",
        value="strict",
    )

    assert item["value"] == "strict"


def test_value_option_includes_label_key_when_present():
    item = builders.value_option("strict", "Strict", label_key="profiles.strict")

    assert item["label_key"] == "profiles.strict"
