from __future__ import annotations

import json
from pathlib import Path

import yaml

from tests.docs_index import doc_path_from_index

MATRIX_PATH = "architecture/product-documentation-provenance-matrix-0.9.0.json"
REVIEW_PATH = "architecture/product-documentation-provenance-review-0.9.0.md"
GUIDES = {
    "user-guide",
    "firefox-policy-guide",
    "cis-settings-guide",
    "api-integration-guide",
    "administrator-guide",
}
REQUIRED_SOURCE_FIELDS = {
    "id",
    "classification",
    "license_id",
    "authoritative_sources",
    "guide_families",
    "publication_policy",
    "may_publish_without_rights_approval",
    "allowed_reuse",
    "required_attribution",
    "forbidden_reuse",
    "update_owner",
    "update_trigger",
}


def _matrix() -> dict[str, object]:
    path = doc_path_from_index(MATRIX_PATH, status="active")
    return json.loads(path.read_text(encoding="utf-8"))


def _review() -> str:
    path = doc_path_from_index(REVIEW_PATH, status="active")
    return " ".join(path.read_text(encoding="utf-8").split())


def _sources_by_id() -> dict[str, dict[str, object]]:
    sources = _matrix()["source_families"]
    assert isinstance(sources, list)
    return {source["id"]: source for source in sources}


def test_provenance_matrix_is_approved_complete_and_owned():
    matrix = _matrix()

    assert matrix["schema_version"] == 1
    assert matrix["bpm_version"] == "0.9.0"
    assert matrix["decision_status"] == "approved"
    assert matrix["default_rule"] == "block-unregistered-or-unclear-source"
    assert set(matrix["guide_owners"]) == GUIDES

    sources = matrix["source_families"]
    source_ids = [source["id"] for source in sources]
    assert len(source_ids) == len(set(source_ids))
    assert all(REQUIRED_SOURCE_FIELDS <= set(source) for source in sources)
    assert all(source["update_owner"] and source["update_trigger"] for source in sources)
    assert all(set(source["guide_families"]) <= GUIDES for source in sources)
    assert set(matrix["publication_policies"]) == {
        "allow",
        "allow-with-notice",
        "link-only",
        "approval-required",
        "inherit",
    }


def test_provenance_matrix_covers_every_required_source_family_and_guide():
    sources = _sources_by_id()

    assert set(sources) >= {
        "bpm-product-source",
        "bpm-ui-screenshots",
        "bpm-openapi-contract",
        "mozilla-policy-schema-facts",
        "mozilla-policy-documentation-prose",
        "mozilla-official-web-docs-unclassified",
        "mdn-web-docs",
        "mozilla-trademarks",
        "cis-benchmark-pdf",
        "cis-trademarks-and-certification-marks",
        "bpm-cis-mapping-implementation",
        "third-party-product-documentation",
        "synthetic-documentation-examples",
        "localized-documentation-content",
        "generated-documentation-output",
    }
    for guide in GUIDES:
        assert any(guide in source["guide_families"] for source in sources.values())

    assert sources["bpm-product-source"]["publication_policy"] == "allow"
    assert sources["bpm-openapi-contract"]["guide_families"] == [
        "api-integration-guide",
        "administrator-guide",
    ]
    assert sources["third-party-product-documentation"]["publication_policy"] == "link-only"


def test_mozilla_reuse_keeps_mpl_provenance_and_separate_trademark_rules():
    sources = _sources_by_id()
    schema_source = sources["mozilla-policy-schema-facts"]
    prose_source = sources["mozilla-policy-documentation-prose"]
    trademark_source = sources["mozilla-trademarks"]

    assert schema_source["license_id"] == "MPL-2.0"
    assert schema_source["publication_policy"] == "allow-with-notice"
    assert (
        "https://github.com/mozilla/policy-templates/releases/tag/v7.12"
        in schema_source["authoritative_sources"]
    )
    assert (
        "https://github.com/mozilla/policy-templates/releases/tag/v8.0"
        in schema_source["authoritative_sources"]
    )
    assert prose_source["publication_policy"] == "allow-with-notice"
    assert any("Unmarked copy/paste" in rule for rule in prose_source["forbidden_reuse"])
    assert trademark_source["license_id"] == "LicenseRef-Mozilla-Trademark-Policy"
    assert any("not affiliated" in notice for notice in trademark_source["required_attribution"])
    assert any("logos" in rule for rule in trademark_source["forbidden_reuse"])

    for schema_name, source in (
        (
            "firefox-release-153.json",
            "mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490",
        ),
        (
            "firefox-esr-153.0.json",
            "mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490",
        ),
        ("firefox-esr-140.13.json", "mozilla-policy-templates-v7.12"),
    ):
        schema = json.loads(
            (Path("app/schemas/policies") / schema_name).read_text(encoding="utf-8")
        )
        assert schema["x-bpm-source"] == source


