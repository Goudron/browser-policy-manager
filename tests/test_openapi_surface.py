from app.main import create_app


def test_openapi_uses_profiles_surface_for_export_and_crud():
    paths = create_app().openapi()["paths"]

    assert "/api/profiles" in paths
    assert "/api/profiles/{profile_id}" in paths
    assert "/api/profiles/{profile_id}/restore" in paths

    assert "/api/export/profiles" in paths
    assert "/api/export/profiles/{profile_id}" in paths
    assert "/api/export/profiles/{profile_id}.json" in paths
    assert "/api/export/profiles/{profile_id}.yaml" in paths

    assert "/api/export/policies" not in paths
    assert "/api/export/{policy_id}/policies.json" not in paths
    assert "/api/export/{policy_id}/policies.yaml" not in paths

    assert paths["/api/profiles"]["get"]["summary"] == "List profiles"
    assert paths["/api/export/profiles"]["get"]["summary"] == "Export profiles collection"
