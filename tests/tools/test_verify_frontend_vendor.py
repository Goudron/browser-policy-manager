from __future__ import annotations

import json

from tools import verify_frontend_vendor


def test_frontend_vendor_lock_matches_checked_in_assets():
    assert verify_frontend_vendor._check_lock() == []


def test_frontend_vendor_lock_tracks_expected_packages_and_assets():
    lock = json.loads(verify_frontend_vendor.LOCK_PATH.read_text(encoding="utf-8"))

    assert lock["packages"] == {
        "js-yaml": "4.2.0",
        "monaco-editor": "0.52.0",
        "esbuild": "0.25.3",
    }
    assert [entry["path"] for entry in lock["assets"]] == list(
        verify_frontend_vendor.LOCKED_ASSET_PATHS
    )


def test_frontend_vendor_license_checks_pass():
    assert verify_frontend_vendor._check_licenses() == []


def test_frontend_vendor_size_report_mentions_locked_assets():
    report = verify_frontend_vendor._size_report()

    assert "Frontend vendor size report:" in report
    assert "profiles_monaco.js" in report
    assert "monaco-json.worker.js" in report
