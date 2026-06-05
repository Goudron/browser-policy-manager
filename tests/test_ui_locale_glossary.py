import json
from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = REPO_ROOT / "docs" / "ui_locale_glossary_global_2026-05-29.md"
MOZILLA_WORKFLOW_PATH = (
    REPO_ROOT / "docs" / "mozilla_terminology_verification_workflow_2026-05-29.md"
)
DE_MOZILLA_AUDIT_PATH = doc_path_from_index(
    "de_mozilla_terminology_audit_2026-05-29.md", status="audit"
)
ZH_CN_MOZILLA_AUDIT_PATH = doc_path_from_index(
    "zh_cn_mozilla_terminology_audit_2026-05-29.md", status="audit"
)
FR_MOZILLA_AUDIT_PATH = doc_path_from_index(
    "fr_mozilla_terminology_audit_2026-05-29.md", status="audit"
)
ES_ES_MOZILLA_AUDIT_PATH = doc_path_from_index(
    "es_es_mozilla_terminology_audit_2026-05-30.md", status="audit"
)
PLACEHOLDER_RULES_PATH = (
    REPO_ROOT / "docs" / "locale_placeholder_identifier_rules_2026-05-29.md"
)
LOCALE_UPDATE_RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "locale_update_runbook_2026-06-01.md"
)
LOCALE_OWNERSHIP_PATH = REPO_ROOT / "docs" / "locale_ownership_2026-06-01.md"
FIREFOX_SCHEMA_UPDATE_RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "firefox-schema-update-runbook.md"
)
HISTORICAL_GLOSSARY_PATH = doc_path_from_index(
    "ui_locale_glossary_en_ru_2026-05-15.md", status="archive"
)
CONTRACT_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "locale_contracts" / "ui_locale_glossary_contract.json"
)
CONTRACT = json.loads(CONTRACT_FIXTURE_PATH.read_text(encoding="utf-8"))


def _contract(section: str, key: str) -> list[str]:
    return CONTRACT[section][key]


def test_ui_locale_glossary_contract_fixture_covers_document_checks():
    expected_sections = {
        "global_ui_locale_glossary_records_six_locale_terms",
        "global_ui_locale_glossary_consolidates_mozilla_qa_findings",
        "mozilla_terminology_workflow_records_repeatable_process",
        "de_mozilla_terminology_audit_records_evidence_and_decisions",
        "zh_cn_mozilla_terminology_audit_records_evidence_and_decisions",
        "fr_mozilla_terminology_audit_records_evidence_and_decisions",
        "es_es_mozilla_terminology_audit_records_evidence_and_decisions",
        "placeholder_identifier_rules_record_locale_review_contract",
        "locale_update_runbook_records_repeatable_release_process",
        "firefox_schema_update_runbook_includes_locale_update_gate",
        "locale_ownership_records_single_maintainer_model",
    }

    assert expected_sections <= set(CONTRACT)
    assert all(CONTRACT[section] for section in expected_sections)


def test_global_ui_locale_glossary_records_six_locale_terms():
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-103`" in glossary
    assert "QA consolidation: `GLOC-305`" in glossary
    assert "Release-readiness glossary update: `GLOC-702`" in glossary
    assert "Document status: primary maintainer glossary" in glossary
    assert "Source locale: `en`" in glossary
    assert "Target locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in glossary
    assert "German, Simplified" in glossary
    assert "Chinese, French, and Spanish record the" in glossary
    assert (
        "| Term ID | English source term | ru | de | zh-CN | fr | es-ES | Notes |"
        in glossary
    )

    required_terms = _contract(
        "global_ui_locale_glossary_records_six_locale_terms", "required_terms"
    )
    for term in required_terms:
        assert term in glossary

    assert "Do not replace `TBD` with unreviewed machine" in glossary
    assert "Firefox/Mozilla terms must be checked against Pontoon and SUMO" in glossary
    assert "docs/mozilla_terminology_verification_workflow_2026-05-29.md" in glossary
    assert "docs/locale_placeholder_identifier_rules_2026-05-29.md" in glossary


def test_global_ui_locale_glossary_consolidates_mozilla_qa_findings():
    glossary = GLOSSARY_PATH.read_text(encoding="utf-8")

    required_markers = _contract(
        "global_ui_locale_glossary_consolidates_mozilla_qa_findings",
        "required_markers",
    )
    for marker in required_markers:
        assert marker in glossary

    mozilla_section = glossary.split("## Firefox And Mozilla Terms", 1)[1].split(
        "## Policy And Schema Terms", 1
    )[0]
    term_rows = [
        row
        for row in mozilla_section.splitlines()
        if row.startswith("| mozilla.")
    ]

    assert term_rows
    assert all("TBD" not in row for row in term_rows)

    required_rows = _contract(
        "global_ui_locale_glossary_consolidates_mozilla_qa_findings",
        "required_rows",
    )
    for row in required_rows:
        assert row in glossary


def test_historical_en_ru_glossary_points_to_global_glossary():
    glossary = HISTORICAL_GLOSSARY_PATH.read_text(encoding="utf-8")

    assert "Scope: historical EN/RU product UI terminology only." in glossary
    assert "docs/ui_locale_glossary_global_2026-05-29.md" in glossary
    assert "historical EN/RU reference" in glossary
    assert "single current maintainer reference" in glossary
    assert "Do not add new terminology decisions here." in glossary


def test_mozilla_terminology_workflow_records_repeatable_process():
    workflow = MOZILLA_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-104`" in workflow
    assert "Applies to locales: `de`, `zh-CN`, `fr`, `es-ES`, and future locale maintenance for `ru`" in workflow
    assert "Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`" in workflow
    assert "Mozilla Pontoon Firefox project and target-locale team pages" in workflow
    assert "SUMO localized Firefox articles" in workflow
    assert "Target locale Firefox Enterprise project" in workflow
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in workflow

    required_terms = _contract(
        "mozilla_terminology_workflow_records_repeatable_process", "required_terms"
    )
    for term in required_terms:
        assert term in workflow

    required_sources = _contract(
        "mozilla_terminology_workflow_records_repeatable_process", "required_sources"
    )
    for source in required_sources:
        assert source in workflow


