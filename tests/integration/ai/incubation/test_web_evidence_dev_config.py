from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from app.core.config import Settings
from app.documentation.web_evidence_dev_config import assess_external_sources, main


def _settings(*, enabled: bool = False, token: str | None = None) -> Settings:
    return Settings(
        _env_file=None,
        WEB_EVIDENCE_ENABLED=enabled,
        BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN=token,
    )


def test_dev_readiness_distinguishes_disabled_missing_and_available_without_probe() -> None:
    disabled = assess_external_sources(_settings())
    missing = assess_external_sources(_settings(enabled=True))
    available = assess_external_sources(
        _settings(enabled=True, token="never-render-this-server-secret")
    )

    assert (disabled.state, disabled.reason_code) == (
        "disabled",
        "assistant_web_disabled",
    )
    assert (missing.state, missing.reason_code) == (
        "credential_missing",
        "assistant_web_credential_unavailable",
    )
    assert (available.state, available.available, available.reason_code) == (
        "available",
        True,
        "assistant_web_available",
    )
    assert all(
        readiness.provider_probe_performed is False for readiness in (disabled, missing, available)
    )
    assert "never-render-this-server-secret" not in repr(available)


def test_dev_cli_json_is_content_free_and_make_dev_runs_the_check(monkeypatch, capsys) -> None:
    secret = "never-render-this-server-secret"
    monkeypatch.setenv("BPM_WEB_EVIDENCE_ENABLED", "true")
    monkeypatch.setenv("BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN", secret)
    from app.documentation import web_evidence_dev_config as module

    module.get_settings.cache_clear()
    try:
        assert main(["--json"]) == 0
    finally:
        module.get_settings.cache_clear()

    output = capsys.readouterr().out
    assert '"state": "available"' in output
    assert '"provider_probe_performed": false' in output
    assert secret not in output

    makefile = Path("Makefile").read_text(encoding="utf-8")
    assert (
        "dev: docs-install-dev ai-model-install-dev ai-runtime-install-dev ai-rag-install-dev ai-web-sources-check-dev"
        in makefile
    )
    assert "$(PYTHON) -m app.documentation.web_evidence_dev_config" in makefile


def test_dev_cli_human_output_and_module_entrypoint_are_safe(monkeypatch, capsys) -> None:
    monkeypatch.setenv("BPM_WEB_EVIDENCE_ENABLED", "false")
    from app.documentation import web_evidence_dev_config as module

    module.get_settings.cache_clear()
    try:
        assert main([]) == 0
        monkeypatch.setattr(sys, "argv", ["web_evidence_dev_config.py"])
        with pytest.raises(SystemExit) as exited:
            runpy.run_path(str(module.__file__), run_name="__main__")
    finally:
        module.get_settings.cache_clear()

    assert exited.value.code == 0
    assert "M13-08: external sources: disabled" in capsys.readouterr().out


def test_readme_keeps_external_source_configuration_outside_the_active_release() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "BPM_WEB_EVIDENCE_ENABLED=true" not in readme
    assert "BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN" not in readme
    assert "No provider token or external-source configuration is required" in readme
    assert "future work" not in readme.lower()
    assert ".env" in Path(".gitignore").read_text(encoding="utf-8")
