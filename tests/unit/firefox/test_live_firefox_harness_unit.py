from __future__ import annotations

import errno
from pathlib import Path

import pytest

from tests.live.firefox.helpers import (
    assert_no_policy_errors,
    clone_firefox_installation,
    resolve_binary_path,
    write_policies_json_bytes,
)


class _PolicyErrorsDriver:
    page_source = ""

    def __init__(self, *, errors_hidden: bool, body_text: str = "") -> None:
        self.errors_hidden = errors_hidden
        self._body_text = body_text
        self.urls: list[str] = []

    def get(self, url: str) -> None:
        self.urls.append(url)

    def execute_script(self, _script: str) -> bool:
        return self.errors_hidden

    def find_element(self, _by: str, _value: str):
        return type("Body", (), {"text": self._body_text})()


def test_resolve_binary_path_prefers_env_override(tmp_path: Path):
    env_binary = tmp_path / "custom-firefox"
    env_binary.write_text("", encoding="utf-8")

    fallback_binary = tmp_path / "fallback-firefox"
    fallback_binary.write_text("", encoding="utf-8")

    resolved = resolve_binary_path(str(env_binary), [fallback_binary])

    assert resolved == env_binary.resolve()


def test_policy_error_helper_accepts_explicit_hidden_errors_category() -> None:
    driver = _PolicyErrorsDriver(errors_hidden=True, body_text="Active Errors Policy Errors")

    assert_no_policy_errors(driver, ["BlockAboutConfig"])

    assert driver.urls == ["about:policies#errors"]


def test_policy_error_helper_keeps_visible_error_category_failing() -> None:
    driver = _PolicyErrorsDriver(errors_hidden=False, body_text="Policy Errors malformed policy")
    driver.page_source = "BlockAboutConfig"

    with pytest.raises(AssertionError, match="Firefox reported policy errors"):
        assert_no_policy_errors(driver, ["BlockAboutConfig"])


def test_resolve_binary_path_falls_back_to_project_candidate(tmp_path: Path):
    fallback_binary = tmp_path / "fallback-firefox"
    fallback_binary.write_text("", encoding="utf-8")

    resolved = resolve_binary_path(None, [fallback_binary])

    assert resolved == fallback_binary.resolve()


def test_resolve_binary_path_returns_none_when_nothing_exists(tmp_path: Path):
    missing = tmp_path / "missing-firefox"

    assert resolve_binary_path(None, [missing]) is None


def test_write_policies_json_bytes_preserves_exported_file_exactly(tmp_path: Path):
    exported = b'{\n  "policies": {"DisableTelemetry": true}\n}\n'

    policy_path = write_policies_json_bytes(tmp_path / "firefox", exported)

    assert policy_path == tmp_path / "firefox" / "distribution" / "policies.json"
    assert policy_path.read_bytes() == exported


def test_clone_firefox_installation_keeps_policy_writes_out_of_source_tree(tmp_path: Path):
    source = tmp_path / "immutable-firefox"
    source.mkdir()
    (source / "firefox").write_text("binary", encoding="utf-8")
    source.chmod(0o555)
    (source / "firefox").chmod(0o555)

    clone = clone_firefox_installation(source, tmp_path / "test-run-firefox")
    policy_path = write_policies_json_bytes(clone, b'{"policies":{"DisableTelemetry":true}}\n')

    assert policy_path.is_file()
    assert not (source / "distribution" / "policies.json").exists()
    assert (source / "firefox").read_text(encoding="utf-8") == "binary"


def test_clone_firefox_installation_falls_back_to_copy_across_filesystems(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = tmp_path / "immutable-firefox"
    source.mkdir()
    (source / "firefox").write_text("binary", encoding="utf-8")

    def cross_device_link(source_name: str, destination_name: str) -> str:
        raise OSError(errno.EXDEV, "Invalid cross-device link", source_name, destination_name)

    monkeypatch.setattr("tests.live.firefox.helpers.os.link", cross_device_link)

    clone = clone_firefox_installation(source, tmp_path / "copied-firefox")

    assert (clone / "firefox").read_text(encoding="utf-8") == "binary"
    assert (clone / "firefox").stat().st_ino != (source / "firefox").stat().st_ino


def test_amo_canary_uses_one_browser_session_and_classifies_external_install_failures():
    source = (
        Path(__file__).resolve().parents[2] / "live/firefox/test_extension_settings_amo.py"
    ).read_text(encoding="utf-8")

    assert source.count("firefox_run(") == 1
    assert "AMO_CANARY_EXTERNAL_FAILURE[provider-or-network]" in source
    assert 'assert_policy_active(driver, "ExtensionSettings")' in source
    assert 'assert_no_policy_errors(driver, ["ExtensionSettings"])' in source
    assert "wait_for_addon_install" in source
    assert 'assert addon["sourceURI"] == UBLOCK_INSTALL_URL' in source


def test_live_harness_has_no_unsigned_local_xpi_build_or_copy_path():
    live_root = Path(__file__).resolve().parents[2] / "live/firefox"
    harness = (live_root / "conftest.py").read_text(encoding="utf-8")
    helpers = (live_root / "helpers.py").read_text(encoding="utf-8")

    for forbidden in (
        "build_test_extension_xpi",
        "test_extension_xpi",
        "test_extension_source_dir",
        "test-extension.xpi",
    ):
        assert forbidden not in harness
    assert "build_test_extension_xpi" not in helpers


def test_live_harness_bounds_external_addon_shutdown_cleanup():
    harness = (Path(__file__).resolve().parents[2] / "live/firefox/conftest.py").read_text(
        encoding="utf-8"
    )

    assert "quit_thread.join(timeout=20.0)" in harness
    assert "service_process.terminate()" in harness
