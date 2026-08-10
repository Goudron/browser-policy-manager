from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from importlinter.cli import EXIT_STATUS_ERROR, EXIT_STATUS_SUCCESS, lint_imports

REPO_ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_RELEASE_MODULES = (
    "app.ai.e5_runtime",
    "app.ai.local_inference_worker",
    "app.ai.rag_bootstrap",
    "app.documentation.local_assistant_runtime",
    "app.documentation.retrieval",
    "numpy",
    "onnxruntime",
    "tokenizers",
)


def test_repository_import_linter_contracts_pass_without_cache():
    assert (
        lint_imports(
            config_filename=str(REPO_ROOT / "pyproject.toml"),
            no_cache=True,
        )
        == EXIT_STATUS_SUCCESS
    )


def test_forbidden_contract_rejects_an_indirect_incubation_import(tmp_path: Path, monkeypatch):
    package = tmp_path / "architecture_fixture"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "release.py").write_text(
        "from architecture_fixture import adapter\n", encoding="utf-8"
    )
    (package / "adapter.py").write_text("", encoding="utf-8")
    (package / "incubation.py").write_text("", encoding="utf-8")
    config = tmp_path / "pyproject.toml"
    config.write_text(
        """
[tool.importlinter]
root_packages = ["architecture_fixture"]

[[tool.importlinter.contracts]]
name = "release cannot reach incubation"
type = "forbidden"
source_modules = ["architecture_fixture.release"]
forbidden_modules = ["architecture_fixture.incubation"]
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert lint_imports(config_filename=str(config), no_cache=True) == EXIT_STATUS_SUCCESS

    (package / "adapter.py").write_text(
        "from architecture_fixture import incubation\n", encoding="utf-8"
    )
    assert lint_imports(config_filename=str(config), no_cache=True) == EXIT_STATUS_ERROR


def test_default_app_import_does_not_load_incubation_runtime_modules():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, sys; import app.main; "
                f"print(json.dumps(sorted(set(sys.modules) & set({FORBIDDEN_RELEASE_MODULES!r}))))"
            ),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []
