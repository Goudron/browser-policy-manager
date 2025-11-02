from fastapi.testclient import TestClient

from app.main import app


def test_policies_not_found_branches_get_delete_restore():
    """Exercise 404 branches in app/api/policies.py."""
    client = TestClient(app)

    # GET not found
    r_get = client.get("/api/policies/999999")
    assert r_get.status_code == 404

    # DELETE not found
    r_del = client.delete("/api/policies/999999")
    assert r_del.status_code == 404

    # RESTORE not found
    r_res = client.post("/api/policies/999999/restore")
    assert r_res.status_code == 404
