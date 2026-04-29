from app.main import create_app


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


def test_openapi_import_schema_uses_firefox_document_shape():
    operation = create_app().openapi()["paths"][
        "/api/profiles/import/firefox/policies.json"
    ]["post"]
    request_body = operation["requestBody"]["content"]
    import_schema = request_body["application/json"]["schema"]
    multipart_schema = request_body["multipart/form-data"]["schema"]
    properties = import_schema["properties"]

    assert "document" in properties
    assert "flags" not in properties
    assert properties["document"]["description"].startswith(
        "Full Firefox policies.json document."
    )
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
