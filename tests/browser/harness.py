"""Shared deterministic Chromium and application-server browser-test harness."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

import pytest
import requests

from tests.support import pick_free_port, run_test_app_server

DEFAULT_WIDTH = 1366
DEFAULT_HEIGHT = 1200
_ACTIVE_HARNESS: ChromiumHarness | None = None
_ACTIVE_PRODUCT_SERVER: str | None = None
_BROWSER_CALL_FAILED = pytest.StashKey[bool]()
_CREDENTIAL_RE = re.compile(r"(?P<scheme>https?://)[^/@\s]+@", re.IGNORECASE)
_SECRET_RE = re.compile(r"(?i)(authorization|cookie|password|secret|token)(\s*[:=]\s*)([^\s,;]+)")


def _artifact_root() -> Path:
    configured = os.environ.get("BPM_BROWSER_ARTIFACT_DIR", "artifacts/browser-failures")
    return Path(configured).resolve()


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    return (normalized or "browser-test")[-180:]


def _safe_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "<invalid-url>"
    hostname = parsed.hostname or ""
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"
    return urlunsplit((parsed.scheme, hostname, parsed.path, "", ""))


def _safe_log_text(value: str, *, limit: int = 64 * 1024) -> str:
    tail = value[-limit:]
    tail = _CREDENTIAL_RE.sub(r"\g<scheme><redacted>@", tail)
    return _SECRET_RE.sub(r"\1\2<redacted>", tail)


@dataclass(frozen=True, slots=True)
class BrowserTestPaths:
    root: Path
    downloads: Path


class BrowserPage:
    """Small semantic page object shared by product and documentation contours."""

    def __init__(self, driver: Any):
        self.driver = driver

    def body_text(self) -> str:
        return self.driver.execute_script("return document.body ? document.body.innerText : '';")

    def assert_document_fits(self) -> None:
        metrics = self.driver.execute_script("""
            return {
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: window.innerWidth,
            };
            """)
        assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics

    def click(self, element: Any) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element
        )
        try:
            element.click()
        except Exception as exc:
            if exc.__class__.__name__ != "ElementClickInterceptedException":
                raise
            self.driver.execute_script("arguments[0].click();", element)

    def click_and_switch_to_new_tab(self, wait: Any, element: Any) -> str:
        previous_handles = set(self.driver.window_handles)
        self.click(element)
        wait.until(
            lambda current_driver: len(set(current_driver.window_handles) - previous_handles) == 1
        )
        new_handle = (set(self.driver.window_handles) - previous_handles).pop()
        self.driver.switch_to.window(new_handle)
        return new_handle


class ChromiumHarness:
    """Own one Chromium process and isolate its mutable state for each pytest item."""

    def __init__(self, *, artifact_root: Path):
        self.artifact_root = artifact_root
        self.profile_dir: Path | None = None
        self.browser_log_path: Path | None = None
        self.chromedriver_log_path: Path | None = None
        self.browser_log: Any | None = None
        self.browser_process: subprocess.Popen[str] | None = None
        self.driver: Any | None = None
        self.test_paths: BrowserTestPaths | None = None

    def start(self) -> Any:
        webdriver = pytest.importorskip("selenium.webdriver")
        exceptions = pytest.importorskip("selenium.common.exceptions")
        chrome_service = pytest.importorskip("selenium.webdriver.chrome.service")

        chromium_binary = Path(os.environ.get("BPM_CHROMIUM_BINARY", "/snap/bin/chromium"))
        chromedriver_binary = Path(
            os.environ.get("BPM_CHROMEDRIVER_BINARY", "/snap/bin/chromium.chromedriver")
        )
        snap_binary = Path("/usr/bin/snap")
        for label, binary in (
            ("Chromium", chromium_binary),
            ("ChromeDriver", chromedriver_binary),
        ):
            if not binary.exists():
                pytest.skip(f"{label} binary is not available at {binary}")
        uses_snap = chromium_binary.resolve() == snap_binary.resolve()
        if uses_snap and not snap_binary.exists():
            pytest.skip(f"Snap launcher is not available at {snap_binary}")

        debug_port = pick_free_port()
        self.profile_dir = Path(tempfile.mkdtemp(prefix=f"bpm-browser-module-{debug_port}-"))
        self.browser_log_path = self.profile_dir / "chromium.log"
        self.chromedriver_log_path = self.profile_dir / "chromedriver.log"
        self.browser_log = self.browser_log_path.open("w", encoding="utf-8")
        command = [str(chromium_binary)]
        if uses_snap:
            command = [str(snap_binary), "run", "chromium"]
        command.extend(
            [
                "--headless=new",
                "--remote-debugging-address=127.0.0.1",
                f"--remote-debugging-port={debug_port}",
                "--no-first-run",
                "--no-default-browser-check",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-popup-blocking",
                "--disable-background-networking",
                "--disable-component-update",
                "--disable-extensions",
                "--renderer-process-limit=2",
                "--js-flags=--max-old-space-size=384",
                "--lang=en-US",
                "--force-device-scale-factor=1",
                f"--user-data-dir={self.profile_dir}",
                f"--window-size={DEFAULT_WIDTH},{DEFAULT_HEIGHT}",
                "about:blank",
            ]
        )
        self.browser_process = subprocess.Popen(
            command,
            stdout=self.browser_log,
            stderr=subprocess.STDOUT,
            text=True,
        )

        debugger_url = f"http://127.0.0.1:{debug_port}/json/version"
        deadline = time.monotonic() + 20
        last_error = ""
        debugger_ready = False
        while time.monotonic() < deadline:
            if self.browser_process.poll() is not None:
                self.browser_log.flush()
                last_error = self.browser_log_path.read_text(encoding="utf-8", errors="ignore")
                break
            try:
                response = requests.get(debugger_url, timeout=2)
                if response.status_code == 200:
                    debugger_ready = True
                    break
                last_error = f"debugger probe returned {response.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)
            time.sleep(0.25)
        if not debugger_ready:
            self.close()
            pytest.skip(
                f"Chromium debugger did not become ready: {_safe_log_text(last_error, limit=4096)}"
            )

        options = webdriver.ChromeOptions()
        options.debugger_address = f"127.0.0.1:{debug_port}"
        options.page_load_strategy = "eager"
        service = chrome_service.Service(
            executable_path=str(chromedriver_binary),
            log_output=str(self.chromedriver_log_path),
        )
        try:
            driver = webdriver.Chrome(service=service, options=options)
        except exceptions.WebDriverException as exc:
            self.close()
            pytest.skip(f"Chromium UI smoke could not start in this environment: {exc}")
        self.driver = driver
        driver.set_window_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        driver.set_page_load_timeout(60)
        return driver

    def begin_test(self, nodeid: str) -> BrowserTestPaths:
        if self.driver is None or self.profile_dir is None:
            raise RuntimeError("Chromium harness is not running")
        test_root = self.profile_dir / "tests" / _safe_name(nodeid)
        if test_root.exists():
            shutil.rmtree(test_root)
        downloads = test_root / "downloads"
        downloads.mkdir(parents=True)
        self.test_paths = BrowserTestPaths(root=test_root, downloads=downloads)
        params = {"behavior": "allow", "downloadPath": str(downloads)}
        try:
            self.driver.execute_cdp_cmd("Browser.setDownloadBehavior", params)
        except Exception:
            self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        self.reset_for_use()
        return self.test_paths

    def reset_for_use(self) -> Any:
        if self.driver is None:
            raise RuntimeError("Chromium harness is not running")
        handles = list(self.driver.window_handles)
        if handles:
            keeper = handles[0]
            for handle in handles:
                self.driver.switch_to.window(handle)
                current_url = str(getattr(self.driver, "current_url", ""))
                parsed = urlsplit(current_url)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    host = parsed.hostname
                    if parsed.port:
                        host = f"{host}:{parsed.port}"
                    self.driver.execute_cdp_cmd(
                        "Storage.clearDataForOrigin",
                        {
                            "origin": urlunsplit((parsed.scheme, host, "", "", "")),
                            "storageTypes": "all",
                        },
                    )
                if handle != keeper:
                    self.driver.close()
            self.driver.switch_to.window(keeper)
        self.driver.get("about:blank")
        self.driver.delete_all_cookies()
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        self.driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": []})
        self.driver.set_window_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        return self.driver

    def capture_failure(self, nodeid: str) -> Path:
        if self.driver is None:
            raise RuntimeError("Chromium harness is not running")
        destination = self.artifact_root / _safe_name(nodeid)
        destination.mkdir(parents=True, exist_ok=True)
        screenshot_error = ""
        try:
            self.driver.save_screenshot(str(destination / "failure.png"))
        except Exception as exc:
            screenshot_error = f"{exc.__class__.__name__}: {exc}"
        metadata = {
            "nodeid": nodeid,
            "url": _safe_url(str(getattr(self.driver, "current_url", ""))),
            "title": str(getattr(self.driver, "title", ""))[:500],
            "screenshot_error": screenshot_error,
        }
        (destination / "context.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if self.browser_log is not None:
            self.browser_log.flush()
        for source, name in (
            (self.browser_log_path, "chromium.log"),
            (self.chromedriver_log_path, "chromedriver.log"),
        ):
            if source is None or not source.exists():
                continue
            (destination / name).write_text(
                _safe_log_text(source.read_text(encoding="utf-8", errors="ignore")),
                encoding="utf-8",
            )
        return destination

    def end_test(self) -> None:
        paths = self.test_paths
        try:
            if self.driver is not None:
                try:
                    self.reset_for_use()
                except Exception:
                    # A crashed/externally interrupted driver must not prevent profile cleanup.
                    pass
        finally:
            if paths is not None:
                shutil.rmtree(paths.root, ignore_errors=True)
            self.test_paths = None

    def close(self) -> None:
        driver, self.driver = self.driver, None
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
        process, self.browser_process = self.browser_process, None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if self.browser_log is not None:
            self.browser_log.close()
            self.browser_log = None
        if self.profile_dir is not None:
            shutil.rmtree(self.profile_dir, ignore_errors=True)
            self.profile_dir = None


@pytest.fixture(scope="module")
def chromium_harness() -> Iterator[ChromiumHarness]:
    global _ACTIVE_HARNESS
    harness = ChromiumHarness(artifact_root=_artifact_root())
    harness.start()
    previous = _ACTIVE_HARNESS
    _ACTIVE_HARNESS = harness
    try:
        yield harness
    finally:
        _ACTIVE_HARNESS = previous
        harness.close()


@pytest.fixture
def browser_test_context(
    request: pytest.FixtureRequest, chromium_harness: ChromiumHarness
) -> Iterator[ChromiumHarness]:
    chromium_harness.begin_test(request.node.nodeid)
    try:
        yield chromium_harness
    finally:
        if request.node.stash.get(_BROWSER_CALL_FAILED, False):
            artifact = chromium_harness.capture_failure(request.node.nodeid)
            print(f"Browser failure artifacts: {artifact}", flush=True)
        chromium_harness.end_test()


@pytest.fixture
def browser_product_server() -> Iterator[str]:
    global _ACTIVE_PRODUCT_SERVER
    with run_test_app_server() as base_url:
        previous = _ACTIVE_PRODUCT_SERVER
        _ACTIVE_PRODUCT_SERVER = base_url
        try:
            yield base_url
        finally:
            _ACTIVE_PRODUCT_SERVER = previous


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Iterator[None]:
    outcome = cast(Any, (yield))
    report = outcome.get_result()
    if report.when == "call":
        item.stash[_BROWSER_CALL_FAILED] = report.failed


@contextmanager
def scoped_test_app_server() -> Iterator[str]:
    if _ACTIVE_PRODUCT_SERVER is None:
        raise RuntimeError("browser_product_server fixture is not active")
    yield _ACTIVE_PRODUCT_SERVER


def build_chromium_driver() -> Any:
    if _ACTIVE_HARNESS is None:
        raise RuntimeError("chromium_harness fixture is not active")
    return _ACTIVE_HARNESS.reset_for_use()


def close_chromium_driver(_driver: Any) -> None:
    """Compatibility boundary; the module fixture owns the real process lifetime."""


def body_text(driver: Any) -> str:
    return BrowserPage(driver).body_text()


def assert_document_fits(driver: Any) -> None:
    BrowserPage(driver).assert_document_fits()


def click_element(driver: Any, element: Any) -> None:
    BrowserPage(driver).click(element)


def click_and_switch_to_new_tab(driver: Any, wait: Any, element: Any) -> str:
    return BrowserPage(driver).click_and_switch_to_new_tab(wait, element)


def wait_for_download(
    downloads: Path, filename: str, *, timeout: float = 20.0, stable_for: float = 0.25
) -> Path:
    """Return only a complete, size-stable download with the exact expected name."""

    expected = downloads / filename
    deadline = time.monotonic() + timeout
    last_size: int | None = None
    stable_since = 0.0
    while time.monotonic() < deadline:
        partials = list(downloads.glob("*.crdownload"))
        if expected.is_file() and not partials:
            size = expected.stat().st_size
            if size == last_size:
                if time.monotonic() - stable_since >= stable_for:
                    return expected
            else:
                last_size = size
                stable_since = time.monotonic()
        time.sleep(0.05)
    present = sorted(path.name for path in downloads.iterdir())
    raise AssertionError(
        f"download {filename!r} did not complete within {timeout:.1f}s; present={present}"
    )


@contextmanager
def configured_environment(environment: Mapping[str, str | Path]) -> Iterator[None]:
    """Temporarily configure a scenario server without leaking process environment."""

    previous = {name: os.environ.get(name) for name in environment}
    os.environ.update({name: str(value) for name, value in environment.items()})
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
