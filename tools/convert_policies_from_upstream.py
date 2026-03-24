#!/usr/bin/env python
"""
Convert Mozilla policy-templates documentation to internal JSON policy schemas.

Usage (from project root):

    python tools/convert_policies_from_upstream.py

This script expects that you have already downloaded the HTML documentation
from https://mozilla.github.io/policy-templates/ and saved it to:

    data/upstream/policy-templates/policy-templates.html

It will generate two JSON schema files:

    app/schemas/policies/firefox-release-148.json
    app/schemas/policies/firefox-esr-140.json

These files are emitted as raw JSON Schema bundles with BPM metadata stored
under ``x-bpm-*`` extension keys.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.convert_policies_from_upstream_lib import api as _api
from tools.convert_policies_from_upstream_lib.cli import main

globals().update({name: getattr(_api, name) for name in _api.__all__})


if __name__ == "__main__":
    main()
