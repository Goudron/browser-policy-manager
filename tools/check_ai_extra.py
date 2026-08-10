"""Fail-fast dependency check for explicit AI-incubation commands."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import sys

REQUIRED_DISTRIBUTIONS = {
    "numpy": "numpy",
    "onnxruntime": "onnxruntime",
    "tokenizers": "tokenizers",
}


def main() -> int:
    missing = [
        distribution
        for module, distribution in REQUIRED_DISTRIBUTIONS.items()
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        print(
            "AI incubation extra is unavailable; install it with "
            '`python -m pip install -e ".[dev,ai]"`.',
            file=sys.stderr,
            flush=True,
        )
        print(f"Missing distributions: {', '.join(missing)}", file=sys.stderr, flush=True)
        return 2
    versions = ", ".join(
        f"{distribution}={importlib.metadata.version(distribution)}"
        for distribution in REQUIRED_DISTRIBUTIONS.values()
    )
    print(f"AI incubation extra ready: {versions}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
