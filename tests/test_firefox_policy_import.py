from __future__ import annotations

import pytest

from app.services.firefox_policy_import import (
    FirefoxPoliciesDocumentValidationError,
    FirefoxPoliciesImportError,
    FirefoxPoliciesImportIssue,
    _type_name,
    parse_firefox_policies_document,
    validate_firefox_policies_document,
)


def test_type_name_reports_scalar_types_through_error_messages():
    expected = {
        None: "null",
        True: "boolean",
        "raw": "string",
        3: "number",
    }

    for document, type_name in expected.items():
        with pytest.raises(FirefoxPoliciesImportError) as excinfo:
            parse_firefox_policies_document(document)

        assert excinfo.value.issues[0].message.endswith(f"got {type_name}")


def test_type_name_reports_object_and_fallback_types():
    class Custom:
        pass

    assert _type_name({}) == "object"
    assert _type_name(Custom()) == "Custom"


def test_parse_firefox_policies_document_normalizes_valid_document():
    document = {
        "policies": {
            "DisableTelemetry": True,
            "BlockAboutConfig": True,
        }
    }

    flags = parse_firefox_policies_document(document)

    assert flags == {
        "DisableTelemetry": True,
        "BlockAboutConfig": True,
    }
    assert flags is not document["policies"]


@pytest.mark.parametrize(
    ("document", "expected_issue"),
    [
        (
            {},
            FirefoxPoliciesImportIssue(
                path=["policies"],
                message="Missing required Firefox policies object",
            ),
        ),
        (
            {"policies": []},
            FirefoxPoliciesImportIssue(
                path=["policies"],
                message="Expected policies to be an object, got array",
            ),
        ),
        (
            [],
            FirefoxPoliciesImportIssue(
                path=[],
                message="Expected Firefox policies.json root object, got array",
            ),
        ),
    ],
)
def test_parse_firefox_policies_document_rejects_invalid_shapes(
    document,
    expected_issue,
):
    with pytest.raises(FirefoxPoliciesImportError) as excinfo:
        parse_firefox_policies_document(document)

    assert expected_issue in excinfo.value.issues


def test_parse_firefox_policies_document_rejects_internal_bpm_flags_shape():
    with pytest.raises(FirefoxPoliciesImportError) as excinfo:
        parse_firefox_policies_document({"flags": {"DisableTelemetry": True}})

    assert FirefoxPoliciesImportIssue(
        path=["policies"],
        message="Missing required Firefox policies object",
    ) in excinfo.value.issues
    assert FirefoxPoliciesImportIssue(
        path=["flags"],
        message=(
            "Unsupported top-level key 'flags'; import Firefox policies.json "
            "with a top-level policies object instead"
        ),
    ) in excinfo.value.issues


def test_parse_firefox_policies_document_rejects_internal_bpm_profile_shape():
    with pytest.raises(FirefoxPoliciesImportError) as excinfo:
        parse_firefox_policies_document(
            {
                "name": "Internal BPM profile",
                "schema_version": "release-150",
                "flags": {"DisableTelemetry": True},
            }
        )

    assert FirefoxPoliciesImportIssue(
        path=["policies"],
        message="Missing required Firefox policies object",
    ) in excinfo.value.issues
    assert FirefoxPoliciesImportIssue(
        path=["flags"],
        message=(
            "Unsupported top-level key 'flags'; import Firefox policies.json "
            "with a top-level policies object instead"
        ),
    ) in excinfo.value.issues
    assert FirefoxPoliciesImportIssue(
        path=["name"],
        message="Unsupported top-level key 'name'",
    ) in excinfo.value.issues
    assert FirefoxPoliciesImportIssue(
        path=["schema_version"],
        message="Unsupported top-level key 'schema_version'",
    ) in excinfo.value.issues


def test_parse_firefox_policies_document_rejects_extra_top_level_keys():
    with pytest.raises(FirefoxPoliciesImportError) as excinfo:
        parse_firefox_policies_document(
            {
                "metadata": {"owner": "IT"},
                "policies": {"DisableTelemetry": True},
            }
        )

    assert excinfo.value.issues == [
        FirefoxPoliciesImportIssue(
            path=["metadata"],
            message="Unsupported top-level key 'metadata'",
        )
    ]


def test_validate_firefox_policies_document_returns_flags_for_valid_document():
    flags = validate_firefox_policies_document(
        {"policies": {"DisableTelemetry": True}},
        "release-150",
    )

    assert flags == {"DisableTelemetry": True}


def test_validate_firefox_policies_document_prefixes_schema_issue_paths():
    with pytest.raises(FirefoxPoliciesDocumentValidationError) as excinfo:
        validate_firefox_policies_document(
            {
                "policies": {
                    "Proxy": {
                        "Mode": "bogus",
                    }
                }
            },
            "release-150",
        )

    assert excinfo.value.issues
    first_issue = excinfo.value.issues[0]
    assert first_issue.policy == "Proxy"
    assert first_issue.path == ["policies", "Proxy", "Mode"]


def test_validate_firefox_policies_document_keeps_structural_errors_separate():
    with pytest.raises(FirefoxPoliciesImportError) as excinfo:
        validate_firefox_policies_document(
            {"flags": {"DisableTelemetry": True}},
            "release-150",
        )

    assert FirefoxPoliciesImportIssue(
        path=["flags"],
        message=(
            "Unsupported top-level key 'flags'; import Firefox policies.json "
            "with a top-level policies object instead"
        ),
    ) in excinfo.value.issues
