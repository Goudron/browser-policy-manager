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