def test_mdn_and_unclassified_web_documentation_are_link_only():
    sources = _sources_by_id()

    mdn = sources["mdn-web-docs"]
    assert mdn["license_id"] == "CC-BY-SA-2.5+"
    assert mdn["publication_policy"] == "link-only"
    assert any("Copy or adapt MDN" in rule for rule in mdn["forbidden_reuse"])

    unclassified = sources["mozilla-official-web-docs-unclassified"]
    assert unclassified["license_id"] == "NOASSERTION"
    assert unclassified["publication_policy"] == "link-only"
    assert unclassified["may_publish_without_rights_approval"] is True


def test_cis_source_expression_is_blocked_without_rights_approval():
    sources = _sources_by_id()
    cis_pdf = sources["cis-benchmark-pdf"]
    cis_marks = sources["cis-trademarks-and-certification-marks"]
    cis_mapping = sources["bpm-cis-mapping-implementation"]

    assert cis_pdf["license_id"] == "CC-BY-NC-SA-4.0"
    assert cis_pdf["publication_policy"] == "approval-required"
    assert cis_pdf["may_publish_without_rights_approval"] is False
    assert any("rights_approval_id" in notice for notice in cis_pdf["required_attribution"])
    assert any("Commit, package, index, or publish" in rule for rule in cis_pdf["forbidden_reuse"])
    assert any("certification" in rule for rule in cis_pdf["forbidden_reuse"])

    assert cis_marks["license_id"] == "LicenseRef-CIS-Trademark-IP-Policy"
    assert cis_marks["publication_policy"] == "allow-with-notice"
    assert any("independent publication" in notice for notice in cis_marks["required_attribution"])
    assert any("certified badges" in rule for rule in cis_marks["forbidden_reuse"])

    assert cis_mapping["license_id"] == "MPL-2.0"
    assert cis_mapping["publication_policy"] == "allow-with-notice"
    assert any("BPM-authored mapping" in rule for rule in cis_mapping["allowed_reuse"])
    assert any("source title/rationale" in rule for rule in cis_mapping["forbidden_reuse"])

    cis_sources = yaml.safe_load(
        Path("app/compliance/firefox/cis/sources.yaml").read_text(encoding="utf-8")
    )
    benchmark = cis_sources["benchmarks"][0]
    assert benchmark["source_license"] == "CC-BY-NC-SA-4.0"
    assert benchmark["source_terms_url"] == (
        "https://www.cisecurity.org/terms-of-use-for-non-member-cis-products"
    )
    assert "/app/compliance/firefox/cis/source_materials/*.pdf" in Path(".gitignore").read_text(
        encoding="utf-8"
    )


def test_localization_and_generated_output_inherit_provenance_without_ai():
    matrix = _matrix()
    sources = _sources_by_id()
    localization = matrix["localization_contract"]

    assert localization["source_locale"] == "en"
    assert tuple(localization["published_locales"]) == ("en", "ru", "de", "zh-CN", "fr", "es-ES")
    assert localization["mode"] == "human-reviewed-ai-assisted-allowed"
    assert localization["inherits_source_provenance"] is True
    assert localization["license_may_not_be_relicensed_by_translation"] is True

    localized = sources["localized-documentation-content"]
    generated = sources["generated-documentation-output"]
    assert localized["publication_policy"] == "inherit"
    assert generated["publication_policy"] == "inherit"
    assert any(
        "Unreviewed AI or machine-generated translation" in rule
        for rule in localized["forbidden_reuse"]
    )
    assert any("removing source restrictions" in rule for rule in generated["forbidden_reuse"])


def test_provenance_review_defines_topic_metadata_notices_and_release_blockers():
    matrix = _matrix()
    review = _review()

    assert set(matrix["required_topic_provenance_fields"]) >= {
        "source_family_id",
        "source_locator",
        "source_version_or_revision",
        "source_retrieved_on",
        "license_id",
        "reuse_mode",
        "rights_approval_id_when_required",
        "localized_from_topic_id_when_not_en",
    }
    for phrase in (
        "an unregistered source or unclear license is blocked",
        "## Attribution And Artifact Notices",
        "## Source Intake And Update Workflow",
        "## Release-Blocking Conditions",
        "The official ignored PDF is a local review input, not a DITA, search, Git, or package input.",
        "does not prove compliance",
        "AI-assisted drafting or localization cannot become publishable",
        "unreviewed machine-generated documentation or translation enters this 0.9.0 scope",
    ):
        assert phrase in review
