from __future__ import annotations

from app.main import app
from tests.support import TestClient, assert_contains_all, build_profile_payload, make_test_client


def _mk(name_prefix: str, owner: str = "ops@example.org"):
    return build_profile_payload(
        name_prefix=name_prefix,
        owner=owner,
        description="Matrix export",
        flags={"DisableTelemetry": True, "DisablePrivateBrowsing": True},
    )


def _ok_yaml(content_type: str) -> bool:
    return any(
        content_type.startswith(prefix)
        for prefix in ("application/x-yaml", "text/yaml", "text/plain")
    )


def _ensure_created(client: TestClient, n: int, prefix: str) -> list[int]:
    ids: list[int] = []
    for _ in range(n):
        response = client.post("/api/profiles", json=_mk(prefix))
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    return ids


def _seed_matrix_profiles(prefix: str = "MATRIX") -> tuple[TestClient, list[int]]:
    client = make_test_client(app)
    ids = _ensure_created(client, 2, prefix)
    return client, ids


def _assert_single_export_response(response, fmt: str) -> None:
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    if fmt == "json":
        assert content_type.startswith("application/json")
        assert '"DisableTelemetry"' in response.text
    else:
        assert _ok_yaml(content_type)
        assert "DisableTelemetry" in response.text

    if content_disposition := response.headers.get("content-disposition", ""):
        assert "attachment" in content_disposition.lower()
        assert f".{fmt}" in content_disposition.lower()


def _assert_collection_envelope(response, fmt: str) -> None:
    assert response.status_code == 200
    if fmt == "json":
        assert response.headers.get("content-type", "").startswith("application/json")
        assert_contains_all(response.text, ('"items"', '"limit"', '"offset"', '"count"'))
    else:
        assert _ok_yaml(response.headers.get("content-type", ""))
        assert_contains_all(response.text, ("items:", "limit:", "offset:", "count:"))


def test_export_single_suffix_matrix():
    client, ids = _seed_matrix_profiles()
    profile_id = ids[0]

    for fmt in ("json", "yaml"):
        base_url = f"/api/export/profiles/{profile_id}.{fmt}"
        for download in ("0", "1"):
            for indent in (None, "2"):
                for pretty in ("0", "1"):
                    query = []
                    if download == "1":
                        query.append("download=1")
                    if indent is not None:
                        query.append(f"indent={indent}")
                    if pretty == "1":
                        query.append("pretty=1")
                    url = base_url + (("?" + "&".join(query)) if query else "")
                    response = client.get(url)
                    _assert_single_export_response(response, fmt)


def test_export_single_queryparam_matrix():
    client, ids = _seed_matrix_profiles()
    profile_id = ids[0]

    for fmt in ("json", "yaml"):
        for download in ("0", "1"):
            for indent in (None, "2"):
                for pretty in ("0", "1"):
                    query = [f"fmt={fmt}"]
                    if download == "1":
                        query.append("download=1")
                    if indent is not None:
                        query.append(f"indent={indent}")
                    if pretty == "1":
                        query.append("pretty=1")
                    response = client.get(f"/api/export/profiles/{profile_id}?" + "&".join(query))
                    _assert_single_export_response(response, fmt)


def test_export_single_deleted_not_found_and_bad_format_paths():
    client, ids = _seed_matrix_profiles()
    profile_id = ids[0]
    bad_id = 9_999_999

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_json = client.get(f"/api/export/profiles/{profile_id}?fmt=json")
    hidden_yaml = client.get(f"/api/export/profiles/{profile_id}?fmt=yaml")
    assert hidden_json.status_code == 404
    assert hidden_yaml.status_code == 404

    deleted_json = client.get(f"/api/export/profiles/{profile_id}?fmt=json&include_deleted=true")
    deleted_yaml = client.get(f"/api/export/profiles/{profile_id}?fmt=yaml&include_deleted=true")
    _assert_single_export_response(deleted_json, "json")
    _assert_single_export_response(deleted_yaml, "yaml")

    bad_suffix_json = client.get(f"/api/export/profiles/{bad_id}.json")
    bad_suffix_yaml = client.get(f"/api/export/profiles/{bad_id}.yaml")
    assert bad_suffix_json.status_code == 404
    assert bad_suffix_yaml.status_code == 404

    bad_query_json = client.get(f"/api/export/profiles/{bad_id}?fmt=json")
    bad_query_yaml = client.get(f"/api/export/profiles/{bad_id}?fmt=yaml")
    assert bad_query_json.status_code == 404
    assert bad_query_yaml.status_code == 404

    bad_format = client.get(f"/api/export/profiles/{profile_id}?fmt=txt")
    assert bad_format.status_code == 422


def test_export_collection_default_and_filtered_json_yaml():
    client, _ = _seed_matrix_profiles()

    default_json = client.get("/api/export/profiles?limit=1&offset=0&pretty=1&indent=2")
    _assert_collection_envelope(default_json, "json")

    filtered_json = client.get(
        "/api/export/profiles",
        params={
            "fmt": "json",
            "download": "1",
            "owner": "ops@example.org",
            "schema_version": "esr-140.9",
            "q": "MATRIX-",
            "include_deleted": "true",
            "limit": 2,
            "offset": 0,
            "sort": "updated_at",
            "order": "desc",
        },
    )
    _assert_collection_envelope(filtered_json, "json")
    if content_disposition := filtered_json.headers.get("content-disposition", ""):
        assert ".json" in content_disposition.lower()

    filtered_yaml = client.get(
        "/api/export/profiles",
        params={
            "fmt": "yaml",
            "download": "1",
            "owner": "ops@example.org",
            "schema_version": "esr-140.9",
            "q": "MATRIX-",
            "include_deleted": "true",
            "limit": 3,
            "offset": 0,
            "sort": "name",
            "order": "asc",
        },
    )
    _assert_collection_envelope(filtered_yaml, "yaml")
    if content_disposition := filtered_yaml.headers.get("content-disposition", ""):
        assert ".yaml" in content_disposition.lower()


def test_export_collection_empty_envelopes_for_json_and_yaml():
    client, _ = _seed_matrix_profiles()

    empty_json = client.get("/api/export/profiles?q=__NO_MATCH_EXPECTED__")
    _assert_collection_envelope(empty_json, "json")

    empty_yaml = client.get("/api/export/profiles?fmt=yaml&q=__NO_MATCH_EXPECTED__")
    _assert_collection_envelope(empty_yaml, "yaml")
