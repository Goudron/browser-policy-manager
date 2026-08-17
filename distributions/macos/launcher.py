"""Native macOS launcher included in the BPM application bundle.

It deliberately keeps database migration separate from server activation. The
source tree is bundled by PyInstaller; no system Python is read or changed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from alembic.config import Config

from alembic import command


def _bundle_root() -> Path:
    """Return the PyInstaller data root, or the repository root in development."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[2]


def _state_directory(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    configured = os.environ.get("BPM_STATE_DIRECTORY")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / "Library" / "Application Support" / "Browser Policy Manager"


def _configure_runtime(state_directory: Path) -> None:
    state_directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("BPM_DATABASE_URL", f"sqlite+aiosqlite:///{state_directory / 'bpm.db'}")
    os.environ.setdefault(
        "BPM_DOCUMENTATION_SITE_DIR", str(_bundle_root() / "documentation" / "site")
    )


def _migrate() -> None:
    config = Config(str(_bundle_root() / "alembic.ini"))
    config.set_main_option("script_location", str(_bundle_root() / "alembic"))
    config.set_main_option("sqlalchemy.url", os.environ["BPM_DATABASE_URL"])
    command.upgrade(config, "head")


def _serve(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, log_level="info")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BPM native macOS launcher")
    parser.add_argument("command", choices=("migrate", "serve"), nargs="?", default="serve")
    parser.add_argument("--state-directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_runtime(_state_directory(args.state_directory))
    if args.command == "migrate":
        _migrate()
    else:
        _serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
