from app.main import app
from tests.support import make_test_client


def test_profiles_not_found_branches_get_delete_restore():
    """Exercise 404 branches in app/api/profiles.py."""
    client = make_test_client(app)

    # GET not found
    r_get = client.get("/api/profiles/999999")
    assert r_get.status_code == 404

    # DELETE not found
    r_del = client.delete("/api/profiles/999999")
    assert r_del.status_code == 404

    # RESTORE not found
    r_res = client.post("/api/profiles/999999/restore")
    assert r_res.status_code == 404
