"""Observable, failure-safe lifecycle helpers for documentation artifacts."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


def remove_path(path: Path) -> None:
    """Remove one controlled temporary path without following directory links."""

    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for an artifact file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class Progress:
    """Report actual completed work; never infer time or synthetic percentages."""

    operation: str
    total: int
    completed: int = 0

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("progress total cannot be negative")

    def phase(self, name: str) -> None:
        print(
            f"{self.operation}: phase={name}; completed={self.completed}/{self.total}",
            flush=True,
        )

    def complete_unit(self, name: str) -> None:
        if self.completed >= self.total:
            raise ValueError("progress completed work exceeds declared total")
        self.completed += 1
        print(
            f"{self.operation}: completed={self.completed}/{self.total}; unit={name}",
            flush=True,
        )

    def terminal(self, state: str) -> None:
        print(
            f"{self.operation}: terminal={state}; completed={self.completed}/{self.total}",
            flush=True,
        )


@contextmanager
def tracked_operation(progress: Progress) -> Iterator[Progress]:
    """Emit one truthful terminal state for successful, failed, or interrupted work."""

    try:
        yield progress
    except KeyboardInterrupt:
        progress.terminal("interrupted")
        raise
    except BaseException:
        progress.terminal("failed")
        raise
    else:
        progress.terminal("complete")


class StagedDirectory:
    """Own a private staging root and preserve failed work in a quarantine directory."""

    def __init__(self, parent: Path, label: str) -> None:
        self.parent = parent
        self.label = label
        self.path: Path | None = None
        self.quarantined_path: Path | None = None

    def __enter__(self) -> StagedDirectory:
        self.parent.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix=f".{self.label}-", dir=self.parent))
        return self

    def candidate(self, name: str) -> Path:
        if self.path is None:
            raise RuntimeError("staging directory is not active")
        candidate = self.path / name
        if candidate.parent != self.path or candidate.name != name:
            raise ValueError(f"unsafe staged candidate name: {name!r}")
        return candidate

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if self.path is None or not self.path.exists():
            return False
        if exc_type is None:
            remove_path(self.path)
            return False
        quarantine_root = self.parent / ".quarantine"
        quarantine_root.mkdir(parents=True, exist_ok=True)
        destination = quarantine_root / f"{self.label}-{time.time_ns()}"
        self.path.replace(destination)
        self.quarantined_path = destination
        print(f"{self.label}: candidate quarantined at {destination}", flush=True)
        return False


def atomic_promote(
    candidate: Path,
    destination: Path,
    *,
    validate: Callable[[Path], None] | None = None,
) -> None:
    """Validate and atomically replace one destination, restoring its last artifact on error."""

    atomic_promote_many(((candidate, destination),), validate=validate)


def atomic_promote_many(
    candidates: tuple[tuple[Path, Path], ...],
    *,
    validate: Callable[[Path], None] | None = None,
) -> None:
    """Promote one artifact set as a rollback-safe transaction on one filesystem."""

    if not candidates:
        raise ValueError("artifact promotion requires at least one candidate")
    destinations = [destination for _candidate, destination in candidates]
    if len(set(destinations)) != len(destinations):
        raise ValueError("artifact promotion destinations must be unique")
    for candidate, _destination in candidates:
        if validate is not None:
            validate(candidate)

    backups: list[tuple[Path, Path, bool]] = []
    promoted: list[Path] = []
    try:
        for _candidate, destination in candidates:
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup = destination.parent / f".{destination.name}-previous"
            remove_path(backup)
            existed = destination.exists() or destination.is_symlink()
            if existed:
                destination.replace(backup)
            backups.append((destination, backup, existed))
        for candidate, destination in candidates:
            candidate.replace(destination)
            promoted.append(destination)
    except BaseException:
        for destination in reversed(promoted):
            remove_path(destination)
        for destination, backup, existed in reversed(backups):
            if existed and (backup.exists() or backup.is_symlink()):
                backup.replace(destination)
        raise
    finally:
        for _destination, backup, _existed in backups:
            remove_path(backup)
