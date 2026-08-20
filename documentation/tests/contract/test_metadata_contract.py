from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
MODULE_PATH = DOCUMENTATION_ROOT / "tools/validate_metadata.py"
SPEC = importlib.util.spec_from_file_location("validate_metadata", MODULE_PATH)
assert SPEC and SPEC.loader
validate_metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_metadata)

LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDE_KEYS = {
    "guide.user-guide",
    "guide.firefox-policy-guide",
    "guide.cis-settings-guide",
    "guide.administrator-guide",
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

pytestmark = pytest.mark.docs_contract


def test_vocabulary_uses_fixed_dita_attributes_and_maintained_dynamic_registries() -> None:
    vocabulary = validate_metadata.load_vocabulary()

    assert set(vocabulary["attributes"]) == {
        "audience",
        "platform",
        "product",
        "deliveryTarget",
        "props",
    }
    assert vocabulary["attributes"]["deliveryTarget"] == [f"locale-{locale}" for locale in LOCALES]
    assert vocabulary["attributes"]["props"] == [
        "firefox-release",
        "firefox-esr",
        "cis-level-1",
        "cis-level-2",
    ]
    assert {group: len(values) for group, values in vocabulary["registry_values"].items()} == {
        "policy": 123,
        "cis": 55,
        "api-operation": 17,
    }


def test_subject_scheme_enumerates_every_fixed_vocabulary_value_once() -> None:
    vocabulary = json.loads(
        (DOCUMENTATION_ROOT / "config/metadata-vocabulary.json").read_text(encoding="utf-8")
    )
    root = ET.parse(DOCUMENTATION_ROOT / "src/shared/metadata-subject-scheme.ditamap").getroot()
    subject_roots = {element.attrib["keys"]: element for element in root.findall("subjectdef")}
    enumeration_roots = {
        definition.find("attributedef").attrib["name"]: (
            definition.find("subjectdef").attrib["keyref"]
        )
        for definition in root.findall("enumerationdef")
    }
    expected_roots = {
        "audience": "audiences",
        "platform": "platforms",
        "product": "bpm-versions",
        "deliveryTarget": "locales",
        "props": "conditions",
    }

    assert enumeration_roots == expected_roots
    for attribute, subject_root in expected_roots.items():
        values = [element.attrib["keys"] for element in subject_roots[subject_root]]
        assert values == vocabulary["attributes"][attribute]


@pytest.mark.parametrize("locale", LOCALES)
def test_locale_key_maps_resolve_guides_and_shared_subject_scheme(locale: str) -> None:
    root = ET.parse(DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/keys.ditamap").getroot()

    assert root.attrib == {"id": "map-keys", XML_LANG: locale}
    scheme = root.find("mapref")
    assert scheme is not None
    assert scheme.attrib == {
        "href": "../../../shared/metadata-subject-scheme.ditamap",
        "format": "ditamap",
        "processing-role": "resource-only",
    }
    keydefs = [element.attrib for element in root.findall("keydef")]
    guide_keydefs = [
        definition for definition in keydefs if definition["keys"].startswith("guide.")
    ]
    topic_keydefs = [
        definition for definition in keydefs if definition["keys"].startswith("topic.")
    ]
    assert {definition["keys"] for definition in guide_keydefs} == GUIDE_KEYS
    assert all(set(definition) == {"keys"} for definition in guide_keydefs)
    assert topic_keydefs
    assert all(set(definition) == {"keys", "href"} for definition in topic_keydefs)
    for definition in topic_keydefs:
        assert definition["href"].startswith(("../user/", "../firefox/", "../cis/", "../admin/"))
        assert definition["href"].endswith(".dita")
        assert (
            (DOCUMENTATION_ROOT / f"src/dita/{locale}/maps" / definition["href"])
            .resolve()
            .is_file()
        )


def test_filters_select_one_firefox_channel_and_one_locale_without_source_copies() -> None:
    filters = DOCUMENTATION_ROOT / "src/shared/filters"
    release = ET.parse(filters / "firefox-release.ditaval").getroot().findall("prop")
    esr = ET.parse(filters / "firefox-esr.ditaval").getroot().findall("prop")
    assert [element.attrib for element in release] == [
        {"action": "exclude", "att": "props", "val": "firefox-esr"}
    ]
    assert [element.attrib for element in esr] == [
        {"action": "exclude", "att": "props", "val": "firefox-release"}
    ]
    for locale in LOCALES:
        exclusions = ET.parse(filters / f"locale-{locale}.ditaval").getroot().findall("prop")
        assert {element.attrib["val"] for element in exclusions} == {
            f"locale-{other}" for other in LOCALES if other != locale
        }
        assert all(
            element.attrib["action"] == "exclude" and element.attrib["att"] == "deliveryTarget"
            for element in exclusions
        )


def test_metadata_validator_accepts_registered_values_and_rejects_unknown_values(
    tmp_path: Path,
) -> None:
    vocabulary = validate_metadata.load_vocabulary()
    valid = tmp_path / "valid.dita"
    valid.write_text(
        '<topic id="valid" audience="user" platform="web" product="bpm-0-9-1" '
        'deliveryTarget="locale-en" props="firefox-release cis-level-1" '
        'otherprops="policy(AIControls) cis(1.1.1.1) api-operation(API-SVC-001)">'
        "<title>Valid</title></topic>",
        encoding="utf-8",
    )
    assert validate_metadata.validate_xml(valid, vocabulary) == []

    invalid = tmp_path / "invalid.dita"
    invalid.write_text(
        '<topic id="invalid" audience="operator" props="firefox-nightly" '
        'otherprops="policy(NotARealPolicy) api-operation(API-UNKNOWN-999)">'
        "<title>Invalid</title></topic>",
        encoding="utf-8",
    )
    errors = validate_metadata.validate_xml(invalid, vocabulary)
    assert any("unknown audience value(s): operator" in error for error in errors)
    assert any("unknown props value(s): firefox-nightly" in error for error in errors)
    assert any("unknown policy value(s): NotARealPolicy" in error for error in errors)
    assert any("unknown api-operation value(s): API-UNKNOWN-999" in error for error in errors)


def test_current_dita_sources_use_only_registered_conditional_metadata() -> None:
    vocabulary = validate_metadata.load_vocabulary()
    files = validate_metadata.source_files(
        [*validate_metadata.DEFAULT_SOURCES, DOCUMENTATION_ROOT / "fixtures/metadata-filter"]
    )

    assert files
    assert [
        error for path in files for error in validate_metadata.validate_xml(path, vocabulary)
    ] == []
