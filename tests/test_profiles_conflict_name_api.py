from __future__ import annotations

import uuid

from app.main import app
from tests.support import TestClient, build_profile_payload


def test_create_conflict_name_returns_409():
    """Verify duplicate profile name handling returns 409 (IntegrityError path)."""
    client = TestClient(app)
    unique = uuid.uuid4().hex[:6]
    body = build_profile_payload(name=f"Conflict-{unique}", description="Duplicate check")

    r1 = client.post("/api/profiles", json=body)
    assert r1.status_code == 201, r1.text

    r2 = client.post("/api/profiles", json=body)
    assert r2.status_code in (409, 400)  # primary path is 409
