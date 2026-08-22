from app.main import create_app

PROFILE_API_OPERATIONS = {
    "/api/profiles": {"get": "200", "post": "201"},
    "/api/profiles/prepare/new": {"post": "201"},
    "/api/profiles/prepare/duplicate": {"post": "201"},
    "/api/profiles/prepare/duplicate/preview": {"post": "200"},
    "/api/profiles/extensions/amo-search": {"get": "200"},
    "/api/profiles/stats": {"get": "200"},
    "/api/profiles/reset": {"delete": "200"},
    "/api/profiles/{profile_id}": {"get": "200", "patch": "200", "delete": "204"},
    "/api/profiles/{profile_id}/conversion-preview": {"post": "200"},
    "/api/profiles/{profile_id}/conversion-apply": {"post": "200"},
    "/api/profiles/{profile_id}/hard": {"delete": "204"},
    "/api/profiles/{profile_id}/restore": {"post": "200"},
    "/api/profiles/import/firefox/policies.json": {"post": "201"},
    "/api/export/profiles/{profile_id}/firefox/policies.json": {"get": "200"},
}


def test_openapi_uses_profiles_surface_for_export_and_crud():
    paths = create_app().openapi()["paths"]

    assert "/api/profiles" in paths
    assert "/api/profiles/{profile_id}" in paths
    assert "/api/profiles/prepare/new" in paths
    assert "/api/profiles/prepare/duplicate" in paths
    assert "/api/profiles/extensions/amo-search" in paths
    assert "/api/profiles/{profile_id}/restore" in paths
    assert "/api/profiles/import/firefox/policies.json" in paths

    assert "/api/export/profiles/{profile_id}/firefox/policies.json" in paths

    assert "/api/export/profiles" not in paths
    assert "/api/export/profiles/{profile_id}" not in paths
    assert "/api/export/profiles/{profile_id}.json" not in paths
    assert "/api/export/profiles/{profile_id}.yaml" not in paths
    assert "/api/export/policies" not in paths
    assert "/api/export/{policy_id}/policies.json" not in paths
    assert "/api/export/{policy_id}/policies.yaml" not in paths

    assert paths["/api/profiles"]["get"]["summary"] == "List profiles"
    assert (
        paths["/api/profiles/import/firefox/policies.json"]["post"]["summary"]
        == "Import Firefox policies.json"
    )
    assert (
        paths["/api/export/profiles/{profile_id}/firefox/policies.json"]["get"]["summary"]
        == "Export Firefox policies.json"
    )


def test_openapi_amo_search_is_a_bounded_read_only_same_origin_surface():
    operation = create_app().openapi()["paths"]["/api/profiles/extensions/amo-search"]["get"]

    assert operation["summary"] == "Search AMO extensions through BPM"
    assert operation["parameters"] == [
        {
            "name": "q",
            "in": "query",
            "required": True,
            "description": "Explicit extension-name lookup; 1--100 NFC characters.",
            "schema": {"type": "string", "minLength": 1, "maxLength": 100},
        },
        {
            "name": "locale",
            "in": "query",
            "required": True,
            "description": "One supported BPM UI locale.",
            "schema": {
                "type": "string",
                "enum": ["en", "ru", "de", "es-ES", "fr", "zh-CN"],
            },
        },
    ]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AmoSearchApiResponse"
    }
    assert operation["responses"]["403"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AmoSearchApiResponse"
    }


def test_openapi_profile_routes_keep_public_methods_and_success_statuses():
    paths = create_app().openapi()["paths"]
    profile_paths = {
        path: {
            method: operation["responses"].keys() & {"200", "201", "204"}
            for method, operation in path_item.items()
            if method in {"get", "post", "patch", "delete"}
        }
        for path, path_item in paths.items()
        if path.startswith("/api/profiles") or path.startswith("/api/export/profiles")
    }

    assert profile_paths == {
        path: {method: {status_code} for method, status_code in operations.items()}
        for path, operations in PROFILE_API_OPERATIONS.items()
    }


