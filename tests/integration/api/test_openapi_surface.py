from app.main import create_app

PROFILE_API_OPERATIONS = {
    "/api/profiles": {"get": "200", "post": "201"},
    "/api/profiles/stats": {"get": "200"},
    "/api/profiles/reset": {"delete": "200"},
    "/api/profiles/{profile_id}": {"get": "200", "patch": "200", "delete": "204"},
    "/api/profiles/{profile_id}/hard": {"delete": "204"},
    "/api/profiles/{profile_id}/restore": {"post": "200"},
    "/api/profiles/import/firefox/policies.json": {"post": "201"},
    "/api/export/profiles/{profile_id}/firefox/policies.json": {"get": "200"},
}


def test_openapi_uses_profiles_surface_for_export_and_crud():
    paths = create_app().openapi()["paths"]

    assert "/api/profiles" in paths
    assert "/api/profiles/{profile_id}" in paths
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
        "revision",
        "created_at",
        "updated_at",
        "deleted_at",
        "is_deleted",
        "validation_state",
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
