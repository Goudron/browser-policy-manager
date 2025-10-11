from app.services.importer import normalize_policies


def test_normalize_accepts_policies_root():
    data = {"policies": {"DisableTelemetry": True}}
    policies, warnings = normalize_policies(data)
    assert policies == {"DisableTelemetry": True}
    assert warnings == []


def test_normalize_accepts_plain_root():
    data = {"DisableTelemetry": True}
    policies, warnings = normalize_policies(data)
    assert policies == {"DisableTelemetry": True}
    assert warnings == []


def test_normalize_rejects_non_object():
    policies, warnings = normalize_policies([1, 2, 3])
    assert policies == {}
    assert warnings and "object" in warnings[0].lower()
