from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.browser.harness import (
    BrowserPage,
    ChromiumHarness,
    configured_environment,
    wait_for_download,
)


class _SwitchTo:
    def __init__(self, driver: _FakeDriver):
        self.driver = driver

    def window(self, handle: str) -> None:
        self.driver.current_handle = handle


class _FakeDriver:
    def __init__(self, *, profile_dir: Path):
        self.profile_dir = profile_dir
        self.window_handles = ["root", "extra"]
        self.current_handle = "root"
        self.switch_to = _SwitchTo(self)
        self.current_url = "https://user:password@example.test/page?token=secret"
        self.title = "Failure title"
        self.commands: list[tuple[str, dict[str, Any]]] = []
        self.visited: list[str] = []
        self.cookies_deleted = 0
        self.window_size: tuple[int, int] | None = None

    def execute_script(self, script: str, *_args: Any) -> Any:
        if "innerText" in script:
            return "Semantic body"
        if "documentWidth" in script:
            return {"documentWidth": 800, "viewportWidth": 800}
        return None

    def execute_cdp_cmd(self, name: str, params: dict[str, Any]) -> None:
        self.commands.append((name, params))

    def close(self) -> None:
        self.window_handles.remove(self.current_handle)

    def get(self, url: str) -> None:
        self.visited.append(url)

    def delete_all_cookies(self) -> None:
        self.cookies_deleted += 1

    def set_window_size(self, width: int, height: int) -> None:
        self.window_size = (width, height)

    def save_screenshot(self, target: str) -> bool:
        Path(target).write_bytes(b"png")
        return True


def _running_harness(tmp_path: Path) -> tuple[ChromiumHarness, _FakeDriver]:
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    harness = ChromiumHarness(artifact_root=tmp_path / "artifacts")
    harness.profile_dir = profile_dir
    harness.browser_log_path = profile_dir / "chromium.log"
    harness.chromedriver_log_path = profile_dir / "chromedriver.log"
    harness.browser_log_path.write_text(
        "Authorization: bearer-value\nhttps://name:password@example.test/page\n",
        encoding="utf-8",
    )
    harness.chromedriver_log_path.write_text("token=private-value\n", encoding="utf-8")
    driver = _FakeDriver(profile_dir=profile_dir)
    harness.driver = driver
    return harness, driver


def test_page_object_exposes_semantic_body_and_fit_assertion(tmp_path: Path) -> None:
    _harness, driver = _running_harness(tmp_path)
    page = BrowserPage(driver)

    assert page.body_text() == "Semantic body"
    page.assert_document_fits()


def test_test_lifecycle_isolates_tabs_downloads_cookies_cache_and_emulation(
    tmp_path: Path,
) -> None:
    harness, driver = _running_harness(tmp_path)

    paths = harness.begin_test("tests/browser/test_page.py::test_download[param]")
    assert paths.downloads.is_dir()
    assert driver.window_handles == ["root"]
    assert driver.current_handle == "root"
    assert driver.visited[-1] == "about:blank"
    assert driver.cookies_deleted == 1
    assert (
        "Storage.clearDataForOrigin",
        {"origin": "https://example.test", "storageTypes": "all"},
    ) in driver.commands
    assert (
        "Browser.setDownloadBehavior",
        {
            "behavior": "allow",
            "downloadPath": str(paths.downloads),
        },
    ) in driver.commands

    (paths.downloads / "result.json").write_text("{}", encoding="utf-8")
    harness.end_test()
    assert not paths.root.exists()
    assert harness.test_paths is None


def test_failure_artifacts_strip_credentials_query_and_sensitive_logs(tmp_path: Path) -> None:
    harness, _driver = _running_harness(tmp_path)

    destination = harness.capture_failure("tests/browser/test_page.py::test_failure[token]")

    assert (destination / "failure.png").read_bytes() == b"png"
    context = json.loads((destination / "context.json").read_text(encoding="utf-8"))
    assert context["url"] == "https://example.test/page"
    combined_logs = (destination / "chromium.log").read_text(encoding="utf-8") + (
        destination / "chromedriver.log"
    ).read_text(encoding="utf-8")
    assert "bearer-value" not in combined_logs
    assert "password" not in combined_logs
    assert "private-value" not in combined_logs
    assert "<redacted>" in combined_logs


def test_wait_for_download_requires_exact_complete_stable_file(tmp_path: Path) -> None:
    expected = tmp_path / "policies.json"
    expected.write_text('{"policies": {}}', encoding="utf-8")

    assert wait_for_download(tmp_path, "policies.json", timeout=0.2, stable_for=0) == expected

    (tmp_path / "pending.crdownload").write_bytes(b"partial")
    with pytest.raises(AssertionError, match="did not complete"):
        wait_for_download(tmp_path, "policies.json", timeout=0.05, stable_for=0)


def test_configured_environment_restores_present_and_absent_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BPM_BROWSER_EXISTING", "before")
    monkeypatch.delenv("BPM_BROWSER_NEW", raising=False)

    with configured_environment(
        {"BPM_BROWSER_EXISTING": "during", "BPM_BROWSER_NEW": Path("site")}
    ):
        assert os.environ["BPM_BROWSER_EXISTING"] == "during"
        assert os.environ["BPM_BROWSER_NEW"] == "site"

    assert os.environ["BPM_BROWSER_EXISTING"] == "before"
    assert "BPM_BROWSER_NEW" not in os.environ
