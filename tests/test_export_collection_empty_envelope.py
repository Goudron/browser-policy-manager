from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_export_collection_empty_result_has_envelope():
    """Covers collection export envelope (items/limit/offset/count) for empty set."""
    client = TestClient(app)

    # Use an impossible query that can't match anything
    params = {
        "q": "___NOPE___SHOULD_NOT_MATCH___",
        "limit": 5,
        "offset": 0,
    }

    # Default fmt (JSON)
    rj = client.get("/api/export/policies", params=params)
    assert rj.status_code == 200
    assert rj.headers.get("content-type", "").startswith("application/json")
    # envelope keys
    assert (
        '"items"' in rj.text
        and '"limit"' in rj.text
        and '"offset"' in rj.text
        and '"count"' in rj.text
    )

    # YAML fmt
    ry = client.get("/api/export/policies", params={**params, "fmt": "yaml"})
    assert ry.status_code == 200
    assert any(
        ry.headers.get("content-type", "").startswith(t)
        for t in ("application/x-yaml", "text/yaml", "text/plain")
    )
    # envelope keys in YAML
    txt = ry.text
    assert "items:" in txt and "limit:" in txt and "offset:" in txt and "count:" in txt
