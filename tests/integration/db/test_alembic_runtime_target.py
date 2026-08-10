from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HEAD_REVISION = "20260804_add_profile_name_casefold"


def test_alembic_cli_uses_the_bpm_runtime_database_url(tmp_path: Path):
    target = tmp_path / "runtime-target.db"
    environment = os.environ | {"BPM_DATABASE_URL": f"sqlite+aiosqlite:///{target}"}

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchall() == [
            (HEAD_REVISION,)
        ]
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'profiles'"
        ).fetchone() == ("profiles",)


def test_alembic_default_matches_the_local_bpm_runtime_database_path():
    alembic_ini = (REPO_ROOT / "alembic.ini").read_text(encoding="utf-8")

    assert "sqlalchemy.url = sqlite:///./data/bpm.db" in alembic_ini
