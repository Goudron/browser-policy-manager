from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from app.services.firefox_policy_export import render_firefox_policies_document
from tests.live_firefox.helpers import (
    build_test_extension_xpi,
    clear_policies_json,
    resolve_binary_path,
    serve_http_proxy,
    serve_https_site,
    serve_static_site,
    write_policies_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"


def _require_binary_path(name: str, candidate_paths: list[Path]) -> Path:
    resolved = resolve_binary_path(os.getenv(name), candidate_paths)
    if resolved is None:
        pretty_candidates = ", ".join(str(path.relative_to(REPO_ROOT)) for path in candidate_paths)
        pytest.skip(
            f"{name} is not configured and no project-local binary was found "
            f"under {pretty_candidates}"
        )
    return resolved


@pytest.fixture(scope="session")
def firefox_binary() -> Path:
    return _require_binary_path(
        "BPM_FIREFOX_BIN",
        [
            REPO_ROOT / ".bpm-test-browsers" / "firefox" / "firefox" / "firefox",
            REPO_ROOT / ".bpm-test-browsers" / "firefox" / "firefox.exe",
            REPO_ROOT / ".bpm-test-browsers" / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
        ],
    )


@pytest.fixture(scope="session")
def geckodriver_binary() -> Path:
    return _require_binary_path(
        "BPM_GECKODRIVER_BIN",
        [
            REPO_ROOT / ".bpm-test-browsers" / "geckodriver" / "geckodriver",
            REPO_ROOT / ".bpm-test-browsers" / "geckodriver" / "geckodriver.exe",
        ],
    )


@pytest.fixture(scope="session")
def firefox_install_root(firefox_binary: Path) -> Path:
    return firefox_binary.parent


@pytest.fixture
def staged_firefox_dir(firefox_install_root: Path):
    clear_policies_json(firefox_install_root)
    yield firefox_install_root
    clear_policies_json(firefox_install_root)


@pytest.fixture
def firefox_driver_factory(geckodriver_binary: Path):
    webdriver = pytest.importorskip("selenium.webdriver")
    firefox_options = pytest.importorskip("selenium.webdriver.firefox.options")
    firefox_service = pytest.importorskip("selenium.webdriver.firefox.service")

    drivers: list[Any] = []

    def factory(
        *,
        firefox_binary: Path,
        profile_dir: Path,
        headless: bool = True,
        accept_insecure_certs: bool = True,
    ):
        options = firefox_options.Options()
        options.binary_location = str(firefox_binary)
        options.accept_insecure_certs = accept_insecure_certs
        options.add_argument("-no-remote")
        options.add_argument("-remote-allow-system-access")
        options.add_argument("-profile")
        options.add_argument(str(profile_dir))
        if headless:
            options.add_argument("-headless")

        service = firefox_service.Service(executable_path=str(geckodriver_binary))
        driver = webdriver.Firefox(service=service, options=options)
        drivers.append(driver)
        return driver

    yield factory

    for driver in reversed(drivers):
        driver.quit()


@pytest.fixture
def firefox_run(tmp_path: Path, staged_firefox_dir: Path, firefox_driver_factory):
    run_index = 0

    def run(
        flags: dict[str, object],
        *,
        headless: bool = True,
        accept_insecure_certs: bool = True,
    ):
        nonlocal run_index
        profile_dir = tmp_path / f"profile-{run_index}"
        run_index += 1
        profile_dir.mkdir()

        document = render_firefox_policies_document(flags)
        write_policies_json(staged_firefox_dir, document)

        binary_name = "firefox.exe" if os.name == "nt" else "firefox"
        firefox_binary = staged_firefox_dir / binary_name
        driver = firefox_driver_factory(
            firefox_binary=firefox_binary,
            profile_dir=profile_dir,
            headless=headless,
            accept_insecure_certs=accept_insecure_certs,
        )
        return driver, document, staged_firefox_dir, profile_dir

    return run


@pytest.fixture
def test_extension_source_dir() -> Path:
    return LIVE_FIXTURES_ROOT / "extensions" / "test-extension"


@pytest.fixture
def test_extension_id() -> str:
    return "bpm-live-test@example.org"


@pytest.fixture
def test_extension_xpi(tmp_path: Path, test_extension_source_dir: Path) -> Path:
    return build_test_extension_xpi(
        test_extension_source_dir,
        tmp_path / "built-extensions" / "test-extension.xpi",
    )


@pytest.fixture
def static_site(tmp_path: Path, test_extension_xpi: Path):
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "index.html").write_text(
        "<html><body><h1>Firefox live test site</h1></body></html>",
        encoding="utf-8",
    )
    (site_dir / "blocked.html").write_text(
        "<html><body><h1>SENTINEL_BLOCKED_TARGET</h1></body></html>",
        encoding="utf-8",
    )
    (site_dir / "allowed.html").write_text(
        "<html><body><h1>SENTINEL_ALLOWED_TARGET</h1></body></html>",
        encoding="utf-8",
    )
    (site_dir / "homepage.html").write_text(
        "<html><body><h1>SENTINEL_HOMEPAGE_TARGET</h1></body></html>",
        encoding="utf-8",
    )
    (site_dir / "first-run.html").write_text(
        "<html><body><h1>SENTINEL_FIRST_RUN_TARGET</h1></body></html>",
        encoding="utf-8",
    )
    shutil.copy2(test_extension_xpi, site_dir / "test-extension.xpi")

    with serve_static_site(site_dir) as site:
        yield site


@pytest.fixture
def http_proxy_site():
    with serve_http_proxy() as site:
        yield site


@pytest.fixture
def https_cert_site(tmp_path: Path):
    openssl_binary = shutil.which("openssl")
    if not openssl_binary:
        pytest.skip("openssl is not available")

    site_dir = tmp_path / "https-site"
    site_dir.mkdir()
    (site_dir / "index.html").write_text(
        "<html><body><h1>HTTPS_CERT_OK</h1></body></html>",
        encoding="utf-8",
    )

    with serve_https_site(site_dir, openssl_binary) as site:
        yield site
