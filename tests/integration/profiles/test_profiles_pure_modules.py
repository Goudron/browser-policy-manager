from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULES = ROOT / "app" / "static" / "profiles_modules"


def test_profile_pure_modules_do_not_reference_browser_globals():
    for module in MODULES.glob("*.mjs"):
        source = module.read_text(encoding="utf-8")
        assert "window." not in source
        assert "document." not in source