def test_openapi_profile_read_response_keeps_all_public_profile_fields():
    profile_read = create_app().openapi()["components"]["schemas"]["ProfileRead"]

    assert set(profile_read["properties"]) == {
        "id",
        "name",
        "description",
        "schema_version",
        "flags",
        "compliance",
        "baseline_provenance",
        "baseline_display",
        "extension_provenance",
        "certificate_provenance",
        "revision",
        "created_at",
        "updated_at",
        "deleted_at",
        "is_deleted",
        "validation_state",
        "recommendation",
    }


def test_openapi_new_profile_preparation_accepts_catalog_identities_only():
    operation = create_app().openapi()["paths"]["/api/profiles/prepare/new"]["post"]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]

    assert operation["summary"] == "Create prepared new profile"
    assert set(schema["properties"]) == {
        "name",
        "target_schema_id",
        "starter_id",
        "cis_baseline_id",
        "preparation_idempotency_key",
    }
    assert schema["required"] == [
        "name",
        "target_schema_id",
        "starter_id",
        "cis_baseline_id",
        "preparation_idempotency_key",
    ]
    assert schema["additionalProperties"] is False
    for response_code in ("409", "422", "500"):
        response_schema = operation["responses"][response_code]["content"]["application/json"][
            "schema"
        ]
        assert response_schema["$ref"] == "#/components/schemas/ProfilePreparationErrorEnvelope"

    error_example = create_app().openapi()["components"]["schemas"][
        "ProfilePreparationErrorEnvelope"
    ]["example"]
    assert error_example == {
        "detail": {
            "kind": "profile-preparation-error",
            "contract_version": 1,
            "code": "preparation_conversion_blocked",
            "i18n_key": "profiles.preparation_error_preparation_conversion_blocked",
            "http_status": 409,
            "mutation": "none",
            "parameters": {},
        }
    }
    assert "flags" not in str(error_example)


def test_openapi_duplicate_preparation_accepts_source_revision_and_retry_key_only():
    operation = create_app().openapi()["paths"]["/api/profiles/prepare/duplicate"]["post"]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]

    assert operation["summary"] == "Create prepared duplicate profile"
    assert set(schema["properties"]) == {
        "name",
        "target_schema_id",
        "starter_id",
        "cis_baseline_id",
        "source_id",
        "expected_source_revision",
        "preparation_idempotency_key",
    }
    assert schema["additionalProperties"] is False
    assert "flags" not in schema["properties"]
    assert "compliance" not in schema["properties"]
    assert "baseline_provenance" not in schema["properties"]
    for response_code in ("404", "409", "422", "500"):
        response_schema = operation["responses"][response_code]["content"]["application/json"][
            "schema"
        ]
        assert response_schema["$ref"] == "#/components/schemas/ProfilePreparationErrorEnvelope"


def test_openapi_patch_declares_the_schema_relabel_conflict_envelope():
    operation = create_app().openapi()["paths"]["/api/profiles/{profile_id}"]["patch"]

    assert operation["responses"]["409"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ProfileUpdateConflictErrorEnvelope"
    }


def test_openapi_import_schema_uses_firefox_document_shape():
    operation = create_app().openapi()["paths"]["/api/profiles/import/firefox/policies.json"][
        "post"
    ]
    request_body = operation["requestBody"]["content"]
    import_schema = request_body["application/json"]["schema"]
    multipart_schema = request_body["multipart/form-data"]["schema"]
    properties = import_schema["properties"]

    assert "document" in properties
    assert "flags" not in properties
    assert properties["document"]["description"].startswith("Full Firefox policies.json document.")
    assert import_schema["example"]["document"] == {
        "policies": {
            "DisableTelemetry": True,
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": True,
                    "Status": "locked",
                }
            },
        }
    }
    assert multipart_schema["required"] == ["file"]
    assert multipart_schema["properties"]["file"]["format"] == "binary"
