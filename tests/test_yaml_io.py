from __future__ import annotations

from app.utils.yaml_io import to_yaml


def test_to_yaml_basic():
    data = {"a": 1, "b": True, "nested": {"x": "y"}}
    s = to_yaml(data)
    assert isinstance(s, str)
    assert "a: 1" in s
    assert "b: true" in s
    assert "nested:" in s
