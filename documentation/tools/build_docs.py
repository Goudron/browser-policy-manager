#!/usr/bin/env python3
# ruff: noqa: E402, F821, I001
"""Validate and reproducibly publish the six-locale BPM DITA documentation.

This is the stable CLI and compatibility façade.  Owned build responsibilities
live in :mod:`documentation.buildlib` so they can be tested independently.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from documentation.buildlib import artifacts as _artifacts
from documentation.buildlib import catalog as _catalog
from documentation.buildlib import pdf as _pdf
from documentation.buildlib import portal as _portal
from documentation.buildlib import publishing as _publishing
from documentation.buildlib import shared as _shared
from documentation.buildlib import sources as _sources

_OWNERS = (_shared, _sources, _catalog, _portal, _artifacts, _pdf, _publishing)
for _owner in _OWNERS:
    globals().update(
        {_name: _value for _name, _value in vars(_owner).items() if not _name.startswith("__")}
    )
_OWNER_DEFAULTS = {
    _owner: {name: value for name, value in vars(_owner).items()} for _owner in _OWNERS
}


def _sync_compatibility_overrides() -> None:
    """Apply legacy façade monkeypatches to every module that consumes a name."""

    for name, default in _FACADE_DEFAULTS.items():
        value = globals().get(name, default)
        for owner in _OWNERS:
            if name not in _OWNER_DEFAULTS[owner]:
                continue
            setattr(
                owner,
                name,
                _OWNER_DEFAULTS[owner][name] if value is default else value,
            )


def _compatibility_wrapper(owner: object, name: str):
    target = getattr(owner, name)

    def call(*args: object, **kwargs: object) -> object:
        _sync_compatibility_overrides()
        return getattr(owner, name)(*args, **kwargs)

    call.__name__ = target.__name__
    call.__doc__ = target.__doc__
    return call


for _owner in _OWNERS:
    for _name, _value in vars(_owner).items():
        if inspect.isfunction(_value) and _value.__module__ == _owner.__name__:
            globals()[_name] = _compatibility_wrapper(_owner, _name)
_FACADE_DEFAULTS = {name: value for name, value in globals().items()}


def main() -> int:
    """Run the legacy command surface with its established exit diagnostics."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "validate",
            "build",
            "install-dev",
            "fast-check",
            "reproducibility",
            "package",
            "package-verify",
            "pdf-build",
            "pdf-verify",
            "pdf-reproducibility",
        ),
    )
    parser.add_argument("paths", nargs="*", help="changed documentation paths for fast-check")
    args = parser.parse_args()
    try:
        {
            "validate": validate_build,
            "build": publish,
            "install-dev": install_dev_site,
            "fast-check": lambda: fast_check(args.paths),
            "reproducibility": reproducibility_check,
            "package": package,
            "package-verify": verify_package,
            "pdf-build": publish_pdfs,
            "pdf-verify": verify_pdfs,
            "pdf-reproducibility": pdf_reproducibility_check,
        }[args.command]()
    except (BuildError, OSError) as exc:
        print(f"documentation build failed: {exc}", file=sys.stderr)
        if args.command == "fast-check":
            diagnostic = write_failure_diagnostic(exc, args.paths)
            print(
                f"diagnostic artifact: {diagnostic.relative_to(REPOSITORY_ROOT)}",
                file=sys.stderr,
            )
            print(
                f"focused rerun: {_diagnostic_payload(exc, args.paths)['focused_rerun']}",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
