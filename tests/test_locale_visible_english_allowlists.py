import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
ALLOWLIST_DOC_PATH = (
    REPO_ROOT / "docs" / "locale_visible_english_allowlists_2026-05-30.md"
)
PLACEHOLDER_RULES_PATH = (
    REPO_ROOT / "docs" / "locale_placeholder_identifier_rules_2026-05-29.md"
)


CONTRACT_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "locale_contracts" / "visible_english_allowlists.json"
)

CONTRACT = json.loads(CONTRACT_FIXTURE_PATH.read_text(encoding="utf-8"))

LOCALES = tuple(CONTRACT["locales"])
CORPORATE_CIS_L2_VISIBLE_KEYS = tuple(CONTRACT["corporate_cis_l2_visible_keys"])
ALLOWED_SHARED_ENGLISH_PHRASES = set(CONTRACT["allowed_shared_english_phrases"])
LATIN_TECHNICAL_TERMS = set(CONTRACT["latin_technical_terms"])
COMMON_UNTRANSLATED_PROSE_FRAGMENTS = tuple(
    CONTRACT["common_untranslated_prose_fragments"]
)
LOCALE_ALLOWED_EXAMPLES = {
    locale: tuple(examples)
    for locale, examples in CONTRACT["locale_allowed_examples"].items()
}
LOCALE_FORBIDDEN_FRAGMENTS = {
    locale: tuple(fragments)
    for locale, fragments in CONTRACT["locale_forbidden_fragments"].items()
}
AUDITED_KEYS = {
    locale: tuple(keys) for locale, keys in CONTRACT["audited_keys"].items()
}


def test_visible_english_contract_fixture_has_locale_sections():
    assert set(LOCALES) == set(LOCALE_ALLOWED_EXAMPLES)
    assert set(LOCALES) == set(LOCALE_FORBIDDEN_FRAGMENTS)
    assert set(LOCALES) == set(AUDITED_KEYS)
    assert CORPORATE_CIS_L2_VISIBLE_KEYS
    assert ALLOWED_SHARED_ENGLISH_PHRASES
    assert LATIN_TECHNICAL_TERMS


