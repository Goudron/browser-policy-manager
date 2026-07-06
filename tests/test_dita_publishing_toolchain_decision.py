from pathlib import Path

DECISION_PATH = Path("docs/architecture/dita-publishing-toolchain-decision-0.9.0.md")


def _decision() -> str:
    return DECISION_PATH.read_text(encoding="utf-8")


def test_dita_toolchain_decision_pins_engine_runtime_formats_and_licenses():
    decision = _decision()

    for pin in (
        "DITA Open Toolkit 4.4",
        "dita-ot-4.4.zip",
        "21.0.11+10",
        "OASIS DITA `1.3`",
        "bundled `html5`",
        "`org.bpm.docs.html5` version `0.9.0`",
        "Apache-2.0",
        "GPL-2.0 with Classpath Exception",
        "MPL-2.0",
    ):
        assert pin in decision

    assert "third-party DITA-OT plug-in" in decision
    assert "DITA 2.0 preview features are forbidden" in decision


def test_dita_toolchain_decision_defines_locked_offline_local_and_ci_builds():
    decision = _decision()

    for contract in (
        "`documentation/config/toolchain-lock.json`",
        "immutable release URLs",
        "archive SHA-256 values",
        "`make setup-docs-toolchain`",
        "`make docs-build`",
        "`make test-docs`",
        "After bootstrap, builds are offline",
        "byte-equivalent publishable files",
        "never installs Java",
        "observed OpenJDK 25 installation is not release-build evidence",
    ):
        assert contract in decision


def test_dita_toolchain_decision_covers_six_locales_and_accessibility():
    decision = _decision()

    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in decision
    for contract in (
        "may not silently fall back to English",
        "ICU4J `77.1`",
        "correct page `lang`",
        "keyboard-visible skip link",
        "authored alternative text and captions",
        "DITA transform alone is never treated as proof",
    ):
        assert contract in decision


def test_dita_toolchain_decision_defers_install_and_requires_controlled_updates():
    decision = _decision()

    assert "This task selects the toolchain; it does not install it." in decision
    assert "`BPM090-M3-03` must create the lock file" in decision
    assert "Updates are never automatic." in decision
    assert "Adding any third-party plug-in requires a separate decision" in decision
