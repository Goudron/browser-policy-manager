#!/usr/bin/env python3
"""Report the disposable PostgreSQL CI service and Alembic-head evidence.

The database integration suite is responsible for exercising all migrations and
the shared runtime contract.  This small, read-only post-suite command makes
the service/client versions and the exact resulting migration head visible in
the GitHub Actions summary without logging the connection URL or password.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

REPO_ROOT = Path(__file__).resolve().parents[1]
_DISPOSABLE_DATABASE = re.compile(r"^bpm_m4_05(?:_[a-z0-9]+)*$")


class PostgreSqlEvidenceError(RuntimeError):
    """Raised when CI evidence is absent, unsafe, or does not prove Alembic head."""


@dataclass(frozen=True)
class PostgreSqlEvidence:
    """Read-only facts that are safe to publish in CI output."""

    database: str
    role: str
    server_version: str
    client_version: str
    migration_head: str


def _required_url() -> str:
    url = os.environ.get("BPM_POSTGRES_TEST_URL", "")
    if not url:
        raise PostgreSqlEvidenceError(
            "BPM_POSTGRES_TEST_URL is required for PostgreSQL CI evidence"
        )
    if not url.startswith("postgresql+") or "+asyncpg" not in url:
        raise PostgreSqlEvidenceError(
            "BPM_POSTGRES_TEST_URL must use the PostgreSQL asyncpg driver"
        )
    database = make_url(url).database or ""
    if not _DISPOSABLE_DATABASE.fullmatch(database):
        raise PostgreSqlEvidenceError(
            "PostgreSQL CI evidence refuses a database outside the disposable bpm_m4_05* scope"
        )
    return url


def _sync_url(async_url: str) -> str:
    """Convert the service URL to the installed, synchronous reporting driver."""

    return (
        make_url(async_url)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )


def _expected_head() -> str:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if not head:
        raise PostgreSqlEvidenceError("Alembic script directory has no current head")
    return head


def collect_evidence(async_url: str) -> PostgreSqlEvidence:
    """Read current server facts and require that the disposable service is at Alembic head."""

    import psycopg

    expected_head = _expected_head()
    engine = create_engine(_sync_url(async_url), future=True)
    try:
        with engine.connect() as connection:
            database, role = connection.execute(
                text("SELECT current_database(), current_user")
            ).one()
            server_version = connection.execute(text("SHOW server_version")).scalar_one()
            revisions = (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            )
    finally:
        engine.dispose()

    if not isinstance(database, str) or not _DISPOSABLE_DATABASE.fullmatch(database):
        raise PostgreSqlEvidenceError(
            "connected PostgreSQL service is outside the disposable scope"
        )
    if revisions != [expected_head]:
        raise PostgreSqlEvidenceError(
            "PostgreSQL integration suite did not leave the disposable service at the Alembic head"
        )
    return PostgreSqlEvidence(
        database=database,
        role=str(role),
        server_version=str(server_version),
        client_version=psycopg.__version__,
        migration_head=expected_head,
    )


def summary_lines(evidence: PostgreSqlEvidence) -> list[str]:
    """Return safe, concise terminal and GitHub-summary output."""

    return [
        "## PostgreSQL integration evidence",
        "",
        f"- Disposable database: `{evidence.database}`",
        f"- Service version: `{evidence.server_version}`",
        f"- Client version: `psycopg {evidence.client_version}`",
        f"- Role: `{evidence.role}`",
        f"- Alembic migration head: `{evidence.migration_head}`",
        "- State: read-only post-suite proof; GitHub Actions tears down the service after the job.",
    ]


def _append_github_summary(lines: list[str]) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with Path(target).open("a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")


def main() -> int:
    evidence = collect_evidence(_required_url())
    lines = summary_lines(evidence)
    print("\n".join(lines))
    _append_github_summary(lines)
    return 0


if __name__ == "__main__":  # pragma: no cover - covered through the Make/CI command.
    raise SystemExit(main())