def test_de_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = DE_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-301`" in audit
    assert "Catalog: `app/i18n/de.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = _contract(
        "de_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_terms",
    )
    for term in required_terms:
        assert term in audit

    required_sources = _contract(
        "de_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_sources",
    )
    for source in required_sources:
        assert source in audit


def test_zh_cn_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = ZH_CN_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-302`" in audit
    assert "Catalog: `app/i18n/zh-CN.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = _contract(
        "zh_cn_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_terms",
    )
    for term in required_terms:
        assert term in audit

    required_sources = _contract(
        "zh_cn_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_sources",
    )
    for source in required_sources:
        assert source in audit


def test_fr_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = FR_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-303`" in audit
    assert "Catalog: `app/i18n/fr.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = _contract(
        "fr_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_terms",
    )
    for term in required_terms:
        assert term in audit

    required_sources = _contract(
        "fr_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_sources",
    )
    for source in required_sources:
        assert source in audit


def test_es_es_mozilla_terminology_audit_records_evidence_and_decisions():
    audit = ES_ES_MOZILLA_AUDIT_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-304`" in audit
    assert "Catalog: `app/i18n/es-ES.json`" in audit
    assert "terminology-focused" in audit
    assert "| Term ID | English source | Candidate term | Pontoon evidence | SUMO evidence | Decision | Notes |" in audit

    required_terms = _contract(
        "es_es_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_terms",
    )
    for term in required_terms:
        assert term in audit

    required_sources = _contract(
        "es_es_mozilla_terminology_audit_records_evidence_and_decisions",
        "required_sources",
    )
    for source in required_sources:
        assert source in audit


def test_placeholder_identifier_rules_record_locale_review_contract():
    rules = PLACEHOLDER_RULES_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-105`" in rules
    assert "Applies to locales: `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in rules
    assert "Make locale review deterministic" in rules
    assert "Preserve the complete token exactly, including braces and case" in rules
    assert "Every target locale key must contain the same placeholder set" in rules
    assert "The complete placeholder inventory is in `placeholder_map`" in rules
    assert "The complete technical-token inventory is in `technical_token_map`" in rules
    assert "docs/locale_visible_english_allowlists_2026-05-30.md" in rules
    assert "English prose is not accepted just because technical terms are allowed" in rules

    required_tokens = _contract(
        "placeholder_identifier_rules_record_locale_review_contract",
        "required_tokens",
    )
    for token in required_tokens:
        assert token in rules


def test_locale_update_runbook_records_repeatable_release_process():
    runbook = LOCALE_UPDATE_RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-703`" in runbook
    assert "Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in runbook
    assert "Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`" in runbook
    assert "Mozilla terminology workflow: `docs/mozilla_terminology_verification_workflow_2026-05-29.md`" in runbook
    assert "Placeholder and identifier rules: `docs/locale_placeholder_identifier_rules_2026-05-29.md`" in runbook
    assert "Visible English allowlists: `docs/locale_visible_english_allowlists_2026-05-30.md`" in runbook
    assert "Locale ownership: `docs/locale_ownership_2026-06-01.md`" in runbook

    required_catalogs = _contract(
        "locale_update_runbook_records_repeatable_release_process",
        "required_catalogs",
    )
    for catalog in required_catalogs:
        assert catalog in runbook

    required_commands = _contract(
        "locale_update_runbook_records_repeatable_release_process",
        "required_commands",
    )
    for command in required_commands:
        assert command in runbook

    required_review_points = _contract(
        "locale_update_runbook_records_repeatable_release_process",
        "required_review_points",
    )
    for point in required_review_points:
        assert point in runbook


def test_firefox_schema_update_runbook_includes_locale_update_gate():
    runbook = FIREFOX_SCHEMA_UPDATE_RUNBOOK_PATH.read_text(encoding="utf-8")

    required_catalogs = _contract(
        "firefox_schema_update_runbook_includes_locale_update_gate",
        "required_catalogs",
    )
    for catalog in required_catalogs:
        assert catalog in runbook

    required_markers = _contract(
        "firefox_schema_update_runbook_includes_locale_update_gate",
        "required_markers",
    )
    for marker in required_markers:
        assert marker in runbook


def test_locale_ownership_records_single_maintainer_model():
    ownership = LOCALE_OWNERSHIP_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-705`" in ownership
    assert "Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`" in ownership
    assert "BPM is currently maintained by a single project maintainer, Valery Ledovskoy" in ownership
    assert "There is no separate translator team, localization vendor, or open community translation process" in ownership
    assert "External or community translation contributions are not a separate maintained workflow yet" in ownership
    assert "Locale drift is handled during ordinary feature work." in ownership
    assert "Revisit this ownership document if BPM adds regular external contributors" in ownership

    required_rows = _contract(
        "locale_ownership_records_single_maintainer_model", "required_rows"
    )
    for row in required_rows:
        assert row in ownership
