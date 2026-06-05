from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _workflow_source(filename: str) -> str:
    return (WORKFLOWS_DIR / filename).read_text(encoding="utf-8")


def test_ci_workflow_splits_mandatory_fast_and_coverage_layers():
    source = _workflow_source("ci.yml")

    assert "fast-tests:" in source
    assert "name: Mandatory fast tests" in source
    assert "make test-fast" in source
    assert "coverage-and-contracts:" in source
    assert "name: Coverage and contract checks" in source
    assert "make test-contract" in source
    assert '-m "not browser_ui and not firefox_live and not firefox_live_amo"' in source
    assert "--cov-fail-under=85" in source


def test_ci_workflow_verifies_frontend_vendor_lock():
    source = _workflow_source("ci.yml")

    assert "make verify-frontend-vendor" in source
    assert "test -f app/static/vendor/js-yaml.js" not in source


def test_ci_workflow_uses_make_targets_for_quality_commands():
    source = _workflow_source("ci.yml")

    assert "make lint" in source
    assert "make typecheck" in source
    assert "ruff check ." not in source
    assert "mypy app" not in source


def test_ci_workflow_keeps_browser_ui_manual_only():
    source = _workflow_source("ci.yml")

    assert "run-browser-ui:" in source
    assert "browser-ui:" in source
    assert "name: Browser UI checks" in source
    assert "github.event_name == 'workflow_dispatch' && inputs.run-browser-ui" in source
    assert "make test-ui" in source
    assert "make test-ui" not in source.split("fast-tests:", maxsplit=1)[1].split(
        "coverage-and-contracts:",
        maxsplit=1,
    )[0]


def test_ci_workflow_does_not_enable_xdist_in_mandatory_jobs():
    source = _workflow_source("ci.yml")

    assert " -n " not in source
    assert "pytest-xdist" not in source


def test_xdist_pilot_workflow_is_manual_and_narrow():
    source = _workflow_source("xdist-pilot.yml")

    assert "workflow_dispatch:" in source
    assert "pull_request:" not in source
    assert "push:" not in source
    assert "schedule:" not in source
    assert "make test-unit-xdist XDIST_WORKERS=2" in source
    assert "make test-fast" not in source
    assert "make test-contract" not in source
    assert "make test-ui" not in source
    assert "make test-live" not in source


def test_firefox_live_workflows_are_scheduled_or_manual_only():
    for filename in ("firefox-live.yml", "firefox-live-amo.yml"):
        source = _workflow_source(filename)

        assert "schedule:" in source
        assert "workflow_dispatch:" in source
        assert "pull_request:" not in source
        assert "push:" not in source


def test_firefox_live_workflows_use_make_targets():
    live_source = _workflow_source("firefox-live.yml")
    amo_source = _workflow_source("firefox-live-amo.yml")

    assert 'make setup-firefox-live-browsers FIREFOX_CHANNEL="${{ matrix.channel }}"' in live_source
    assert "make test-firefox-live" in live_source
    assert "tools/setup_firefox_live_browsers.sh" not in live_source
    assert "test_policy_activation.py" not in live_source

    assert 'make setup-firefox-live-browsers FIREFOX_CHANNEL="${{ matrix.channel }}"' in amo_source
    assert "make test-firefox-live-amo" in amo_source
    assert "tools/setup_firefox_live_browsers.sh" not in amo_source
    assert "test_extension_settings_amo.py" not in amo_source
