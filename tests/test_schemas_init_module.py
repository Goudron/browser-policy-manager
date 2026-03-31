from __future__ import annotations

import importlib


def test_legacy_schemas_init_module_exports_schema_manager_symbols():
    module = importlib.import_module("app.schemas.init")

    assert module.SchemaManager is not None
    assert module.SchemaVersion is not None
    assert "SchemaManager" in module.__all__
    assert "SchemaVersion" in module.__all__
