from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

REPO_ROOT = Path(__file__).resolve().parents[4]
AI_DISTRIBUTIONS = {"numpy", "onnxruntime", "tokenizers"}
FORBIDDEN_STARTUP_MODULES = {
    "app.ai.e5_runtime",
    "app.ai.local_inference_worker",
    "app.ai.rag_bootstrap",
    "app.documentation.local_assistant_runtime",
    "app.documentation.retrieval",
    *AI_DISTRIBUTIONS,
}


def test_native_ai_dependencies_are_owned_only_by_the_ai_extra() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    base = {canonicalize_name(Requirement(value).name) for value in project["dependencies"]}
    ai = {
        canonicalize_name(Requirement(value).name)
        for value in project["optional-dependencies"]["ai"]
    }

    assert AI_DISTRIBUTIONS.isdisjoint(base)
    assert AI_DISTRIBUTIONS == ai


def test_release_startup_and_routes_do_not_import_optional_ai_runtime() -> None:
    script = f"""
import json
import sys
import app.main

forbidden = {FORBIDDEN_STARTUP_MODULES!r}
paths = {{
    route.path
    for module in (app.main.documentation_assistant, app.main.local_model)
    for route in module.router.routes
}}
print(json.dumps({{
    "loaded": sorted(forbidden & set(sys.modules)),
    "assistant_route": "/api/documentation-assistant/status" in paths,
    "model_route": "/api/local-model" in paths,
}}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "loaded": [],
        "assistant_route": True,
        "model_route": True,
    }
