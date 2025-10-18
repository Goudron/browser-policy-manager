import yaml

from app.exporters.firefox import build_form_payload_from_policies, build_policies


def load_schema():
    with open("app/schemas/firefox.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f.read())


def test_boolean_and_object_export_ok():
    schema = load_schema()
    payload = {
        "disable_app_update": True,
        "homepage": '{"URL":"https://intranet","Locked":true,"StartPage":"homepage"}',
        "extensions": "https://addons.mozilla.org/.../xpi\nfile:///opt/addons/acme.xpi",
    }
    policies = build_policies(payload, schema)
    assert policies["policies"]["DisableAppUpdate"] is True
    assert policies["policies"]["Homepage"]["Locked"] is True
    assert isinstance(policies["policies"]["Extensions"], list)
    assert len(policies["policies"]["Extensions"]) == 2


def test_ignore_invalid_json_object():
    schema = load_schema()
    payload = {"homepage": "{not_json"}
    policies = build_policies(payload, schema)
    assert "Homepage" not in policies["policies"]


def test_reverse_parser_roundtrip():
    schema = load_schema()
    policies = {
        "policies": {
            "DisableAppUpdate": True,
            "Extensions": ["a.xpi", "b.xpi"],
            "Homepage": {
                "URL": "https://intra",
                "Locked": True,
                "StartPage": "homepage",
            },
        }
    }
    form_payload = build_form_payload_from_policies(policies, schema)
    assert form_payload["disable_app_update"] is True
    assert "a.xpi" in form_payload["extensions"]
    assert form_payload["homepage"].startswith("{")
    rebuilt = build_policies(form_payload, schema)
    assert rebuilt["policies"]["DisableAppUpdate"] is True
    assert rebuilt["policies"]["Extensions"] == ["a.xpi", "b.xpi"]
