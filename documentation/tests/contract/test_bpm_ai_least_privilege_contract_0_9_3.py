from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai import least_privilege

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-ai-least-privilege-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_05_keeps_network_and_future_transport_fail_closed_without_a_route() -> None:
    contract = _contract()

    assert contract["process"]["environment"] == {
        "PATH": "",
        "LC_ALL": "C",
        "NO_PROXY": "*",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "ALL_PROXY": "",
    }
    assert contract["network"] == {
        "local_worker": "offline and proxy-free; it inherits no process environment or credentials",
        "model_download": (
            "explicit install only, one pinned HTTPS source, no redirect following and no proxy environment inheritance"
        ),
        "web_evidence": "absent; nonlocal sources remain rejected until M9",
        "arbitrary_model_url": False,
        "ssrf_surface": False,
    }
    assert contract["future_assistant_transport"] == {
        "status": "guard implemented without adding a route",
        "method": "POST",
        "content_type": "application/json",
        "origin": (
            "exact configured http(s) origin and Host; wildcard, cross-origin and preflight are rejected"
        ),
        "fetch_metadata": "Sec-Fetch-Site, when present, must be same-origin",
        "content_length_max": least_privilege.ASSISTANT_MAX_REQUEST_BYTES,
    }
    assert contract["acceptance"] == {
        "http_route": False,
        "browser_ui": False,
        "ordinary_search_import": False,
        "path_traversal": "rejected",
        "symlink_escape": "rejected",
        "shell_metacharacters": "rejected",
        "cross_origin": "rejected",
        "resource_flood": "rejected before a second active or queued worker can be created",
    }
