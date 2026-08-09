from __future__ import annotations

from tools import package_smoke


def test_packaging_declarations_keep_ai_out_of_base_and_extras_explicit() -> None:
    package_smoke.validate_declared_packaging()


def test_package_smoke_declares_required_delivery_assets_and_exclusions() -> None:
    assert "app/main.py" in package_smoke.REQUIRED_ARTIFACT_FILES
    assert "app/services/firefox_policy_export.py" in package_smoke.REQUIRED_ARTIFACT_FILES
    assert {"tests", "tools", "data"} <= package_smoke.FORBIDDEN_ARTIFACT_PARTS
    assert package_smoke.NATIVE_AI_DISTRIBUTIONS.isdisjoint(package_smoke.POSTGRES_DISTRIBUTIONS)
