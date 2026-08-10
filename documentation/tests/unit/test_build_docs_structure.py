from __future__ import annotations

from pathlib import Path

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
FACADE = DOCUMENTATION_ROOT / "tools/build_docs.py"
BUILD_LIBRARY = DOCUMENTATION_ROOT / "buildlib"


def test_build_docs_cli_is_a_small_compatible_facade() -> None:
    source = FACADE.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 180
    assert '"validate",' in source
    assert '"pdf-reproducibility",' in source
    assert "documentation build failed:" in source
    assert "diagnostic artifact:" in source
    assert "def build_tree" not in source
    assert "def generate_manifest_files" not in source
    assert "def build_pdf_tree" not in source


def test_documentation_build_responsibilities_have_owned_modules() -> None:
    expected_modules = {
        "shared.py",
        "sources.py",
        "portal.py",
        "catalog.py",
        "pdf.py",
        "artifacts.py",
        "publishing.py",
    }

    assert expected_modules <= {path.name for path in BUILD_LIBRARY.glob("*.py")}
    assert all(
        (BUILD_LIBRARY / module).read_text(encoding="utf-8").strip() for module in expected_modules
    )
