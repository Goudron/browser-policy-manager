from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.support import make_test_client

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
API_INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"

pytestmark = pytest.mark.docs_contract

ParameterContract = tuple[str, str, bool, str, Any, Any, Any]
RequestContract = tuple[str, tuple[str, ...]]
ResponseContract = tuple[str, tuple[str, ...], tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class OperationContract:
    api_id: str
    method: str
    path: str
    operation_id: str
    tags: tuple[str, ...]
    guide_topics: tuple[str, ...]
    inventory_topic: str
    parameters: tuple[ParameterContract, ...] = ()
    request: tuple[RequestContract, ...] = ()
    responses: tuple[ResponseContract, ...] = ()
    documented_statuses: tuple[str, ...] = ()


PROGRAMMATIC_OPERATIONS: tuple[OperationContract, ...] = (
    OperationContract(
        api_id="API-SVC-001",
        method="GET",
        path="/",
        operation_id="root__get",
        tags=(),
        guide_topics=(
            "admin-concept-api-conventions",
            "admin-concept-supported-integration-patterns",
        ),
        inventory_topic="admin-task-check-health-readiness",
        responses=(("200", ("application/json",), ()),),
        documented_statuses=("200",),
    ),
    OperationContract(
        api_id="API-HEALTH-001",
        method="GET",
        path="/health",
        operation_id="health_health_get",
        tags=("health",),
        guide_topics=("admin-task-check-health-readiness", "admin-task-use-reusable-api-examples"),
        inventory_topic="admin-task-check-health-readiness",
        responses=(("200", ("application/json",), ()),),
        documented_statuses=("200",),
    ),
    OperationContract(
        api_id="API-HEALTH-002",
        method="GET",
        path="/health/ready",
        operation_id="ready_health_ready_get",
        tags=("health",),
        guide_topics=("admin-task-check-health-readiness", "admin-task-use-reusable-api-examples"),
        inventory_topic="admin-task-check-health-readiness",
        responses=(("200", ("application/json",), ()),),
        documented_statuses=("200",),
    ),
    OperationContract(
        api_id="API-PROFILE-001",
        method="GET",
        path="/api/profiles",
        operation_id="list_profiles_api_profiles_get",
        tags=("profiles",),
        guide_topics=(
            "admin-task-sync-profile-lifecycle",
            "admin-task-run-pull-compare-update-scenario",
        ),
        inventory_topic="admin-task-sync-profile-lifecycle",
        parameters=(
            ("q", "query", False, "anyOf:string|null", None, None, None),
            ("schema_version", "query", False, "anyOf:string|null", None, None, None),
            ("validation_state", "query", False, "anyOf:string|null", None, None, None),
            ("lifecycle", "query", False, "string", "active", None, None),
            ("include_deleted", "query", False, "boolean", False, None, None),
            ("limit", "query", False, "integer", 50, 1, 200),
            ("offset", "query", False, "integer", 0, 0, None),
            ("sort", "query", False, "string", "updated_at", None, None),
            ("order", "query", False, "string", "desc", None, None),
        ),
        responses=(
            ("200", ("application/json",), ("ProfileRead",)),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-002",
        method="GET",
        path="/api/profiles/stats",
        operation_id="profile_library_stats_api_profiles_stats_get",
        tags=("profiles",),
        guide_topics=("admin-task-sync-profile-lifecycle",),
        inventory_topic="admin-task-sync-profile-lifecycle",
        parameters=(
            ("q", "query", False, "anyOf:string|null", None, None, None),
            ("schema_version", "query", False, "anyOf:string|null", None, None, None),
            ("validation_state", "query", False, "anyOf:string|null", None, None, None),
            ("lifecycle", "query", False, "string", "active", None, None),
            ("include_deleted", "query", False, "boolean", False, None, None),
        ),
        responses=(
            ("200", ("application/json",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-003",
        method="GET",
        path="/api/profiles/{profile_id}",
        operation_id="get_profile_api_profiles__profile_id__get",
        tags=("profiles",),
        guide_topics=(
            "admin-task-sync-profile-lifecycle",
            "admin-task-run-pull-compare-update-scenario",
            "admin-task-run-import-review-export-scenario",
        ),
        inventory_topic="admin-task-sync-profile-lifecycle",
        parameters=(
            ("profile_id", "path", True, "integer", None, None, None),
            ("include_deleted", "query", False, "boolean", False, None, None),
        ),
        responses=(
            ("200", ("application/json",), ("ProfileRead",)),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "404", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-004",
        method="POST",
        path="/api/profiles",
        operation_id="create_profile_api_profiles_post",
        tags=("profiles",),
        guide_topics=("admin-task-sync-profile-lifecycle", "admin-task-use-reusable-api-examples"),
        inventory_topic="admin-task-sync-profile-lifecycle",
        request=(("application/json", ("ProfileCreate",)),),
        responses=(
            ("201", ("application/json",), ("ProfileRead",)),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("201", "400", "409", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-005",
        method="PATCH",
        path="/api/profiles/{profile_id}",
        operation_id="update_profile_api_profiles__profile_id__patch",
        tags=("profiles",),
        guide_topics=(
            "admin-task-sync-profile-lifecycle",
            "admin-task-run-pull-compare-update-scenario",
        ),
        inventory_topic="admin-task-sync-profile-lifecycle",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        request=(("application/json", ("ProfileUpdate",)),),
        responses=(
            ("200", ("application/json",), ("ProfileRead",)),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "400", "404", "409", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-010",
        method="POST",
        path="/api/profiles/{profile_id}/conversion-preview",
        operation_id="preview_profile_conversion_api_profiles__profile_id__conversion_preview_post",
        tags=("profiles",),
        guide_topics=("admin-task-use-reusable-api-examples",),
        inventory_topic="admin-task-use-reusable-api-examples",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        request=(("application/json", ()),),
        responses=(
            ("200", ("application/json",), ("ConversionPreviewResponse",)),
            ("404", ("application/json",), ("ConversionPreviewErrorEnvelope",)),
            ("409", ("application/json",), ("ConversionPreviewErrorEnvelope",)),
            ("422", ("application/json",), ("ConversionPreviewErrorEnvelope",)),
            ("503", ("application/json",), ("ConversionPreviewErrorEnvelope",)),
        ),
        documented_statuses=("200", "404", "409", "422", "503"),
    ),
    OperationContract(
        api_id="API-PROFILE-011",
        method="POST",
        path="/api/profiles/{profile_id}/conversion-apply",
        operation_id="apply_profile_conversion_api_profiles__profile_id__conversion_apply_post",
        tags=("profiles",),
        guide_topics=("admin-task-use-reusable-api-examples",),
        inventory_topic="admin-task-use-reusable-api-examples",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        request=(("application/json", ("ConversionLineArtifactReference",)),),
        responses=(
            ("200", ("application/json",), ("ConversionApplyResponse",)),
            ("404", ("application/json",), ("ConversionApplyErrorEnvelope",)),
            ("409", ("application/json",), ("ConversionApplyErrorEnvelope",)),
            ("422", ("application/json",), ("ConversionApplyErrorEnvelope",)),
            ("500", ("application/json",), ("ConversionApplyErrorEnvelope",)),
            ("503", ("application/json",), ("ConversionApplyErrorEnvelope",)),
        ),
        documented_statuses=("200", "404", "409", "422", "500", "503"),
    ),
    OperationContract(
        api_id="API-PROFILE-006",
        method="DELETE",
        path="/api/profiles/{profile_id}",
        operation_id="delete_profile_api_profiles__profile_id__delete",
        tags=("profiles",),
        guide_topics=("admin-task-manage-profile-retirement",),
        inventory_topic="admin-task-manage-profile-retirement",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(("204", (), ()), ("422", ("application/json",), ("HTTPValidationError",))),
        documented_statuses=("204", "404", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-007",
        method="POST",
        path="/api/profiles/{profile_id}/restore",
        operation_id="restore_profile_api_profiles__profile_id__restore_post",
        tags=("profiles",),
        guide_topics=("admin-task-manage-profile-retirement",),
        inventory_topic="admin-task-manage-profile-retirement",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(
            ("200", ("application/json",), ("ProfileRead",)),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "404", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-008",
        method="DELETE",
        path="/api/profiles/{profile_id}/hard",
        operation_id="hard_delete_profile_api_profiles__profile_id__hard_delete",
        tags=("profiles",),
        guide_topics=("admin-task-manage-profile-retirement",),
        inventory_topic="admin-task-manage-profile-retirement",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(("204", (), ()), ("422", ("application/json",), ("HTTPValidationError",))),
        documented_statuses=("204", "404", "422"),
    ),
    OperationContract(
        api_id="API-PROFILE-009",
        method="DELETE",
        path="/api/profiles/reset",
        operation_id="reset_profiles_library_api_profiles_reset_delete",
        tags=("profiles",),
        guide_topics=("admin-task-manage-profile-retirement",),
        inventory_topic="admin-task-manage-profile-retirement",
        responses=(("200", ("application/json",), ()),),
        documented_statuses=("200",),
    ),
    OperationContract(
        api_id="API-FF-001",
        method="POST",
        path="/api/profiles/import/firefox/policies.json",
        operation_id="import_firefox_policies_json_api_profiles_import_firefox_policies_json_post",
        tags=("profiles",),
        guide_topics=(
            "admin-task-import-firefox-policies-json",
            "admin-task-run-import-review-export-scenario",
        ),
        inventory_topic="admin-task-import-firefox-policies-json",
        request=(("application/json", ()), ("multipart/form-data", ())),
        responses=(("201", ("application/json",), ("ProfileRead",)),),
        documented_statuses=("201", "400", "409", "415", "422"),
    ),
    OperationContract(
        api_id="API-FF-002",
        method="GET",
        path="/api/export/profiles/{profile_id}/firefox/policies.json",
        operation_id="export_single_firefox_policies_json_api_export_profiles__profile_id__firefox_policies_json_get",
        tags=("export",),
        guide_topics=(
            "admin-task-export-firefox-policies-json",
            "admin-task-run-import-review-export-scenario",
            "admin-task-use-reusable-api-examples",
        ),
        inventory_topic="admin-task-export-firefox-policies-json",
        parameters=(
            ("profile_id", "path", True, "integer", None, None, None),
            ("include_deleted", "query", False, "boolean", False, None, None),
            ("download", "query", False, "integer", 0, 0, 1),
            ("indent", "query", False, "anyOf:integer|null", None, None, None),
            ("pretty", "query", False, "integer", 0, 0, 1),
        ),
        responses=(
            ("200", ("application/json",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "404", "422"),
    ),
    OperationContract(
        api_id="API-VAL-001",
        method="POST",
        path="/api/validate/{profile}",
        operation_id="validate_profile_api_validate__profile__post",
        tags=("validation",),
        guide_topics=(
            "admin-task-validate-firefox-policies-json",
            "admin-task-run-pull-compare-update-scenario",
            "admin-task-run-import-review-export-scenario",
            "admin-task-use-reusable-api-examples",
        ),
        inventory_topic="admin-task-validate-firefox-policies-json",
        parameters=(("profile", "path", True, "string", None, None, None),),
        request=(("application/json", ("ValidationRequest",)),),
        responses=(
            ("200", ("application/json",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
        documented_statuses=("200", "400", "404", "422", "503"),
    ),
)

WEB_OPERATIONS: tuple[OperationContract, ...] = (
    OperationContract(
        api_id="WEB-001",
        method="GET",
        path="/profiles",
        operation_id="profiles_page_profiles_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="Profile Library HTML route",
        responses=(("200", ("text/html",), ()),),
    ),
    OperationContract(
        api_id="WEB-002",
        method="GET",
        path="/profiles/compare",
        operation_id="profiles_compare_page_profiles_compare_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="Profile Comparison HTML route",
        responses=(("200", ("text/html",), ()),),
    ),
    OperationContract(
        api_id="WEB-003",
        method="GET",
        path="/profiles/new",
        operation_id="profiles_new_page_profiles_new_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="New Guided draft HTML route",
        responses=(("200", ("text/html",), ()),),
    ),
    OperationContract(
        api_id="WEB-004",
        method="GET",
        path="/profiles/{profile_id}/edit",
        operation_id="profiles_edit_page_profiles__profile_id__edit_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="Saved Guided Editor HTML route",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(
            ("200", ("text/html",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
    ),
    OperationContract(
        api_id="WEB-005",
        method="GET",
        path="/profiles/{profile_id}/settings",
        operation_id="profiles_settings_page_profiles__profile_id__settings_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="All Settings HTML route",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(
            ("200", ("text/html",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
    ),
    OperationContract(
        api_id="WEB-006",
        method="GET",
        path="/profiles/{profile_id}/json",
        operation_id="profiles_json_page_profiles__profile_id__json_get",
        tags=("web",),
        guide_topics=("user-guide",),
        inventory_topic="JSON Editor HTML route",
        parameters=(("profile_id", "path", True, "integer", None, None, None),),
        responses=(
            ("200", ("text/html",), ()),
            ("422", ("application/json",), ("HTTPValidationError",)),
        ),
    ),
)

# The assistant transport has a separate versioned API delivery contract.  It is not
# part of the public profile/API integration inventory or its Administrator Guide
# coverage matrix.
DOCUMENTATION_ASSISTANT_ROUTE_KEYS = frozenset(
    {
        ("GET", "/api/documentation-assistant/status"),
        ("GET", "/api/documentation-assistant/web-mode"),
        ("POST", "/api/documentation-assistant/web-mode"),
        ("POST", "/api/documentation-assistant/chat"),
        ("GET", "/api/documentation-assistant/chat/{request_id}/stream"),
        ("POST", "/api/documentation-assistant/chat/{request_id}/cancel"),
        ("DELETE", "/api/documentation-assistant/conversation"),
        ("GET", "/api/documentation-assistant/chat/{request_id}/sources/{source_id}"),
    }
)

EXPECTED_MODEL_FIELDS = {
    "ProfileCreate": {
        "required": ("name",),
        "properties": {
            "name": ("string", None, None, 255),
            "description": ("anyOf:string|null", None, None, None),
            "schema_version": ("string", "esr-153.0", None, 50),
            "flags": ("object", None, None, None),
            "compliance": ("anyOf:object|null", None, None, None),
        },
    },
    "ProfileUpdate": {
        "required": (),
        "properties": {
            "description": ("anyOf:string|null", None, None, None),
            "schema_version": ("anyOf:string|null", None, None, None),
            "flags": ("anyOf:object|null", None, None, None),
            "compliance": ("anyOf:object|null", None, None, None),
            "expected_revision": ("anyOf:integer|null", None, None, None),
        },
    },
    "ProfileRead": {
        "required": ("name", "id", "revision", "created_at", "updated_at", "is_deleted"),
        "properties": {
            "name": ("string", None, None, 255),
            "description": ("anyOf:string|null", None, None, None),
            "schema_version": ("string", "esr-153.0", None, 50),
            "flags": ("object", None, None, None),
            "compliance": ("anyOf:object|null", None, None, None),
            "id": ("integer", None, None, None),
            "revision": ("integer", None, None, None),
            "created_at": ("string", None, None, None),
            "updated_at": ("string", None, None, None),
            "deleted_at": ("anyOf:string|null", None, None, None),
            "is_deleted": ("boolean", None, None, None),
            "validation_state": ("string", "not_validated", None, None),
            "recommendation": ("anyOf:ref:ProfileRecommendation|null", None, None, None),
        },
    },
    "ValidationRequest": {
        "required": ("document",),
        "properties": {
            "document": ("any", None, None, None),
        },
    },
}


def _openapi_schema() -> dict[str, Any]:
    with make_test_client() as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    return response.json()


def _schema_type(schema: Mapping[str, Any]) -> str:
    if "$ref" in schema:
        return f"ref:{schema['$ref'].rsplit('/', 1)[-1]}"
    if "anyOf" in schema:
        return "anyOf:" + "|".join(_schema_type(option) for option in schema["anyOf"])
    if schema.get("type") == "array":
        return "array:" + _schema_type(schema.get("items", {}))
    return schema.get("type", "any")


def _schema_refs(schema: Any) -> tuple[str, ...]:
    refs: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str):
                refs.add(ref.rsplit("/", 1)[-1])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(schema)
    return tuple(sorted(refs))


def _actual_operation_contract(
    schema: Mapping[str, Any], operation: OperationContract
) -> dict[str, Any]:
    openapi_operation = schema["paths"][operation.path][operation.method.lower()]
    request_content = openapi_operation.get("requestBody", {}).get("content", {})
    responses = openapi_operation.get("responses", {})
    return {
        "operation_id": openapi_operation.get("operationId"),
        "tags": tuple(openapi_operation.get("tags") or ()),
        "parameters": tuple(
            (
                parameter["name"],
                parameter["in"],
                parameter.get("required", False),
                _schema_type(parameter.get("schema", {})),
                parameter.get("schema", {}).get("default"),
                parameter.get("schema", {}).get("minimum"),
                parameter.get("schema", {}).get("maximum"),
            )
            for parameter in openapi_operation.get("parameters", [])
        ),
        "request": tuple(
            (content_type, _schema_refs(content.get("schema", {})))
            for content_type, content in sorted(request_content.items())
        ),
        "responses": tuple(
            (
                status_code,
                tuple(sorted(response.get("content", {}).keys())),
                _schema_refs({"content": response.get("content", {})}),
            )
            for status_code, response in sorted(responses.items())
        ),
    }


def _expected_operation_contract(operation: OperationContract) -> dict[str, Any]:
    return {
        "operation_id": operation.operation_id,
        "tags": operation.tags,
        "parameters": operation.parameters,
        "request": operation.request,
        "responses": operation.responses,
    }


def _topic_text(topic_id: str) -> str:
    path = DITA_ROOT / "en/admin" / f"{topic_id}.dita"
    assert path.is_file(), f"Missing Administrator Guide API integration topic {topic_id}"
    return " ".join(path.read_text(encoding="utf-8").split())


def test_openapi_operation_inventory_matches_generated_schema_with_topic_ids() -> None:
    schema = _openapi_schema()
    expected_operations = PROGRAMMATIC_OPERATIONS + WEB_OPERATIONS
    actual_route_keys = {
        (method.upper(), path) for path, methods in schema["paths"].items() for method in methods
    }
    expected_route_keys = {(operation.method, operation.path) for operation in expected_operations}

    assert actual_route_keys == expected_route_keys | DOCUMENTATION_ASSISTANT_ROUTE_KEYS, (
        "OpenAPI route set drifted. Update API documentation inventory and DITA coverage. "
        f"missing={sorted(expected_route_keys - actual_route_keys)} "
        f"unexpected={sorted(actual_route_keys - expected_route_keys)}"
    )

    for operation in expected_operations:
        actual = _actual_operation_contract(schema, operation)
        expected = _expected_operation_contract(operation)
        assert actual == expected, (
            f"{operation.api_id} ({operation.method} {operation.path}) drifted for "
            f"DITA topics {operation.guide_topics} and inventory topic {operation.inventory_topic}: "
            f"actual={actual!r} expected={expected!r}"
        )


def test_api_inventory_rows_match_current_operation_topics_and_status_families() -> None:
    inventory = " ".join(API_INVENTORY_PATH.read_text(encoding="utf-8").split())
    guide_text_cache = {
        topic_id: _topic_text(topic_id)
        for operation in PROGRAMMATIC_OPERATIONS
        for topic_id in operation.guide_topics
    }

    for operation in PROGRAMMATIC_OPERATIONS:
        inventory_needles = (
            operation.api_id,
            f"`{operation.method}`",
            f"`{operation.path}`",
            f"`{operation.inventory_topic}`",
        )
        for needle in inventory_needles:
            assert needle in inventory, (
                f"{operation.api_id} inventory drift: missing {needle!r} for "
                f"{operation.method} {operation.path} / topic {operation.inventory_topic}"
            )

        for status_code in operation.documented_statuses:
            assert status_code in inventory, (
                f"{operation.api_id} inventory status drift: missing status {status_code} "
                f"for topic {operation.inventory_topic}"
            )
            assert any(
                status_code in guide_text_cache[topic_id] for topic_id in operation.guide_topics
            ), (
                f"{operation.api_id} DITA status drift: status {status_code} is not documented "
                f"in guide topics {operation.guide_topics}"
            )

    for operation in WEB_OPERATIONS:
        for needle in (operation.api_id, f"`{operation.method}`", f"`{operation.path}`"):
            assert needle in inventory, (
                f"{operation.api_id} web-route classification drift: missing {needle!r}"
            )
        assert "User Guide, not by the Administrator/DevOps API integration sections" in inventory


def test_openapi_models_match_documented_api_boundary_fields() -> None:
    schema = _openapi_schema()
    schemas = schema["components"]["schemas"]

    for model_name, expected_model in EXPECTED_MODEL_FIELDS.items():
        actual_model = schemas[model_name]
        actual_required = tuple(actual_model.get("required", ()))
        assert actual_required == expected_model["required"], (
            f"{model_name} required-field drift affects API model DITA topics: "
            f"actual={actual_required!r} expected={expected_model['required']!r}"
        )

        actual_properties = {
            name: (
                _schema_type(property_schema),
                property_schema.get("default"),
                property_schema.get("minimum"),
                property_schema.get("maxLength"),
            )
            for name, property_schema in actual_model.get("properties", {}).items()
        }
        assert actual_properties == expected_model["properties"], (
            f"{model_name} property drift affects API model DITA topics: "
            f"actual={actual_properties!r} expected={expected_model['properties']!r}"
        )


def test_openapi_examples_match_documented_copyable_examples_boundary() -> None:
    schema = _openapi_schema()
    import_schema = schema["paths"]["/api/profiles/import/firefox/policies.json"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    validation_schema = schema["components"]["schemas"]["ValidationRequest"]["properties"][
        "document"
    ]

    assert import_schema["example"] == {
        "name": "Workstation baseline",
        "description": "Imported from Firefox policies.json",
        "schema_version": "esr-153.0",
        "document": {
            "policies": {
                "DisableTelemetry": True,
                "Preferences": {
                    "browser.tabs.warnOnClose": {
                        "Value": True,
                        "Status": "locked",
                    }
                },
            }
        },
    }, (
        "API-FF-001 OpenAPI example drifted; update admin-task-import-firefox-policies-json "
        "and reusable copyable examples if the canonical import example changes."
    )
    assert validation_schema["examples"] == [
        {
            "policies": {
                "DisableAppUpdate": True,
                "HttpAllowlist": ["http://example.org"],
            }
        }
    ], (
        "API-VAL-001 OpenAPI example drifted; update admin-task-validate-firefox-policies-json "
        "and reusable copyable examples if the validation example changes."
    )
