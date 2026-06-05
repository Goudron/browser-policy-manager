from __future__ import annotations

import os
import re
import shutil
import tempfile
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path

_SAFE_WORKER_ID = re.compile(r"[^A-Za-z0-9_.-]+")


def normalize_worker_id(raw_worker_id: str | None) -> str:
    """Return a filesystem-safe pytest worker identifier."""
    normalized = _SAFE_WORKER_ID.sub("-", (raw_worker_id or "main").strip()).strip("-.")
    return normalized or "main"


def sqlite_async_url(path: Path) -> str:
    """Build an absolute aiosqlite URL for a test database path."""
    return f"sqlite+aiosqlite:///{path.resolve()}"


@dataclass(frozen=True)
class WorkerDatabaseContext:
    worker_id: str
    root_dir: Path
    database_path: Path
    database_url: str

    def cleanup(self) -> None:
        shutil.rmtree(self.root_dir, ignore_errors=True)


def configure_worker_database(
    *,
    env: MutableMapping[str, str] | None = None,
    temp_parent: Path | None = None,
) -> WorkerDatabaseContext:
    """
    Configure a unique SQLite database URL before application modules are imported.

    `pytest-xdist` exposes the worker name through `PYTEST_XDIST_WORKER`. A separate
    directory per worker prevents fallback application sessions from sharing
    `./data/bpm.db` or another worker's SQLite file.
    """
    target_env = env if env is not None else os.environ
    worker_id = normalize_worker_id(target_env.get("PYTEST_XDIST_WORKER"))
    configured_root = target_env.get("BPM_TEST_DATABASE_ROOT")

    if configured_root:
        root_dir = Path(configured_root).expanduser().resolve() / worker_id
        shutil.rmtree(root_dir, ignore_errors=True)
        root_dir.mkdir(parents=True, exist_ok=True)
    else:
        parent = temp_parent.resolve() if temp_parent is not None else None
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        root_dir = Path(
            tempfile.mkdtemp(
                prefix=f"bpm-pytest-{worker_id}-",
                dir=str(parent) if parent is not None else None,
            )
        ).resolve()

    database_path = root_dir / "bpm.db"
    database_url = sqlite_async_url(database_path)
    target_env["BPM_DATABASE_URL"] = database_url
    target_env["BPM_TEST_DATABASE_PATH"] = str(database_path)
    target_env["BPM_TEST_WORKER_ID"] = worker_id

    return WorkerDatabaseContext(
        worker_id=worker_id,
        root_dir=root_dir,
        database_path=database_path,
        database_url=database_url,
    )
