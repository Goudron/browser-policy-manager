#!/usr/bin/env python3
"""Verify SQLite backups and create clean, non-promoted Alembic retry candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from alembic.config import Config
from sqlalchemy import create_engine

from alembic import command
from app.db import EXPECTED_DATABASE_REVISION, _assert_release_schema_ready

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DATABASE = (REPO_ROOT / "data" / "bpm.db").resolve()
MANIFEST_VERSION = 1


class RecoveryBoundaryError(RuntimeError):
    """A requested recovery operation crosses the fail-closed safety boundary."""


def _explicit_absolute_path(raw: str, *, must_exist: bool) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        raise RecoveryBoundaryError(f"Path must be explicit and absolute: {raw!r}")
    if must_exist:
        if not path.is_file() or path.is_symlink():
            raise RecoveryBoundaryError(f"Expected a regular, non-symlink file: {path}")
        return path.resolve(strict=True)
    resolved = path.resolve(strict=False)
    if resolved.exists() or path.is_symlink():
        raise RecoveryBoundaryError(f"Refusing to overwrite an existing path: {resolved}")
    if not resolved.parent.is_dir():
        raise RecoveryBoundaryError(f"Parent directory does not exist: {resolved.parent}")
    return resolved


def _reject_repository_path(path: Path) -> None:
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        return
    if path == PROJECT_DATABASE:
        raise RecoveryBoundaryError(
            "Refusing the repository data/bpm.db path; first create and retain an explicit "
            "backup outside the repository"
        )
    raise RecoveryBoundaryError(
        f"Recovery evidence and candidates must stay outside the repo: {path}"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_uri(path: Path) -> str:
    return f"file:{quote(str(path))}?mode=ro"


def _sqlite_summary(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(_sqlite_uri(path), uri=True)
    try:
        connection.execute("PRAGMA query_only = ON")
        integrity = connection.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise RecoveryBoundaryError(f"SQLite integrity_check failed for {path}: {integrity}")
        tables = sorted(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        )
        revisions: list[str] = []
        if "alembic_version" in tables:
            revisions = [
                str(row[0])
                for row in connection.execute(
                    "SELECT version_num FROM alembic_version ORDER BY version_num"
                )
            ]
        row_counts = {
            table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in ("policies", "profiles")
            if table in tables
        }
        return {
            "integrity_check": "ok",
            "tables": tables,
            "alembic_revisions": revisions,
            "profile_table_row_counts": row_counts,
        }
    finally:
        connection.close()


def verify_sqlite_backup(backup: Path, manifest: Path) -> dict[str, Any]:
    backup = _explicit_absolute_path(str(backup), must_exist=True)
    manifest = _explicit_absolute_path(str(manifest), must_exist=False)
    _reject_repository_path(backup)
    _reject_repository_path(manifest)
    if backup.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        raise RecoveryBoundaryError(f"Verified backup must be read-only before use: {backup}")

    payload = {
        "manifest_version": MANIFEST_VERSION,
        "engine": "sqlite",
        "backup_path": str(backup),
        "backup_sha256": _sha256(backup),
        "backup_size_bytes": backup.stat().st_size,
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "database_summary": _sqlite_summary(backup),
    }
    with manifest.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    manifest.chmod(0o444)
    return payload


def _load_verified_manifest(backup: Path, manifest: Path) -> dict[str, Any]:
    backup = _explicit_absolute_path(str(backup), must_exist=True)
    manifest = _explicit_absolute_path(str(manifest), must_exist=True)
    _reject_repository_path(backup)
    _reject_repository_path(manifest)
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryBoundaryError(f"Cannot read verified-backup manifest: {exc}") from exc
    if payload.get("manifest_version") != MANIFEST_VERSION or payload.get("engine") != "sqlite":
        raise RecoveryBoundaryError("Unsupported verified-backup manifest")
    if payload.get("backup_path") != str(backup):
        raise RecoveryBoundaryError("Manifest is bound to a different backup path")
    if payload.get("backup_sha256") != _sha256(backup):
        raise RecoveryBoundaryError("Backup SHA-256 differs from the verified manifest")
    if payload.get("backup_size_bytes") != backup.stat().st_size:
        raise RecoveryBoundaryError("Backup size differs from the verified manifest")
    if payload.get("database_summary") != _sqlite_summary(backup):
        raise RecoveryBoundaryError("Backup database summary differs from the verified manifest")
    return payload


def restore_sqlite_candidate(backup: Path, manifest: Path, candidate: Path) -> None:
    backup = _explicit_absolute_path(str(backup), must_exist=True)
    candidate = _explicit_absolute_path(str(candidate), must_exist=False)
    _reject_repository_path(backup)
    _reject_repository_path(manifest.resolve(strict=False))
    _reject_repository_path(candidate)
    if candidate in {backup, manifest.resolve(strict=False)}:
        raise RecoveryBoundaryError("Backup, manifest, and candidate paths must be distinct")
    payload = _load_verified_manifest(backup, manifest)

    descriptor = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    source = sqlite3.connect(_sqlite_uri(backup), uri=True)
    destination = sqlite3.connect(candidate)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    if _sqlite_summary(candidate) != payload["database_summary"]:
        raise RecoveryBoundaryError("Restored candidate does not match the verified backup summary")


def retry_sqlite_upgrade(backup: Path, manifest: Path, candidate: Path) -> None:
    restore_sqlite_candidate(backup, manifest, candidate)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{candidate}")
    try:
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{candidate}", future=True)
        try:
            with engine.connect() as connection:
                _assert_release_schema_ready(connection)
        finally:
            engine.dispose()
    except BaseException as exc:
        raise RecoveryBoundaryError(
            f"Candidate upgrade failed and was left quarantined at {candidate}: {exc}"
        ) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a retained SQLite backup and create a clean upgrade candidate."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-sqlite-backup")
    verify.add_argument("--backup", required=True)
    verify.add_argument("--manifest", required=True)
    retry = commands.add_parser("retry-sqlite-upgrade")
    retry.add_argument("--backup", required=True)
    retry.add_argument("--manifest", required=True)
    retry.add_argument("--candidate", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify-sqlite-backup":
            print("[1/2] Checking read-only SQLite backup integrity and metadata", flush=True)
            payload = verify_sqlite_backup(Path(args.backup), Path(args.manifest))
            print(
                f"[2/2] Verified backup sha256={payload['backup_sha256']} manifest={args.manifest}",
                flush=True,
            )
        else:
            print("[1/3] Rechecking the retained backup against its manifest", flush=True)
            _load_verified_manifest(Path(args.backup), Path(args.manifest))
            print("[2/3] Restoring a new candidate and running Alembic upgrade head", flush=True)
            retry_sqlite_upgrade(
                Path(args.backup),
                Path(args.manifest),
                Path(args.candidate),
            )
            print(
                f"[3/3] Candidate reached {EXPECTED_DATABASE_REVISION}; no configured "
                "database was replaced",
                flush=True,
            )
    except RecoveryBoundaryError as exc:
        parser = _parser()
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
