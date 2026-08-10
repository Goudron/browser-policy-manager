from __future__ import annotations

import pytest

from tools.report_postgres_ci_evidence import (
    PostgreSqlEvidence,
    PostgreSqlEvidenceError,
    _required_url,
    _sync_url,
    summary_lines,
)


def test_postgres_ci_evidence_accepts_only_disposable_asyncpg_target(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        "BPM_POSTGRES_TEST_URL", "postgresql+asyncpg://postgres:secret@localhost:5432/bpm_m4_05"
    )

    assert _required_url().endswith("/bpm_m4_05")
    assert _sync_url(_required_url()).startswith("postgresql+psycopg://")

    monkeypatch.setenv(
        "BPM_POSTGRES_TEST_URL", "postgresql+asyncpg://postgres:secret@localhost:5432/production"
    )
    with pytest.raises(PostgreSqlEvidenceError, match="disposable bpm_m4_05"):
        _required_url()


def test_postgres_ci_evidence_summary_is_safe_and_includes_all_required_facts():
    lines = summary_lines(
        PostgreSqlEvidence(
            database="bpm_m4_05",
            role="postgres",
            server_version="17.6",
            client_version="3.2.10",
            migration_head="20260804_add_profile_name_casefold",
        )
    )
    rendered = "\n".join(lines)

    assert "Service version" in rendered
    assert "Client version" in rendered
    assert "Alembic migration head" in rendered
    assert "password" not in rendered.lower()
    assert "secret" not in rendered.lower()
