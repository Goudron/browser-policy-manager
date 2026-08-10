from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LIVE_E2E_PATH = REPO_ROOT / "tests/live/firefox/test_persisted_profile_e2e.py"
HARNESS_PATH = REPO_ROOT / "tests/live/firefox/conftest.py"


def test_persisted_firefox_e2e_must_cross_public_bpm_persistence_and_export_boundary():
    source = LIVE_E2E_PATH.read_text(encoding="utf-8")

    assert 'requests.post(f"{base_url}/api/profiles"' in source
    assert 'requests.get(f"{base_url}/api/profiles/{profile_id}"' in source
    assert "/api/export/profiles/{profile_id}/firefox/policies.json?indent=2" in source
    assert "run_test_app_server" in source
    assert "render_firefox_policies_document" not in source


def test_persisted_firefox_e2e_installs_the_export_response_without_rerendering():
    source = LIVE_E2E_PATH.read_text(encoding="utf-8")
    harness = HARNESS_PATH.read_text(encoding="utf-8")

    assert "firefox_run_exported_document" in source
    assert "exported.content" in source
    assert "policy_path.read_bytes() == exported.content" in source
    assert "write_policies_json_bytes" in harness
    exported_fixture = harness.split("def firefox_run_exported_document", maxsplit=1)[1]
    assert "render_firefox_policies_document(" not in exported_fixture


def test_persisted_firefox_e2e_observes_each_required_runtime_effect():
    source = LIVE_E2E_PATH.read_text(encoding="utf-8")

    for required in (
        "assert_no_policy_errors",
        "get_requested_locales",
        "network.proxy.http",
        "network.proxy.http_port",
        "is_pref_locked",
        "http_proxy_site.requests",
    ):
        assert required in source


def test_deterministic_firefox_make_target_includes_persisted_profile_e2e():
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    target = makefile.split("test-firefox-live:", maxsplit=1)[1].split(
        "test-firefox-live-amo:", maxsplit=1
    )[0]
    assert "tests/live/firefox/test_policy_scenarios.py" in target
    assert "tests/live/firefox/test_persisted_profile_e2e.py" in target