def _load_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _english_source_phrases(value: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*", value)
    phrases = set()
    for size in (4, 3, 2):
        for index in range(len(words) - size + 1):
            phrase = " ".join(words[index : index + size])
            if any(allowed in phrase or phrase in allowed for allowed in ALLOWED_SHARED_ENGLISH_PHRASES):
                continue
            phrases.add(phrase)
    return phrases


def _all_english_source_phrases(value: str) -> set[str]:
    allowed_terms = {term.lower() for term in LATIN_TECHNICAL_TERMS}
    source_words = [
        word
        for word in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*", value)
        if word.lower() not in allowed_terms
    ]
    phrases = set()
    for size in (5, 4, 3, 2):
        for index in range(len(source_words) - size + 1):
            phrase = " ".join(source_words[index : index + size])
            if any(
                allowed.lower() in phrase.lower()
                or phrase.lower() in allowed.lower()
                for allowed in ALLOWED_SHARED_ENGLISH_PHRASES
            ):
                continue
            phrases.add(phrase)
    return phrases


def _without_placeholders(value: str) -> str:
    return re.sub(r"\{[^}]+\}", "", value)


def _unapproved_visible_english_fragments(text: str, locale: str) -> list[str]:
    fragments = list(COMMON_UNTRANSLATED_PROSE_FRAGMENTS)
    fragments.extend(LOCALE_FORBIDDEN_FRAGMENTS[locale])
    return [fragment for fragment in fragments if fragment in text]


def test_visible_english_allowlist_document_records_locale_contract():
    allowlist = ALLOWLIST_DOC_PATH.read_text(encoding="utf-8")
    rules = PLACEHOLDER_RULES_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-306`" in allowlist
    assert "without being treated as untranslated prose" in allowlist
    assert "full-catalog source-phrase reuse" in allowlist
    assert "Flag ordinary English commands or prose" in allowlist
    assert "docs/locale_visible_english_allowlists_2026-05-30.md" in rules

    for locale in LOCALES:
        assert f"| `{locale}` |" in allowlist

    for term in CONTRACT["allowlist_doc_required_allowed_terms"]:
        assert term in allowlist

    for term in CONTRACT["allowlist_doc_required_forbidden_terms"]:
        assert term in allowlist


def test_locale_visible_english_allowlists_accept_documented_technical_examples():
    for locale, examples in LOCALE_ALLOWED_EXAMPLES.items():
        for example in examples:
            assert _unapproved_visible_english_fragments(example, locale) == []


def test_locale_visible_english_allowlists_reject_ordinary_untranslated_prose():
    for locale in LOCALES:
        sample = "Open profile. Save changes. Use this when setup needs a Task-first setup."

        unexpected = _unapproved_visible_english_fragments(sample, locale)

        assert "Open profile" in unexpected
        assert "Save changes" in unexpected
        assert "Use this when" in unexpected
        assert "Task-first setup" in unexpected


def test_audited_locale_surfaces_do_not_contain_forbidden_english_fragments():
    for locale, keys in AUDITED_KEYS.items():
        catalog = _load_catalog(locale)
        audited_text = "\n".join(catalog[key] for key in keys)

        assert _unapproved_visible_english_fragments(audited_text, locale) == []


def test_compare_locale_terms_match_dedicated_ownerless_interface_copy():
    expected = {
        "ru": {
            "profiles.compare_route_eyebrow": "Отдельное сравнение",
            "profiles.compare_route_title": "Сравнить настройки профилей",
            "profiles.compare_left_label": "Профиль A",
            "profiles.compare_right_label": "Профиль B",
            "profiles.compare_search_placeholder": "Найти профиль по имени",
            "profiles.compare_selection_title": "Выберите профили для сравнения",
            "profiles.compare_settings_title": "Настройки рядом",
            "profiles.compare_table_empty": "Выберите профиль A и профиль B, чтобы сравнить их настройки.",
            "profiles.compare_table_no_settings": "В этих профилях нет настроек для сравнения.",
            "profiles.compare_profile_empty": "Профиль не выбран",
            "profiles.compare_setting_column": "Настройка",
            "profiles.compare_left_column": "Значение профиля A",
            "profiles.compare_right_column": "Значение профиля B",
            "profiles.compare_state_missing": "Отсутствует",
            "profiles.compare_state_equal": "То же значение",
            "profiles.compare_state_different": "Другое значение",
            "profiles.compare_kind_policy": "Политика",
            "profiles.compare_kind_preference": "Управляемая настройка",
            "profiles.compare_action": "Сравнить здесь",
        },
        "de": {
            "profiles.compare_route_eyebrow": "Eigener Vergleich",
            "profiles.compare_route_title": "Profileinstellungen vergleichen",
            "profiles.compare_left_label": "Profil A",
            "profiles.compare_right_label": "Profil B",
            "profiles.compare_search_placeholder": "Profil nach Name suchen",
            "profiles.compare_selection_title": "Profile zum Vergleichen wählen",
            "profiles.compare_settings_title": "Einstellungen nebeneinander",
            "profiles.compare_table_empty": "Wählen Sie Profil A und Profil B aus, um ihre Einstellungen zu vergleichen.",
            "profiles.compare_table_no_settings": "Keines der Profile hat Einstellungen zum Vergleichen.",
            "profiles.compare_profile_empty": "Kein Profil ausgewählt",
            "profiles.compare_setting_column": "Einstellung",
            "profiles.compare_left_column": "Wert von Profil A",
            "profiles.compare_right_column": "Wert von Profil B",
            "profiles.compare_state_missing": "Fehlt",
            "profiles.compare_state_equal": "Gleicher Wert",
            "profiles.compare_state_different": "Anderer Wert",
            "profiles.compare_kind_policy": "Richtlinie",
            "profiles.compare_kind_preference": "Verwaltete Einstellung",
            "profiles.compare_action": "Hier vergleichen",
            "profiles.compare_selected": "Derzeit verglichen",
        },
        "zh-CN": {
            "profiles.compare_route_eyebrow": "专用比较",
            "profiles.compare_route_title": "比较配置档案设置",
            "profiles.compare_left_label": "配置档案甲",
            "profiles.compare_right_label": "配置档案乙",
            "profiles.compare_search_placeholder": "按名称查找配置档案",
            "profiles.compare_selection_title": "选择要比较的配置档案",
            "profiles.compare_settings_title": "并排查看设置",
            "profiles.compare_table_empty": "选择配置档案甲和配置档案乙以比较它们的设置。",
            "profiles.compare_table_no_settings": "两个配置档案都没有可比较的设置。",
            "profiles.compare_profile_empty": "未选择配置档案",
            "profiles.compare_setting_column": "设置",
            "profiles.compare_left_column": "配置档案甲的值",
            "profiles.compare_right_column": "配置档案乙的值",
            "profiles.compare_state_missing": "缺失",
            "profiles.compare_state_equal": "值相同",
            "profiles.compare_state_different": "值不同",
            "profiles.compare_kind_policy": "策略",
            "profiles.compare_kind_preference": "托管首选项",
            "profiles.compare_action": "在此比较",
            "profiles.compare_selected": "当前正在比较",
        },
        "fr": {
            "profiles.compare_route_eyebrow": "Comparaison dédiée",
            "profiles.compare_route_title": "Comparer les paramètres des profils",
            "profiles.compare_left_label": "Profil A",
            "profiles.compare_right_label": "Profil B",
            "profiles.compare_search_placeholder": "Rechercher un profil par nom",
            "profiles.compare_selection_title": "Choisir les profils à comparer",
            "profiles.compare_settings_title": "Paramètres côte à côte",
            "profiles.compare_table_empty": "Choisissez le profil A et le profil B pour comparer leurs paramètres.",
            "profiles.compare_table_no_settings": "Aucun des deux profils ne contient de paramètres à comparer.",
            "profiles.compare_profile_empty": "Aucun profil sélectionné",
            "profiles.compare_setting_column": "Paramètre",
            "profiles.compare_left_column": "Valeur du profil A",
            "profiles.compare_right_column": "Valeur du profil B",
            "profiles.compare_state_missing": "Manquant",
            "profiles.compare_state_equal": "Même valeur",
            "profiles.compare_state_different": "Valeur différente",
            "profiles.compare_kind_policy": "Politique",
            "profiles.compare_kind_preference": "Préférence gérée",
            "profiles.compare_action": "Comparer ici",
            "profiles.compare_selected": "Comparaison en cours",
        },
        "es-ES": {
            "profiles.compare_route_eyebrow": "Comparación dedicada",
            "profiles.compare_route_title": "Comparar ajustes de perfiles",
            "profiles.compare_left_label": "Perfil A",
            "profiles.compare_right_label": "Perfil B",
            "profiles.compare_search_placeholder": "Buscar un perfil por nombre",
            "profiles.compare_selection_title": "Elija perfiles para comparar",
            "profiles.compare_settings_title": "Ajustes en paralelo",
            "profiles.compare_table_empty": "Elija el perfil A y el perfil B para comparar sus ajustes.",
            "profiles.compare_table_no_settings": "Ninguno de los perfiles tiene ajustes para comparar.",
            "profiles.compare_profile_empty": "Ningún perfil seleccionado",
            "profiles.compare_setting_column": "Ajuste",
            "profiles.compare_left_column": "Valor del perfil A",
            "profiles.compare_right_column": "Valor del perfil B",
            "profiles.compare_state_missing": "Falta",
            "profiles.compare_state_equal": "Mismo valor",
            "profiles.compare_state_different": "Valor diferente",
            "profiles.compare_kind_policy": "Política",
            "profiles.compare_kind_preference": "Preferencia gestionada",
            "profiles.compare_action": "Comparar aquí",
            "profiles.compare_selected": "Comparado actualmente",
        },
    }
    stale_fragments = (
        "owner",
        "Owner",
        "No owner",
        "Left profile",
        "Right profile",
        "Left value",
        "Right value",
        "Settings comparison",
        "Not set",
        "comparerd",
        "comparard",
        "Currently compared",
        "Compare here",
    )

    for locale, expected_terms in expected.items():
        catalog = _load_catalog(locale)
        for key, value in expected_terms.items():
            assert catalog[key] == value

        compare_text = "\n".join(
            value for key, value in catalog.items() if key.startswith("profiles.compare_")
        )
        for fragment in stale_fragments:
            assert fragment not in compare_text


def test_corporate_cis_l2_visible_locale_strings_do_not_reuse_english_source_phrases():
    english_catalog = _load_catalog("en")
    source_phrases = {
        key: _english_source_phrases(english_catalog[key])
        for key in CORPORATE_CIS_L2_VISIBLE_KEYS
    }

    failures = []
    for locale in LOCALES:
        catalog = _load_catalog(locale)
        for key, phrases in source_phrases.items():
            reused = sorted(phrase for phrase in phrases if phrase in catalog[key])
            if reused:
                failures.append(f"{locale}:{key}: {', '.join(reused[:5])}")

    assert failures == []


def test_non_english_catalogs_do_not_reuse_english_source_phrases():
    english_catalog = _load_catalog("en")
    source_phrases = {
        key: _all_english_source_phrases(value)
        for key, value in english_catalog.items()
    }

    failures = []
    for locale in LOCALES:
        catalog = _load_catalog(locale)
        for key, phrases in source_phrases.items():
            text = _without_placeholders(catalog[key])
            reused = sorted(
                phrase for phrase in phrases if phrase.lower() in text.lower()
            )
            if reused:
                failures.append(f"{locale}:{key}: {', '.join(reused[:5])}")

    assert failures == []


def test_simplified_chinese_catalog_keeps_latin_to_allowed_terms_only():
    catalog = _load_catalog("zh-CN")
    failures = []
    allowed_terms = {term.lower() for term in LATIN_TECHNICAL_TERMS}

    for key, value in catalog.items():
        text = _without_placeholders(value)
        if "://" in text or "@" in text:
            continue
        unexpected = sorted(
            {
                word
                for word in re.findall(
                    r"[A-Za-z][A-Za-z0-9]*(?:[-/][A-Za-z0-9]+)*",
                    text,
                )
                if word.lower() not in allowed_terms
                and not re.fullmatch(r"[A-Z]{2,}", word)
            }
        )
        if unexpected:
            failures.append(f"{key}: {', '.join(unexpected[:5])}")

    assert failures == []
