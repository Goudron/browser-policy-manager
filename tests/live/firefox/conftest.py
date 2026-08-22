from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from app.services.firefox_policy_export import render_firefox_policies_document
from tests.live.firefox.helpers import (
    clear_policies_json,
    clone_firefox_installation,
    resolve_binary_path,
    serve_http_proxy,
    serve_https_site,
    serve_static_site,
    write_policies_json,
    write_policies_json_bytes,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_live_progress_total = 0
_live_progress_completed = 0


def _live_failure_root() -> Path | None:
    configured = os.getenv("BPM_FIREFOX_LIVE_ARTIFACT_DIR")
    return Path(configured).resolve() if configured else None


def _scenario_artifact_dir(nodeid: str) -> Path | None:
    root = _live_failure_root()
    if root is None:
        return None
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", nodeid).strip("-")
    return root / slug


def _record_live_evidence(request: pytest.FixtureRequest, *, policy_path: Path) -> None:
    """Record only the policy file and driver log needed for a failed scenario."""

    request.node.user_properties.append(("bpm_firefox_policy_path", str(policy_path)))


def pytest_collection_finish(session: pytest.Session) -> None:
    """Expose deterministic per-scenario progress for the pinned browser runner."""

    global _live_progress_total, _live_progress_completed
    _live_progress_completed = 0
    _live_progress_total = sum(
        1 for item in session.items if item.get_closest_marker("firefox_live") is not None
    )
    channel = os.getenv("BPM_FIREFOX_CHANNEL", "release")
    print(
        f"Firefox live [{channel}] scenarios 0/{_live_progress_total}: collection complete",
        flush=True,
    )


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Print a truthful completed/total boundary after each live test call."""

    global _live_progress_completed
    if report.when != "call":
        return
    _live_progress_completed += 1
    if report.passed:
        outcome = "passed"
    elif report.failed:
        outcome = "failed"
    else:
        outcome = "skipped"
    channel = os.getenv("BPM_FIREFOX_CHANNEL", "release")
    print(
        f"Firefox live [{channel}] scenarios {_live_progress_completed}/{_live_progress_total}: "
        f"{outcome} {report.nodeid}",
        flush=True,
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    """Persist safe failure evidence without retaining profile directories."""

    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        item._bpm_live_scenario_failed = True  # type: ignore[attr-defined]
    if report.when == "teardown" and not getattr(item, "_bpm_live_scenario_failed", False):
        destination = _scenario_artifact_dir(item.nodeid)
        if destination is not None:
            shutil.rmtree(destination, ignore_errors=True)
        return
    if report.when != "call" or not report.failed:
        return
    destination = _scenario_artifact_dir(item.nodeid)
    if destination is None:
        return
    destination.mkdir(parents=True, exist_ok=True)
    copied_policy = False
    copied_log = False
    for key, value in item.user_properties:
        source = Path(str(value))
        if key == "bpm_firefox_policy_path" and source.is_file():
            shutil.copy2(source, destination / "policies.json")
            copied_policy = True
        if key == "bpm_geckodriver_log_path" and source.is_file():
            shutil.copy2(source, destination / "geckodriver.log")
            copied_log = True
    (destination / "scenario.json").write_text(
        json.dumps(
            {
                "nodeid": item.nodeid,
                "channel": os.getenv("BPM_FIREFOX_CHANNEL", "release"),
                "policy_file_retained": copied_policy,
                "geckodriver_log_retained": copied_log,
                "profile_directory_retained": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _require_binary_path(name: str, candidate_paths: list[Path]) -> Path:
    resolved = resolve_binary_path(os.getenv(name), candidate_paths)
    if resolved is None:
        pretty_candidates = ", ".join(str(path.relative_to(REPO_ROOT)) for path in candidate_paths)
        pytest.skip(
            f"{name} is not configured and no project-local binary was found "
            f"under {pretty_candidates}"
        )
    return resolved


def _provisioned_candidates(binary_name: str, channel: str) -> list[Path]:
    """Return only versioned, manifest-provisioned binary candidates.

    The legacy flat sandbox is deliberately not a fallback: it has no
    immutable provenance record and therefore cannot establish live-test
    supply-chain evidence.
    """

    root = Path(os.getenv("BPM_FIREFOX_PROVISION_ROOT", REPO_ROOT / ".bpm-test-browsers"))
    return sorted(
        root.glob(f"installs/*/{channel}-*/{binary_name}"),
        key=lambda path: path.as_posix(),
        reverse=True,
    )


@pytest.fixture(scope="session")
def firefox_binary() -> Path:
    channel = os.getenv("BPM_FIREFOX_CHANNEL", "release")
    return _require_binary_path(
        "BPM_FIREFOX_BIN",
        _provisioned_candidates("firefox/firefox", channel),
    )


@pytest.fixture(scope="session")
def geckodriver_binary() -> Path:
    channel = os.getenv("BPM_FIREFOX_CHANNEL", "release")
    return _require_binary_path(
        "BPM_GECKODRIVER_BIN",
        _provisioned_candidates("geckodriver/geckodriver", channel),
    )


@pytest.fixture(scope="session")
def firefox_install_root(firefox_binary: Path) -> Path:
    return firefox_binary.parent


@pytest.fixture
def staged_firefox_dir(tmp_path: Path, firefox_install_root: Path):
    firefox_dir = clone_firefox_installation(
        firefox_install_root, tmp_path / "firefox-installation"
    )
    clear_policies_json(firefox_dir)
    yield firefox_dir
    clear_policies_json(firefox_dir)


@pytest.fixture
def firefox_driver_factory(request: pytest.FixtureRequest, geckodriver_binary: Path):
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
        options.add_argument("-profile")
        options.add_argument(str(profile_dir))
        if headless:
            options.add_argument("-headless")

        scenario_dir = _scenario_artifact_dir(request.node.nodeid)
        service_options: dict[str, Any] = {
            "executable_path": str(geckodriver_binary),
            "service_args": ["--allow-system-access"],
        }
        if scenario_dir is not None:
            scenario_dir.mkdir(parents=True, exist_ok=True)
            geckodriver_log = scenario_dir / "geckodriver-live.log"
            service_options["log_output"] = str(geckodriver_log)
            request.node.user_properties.append(("bpm_geckodriver_log_path", str(geckodriver_log)))
        service = firefox_service.Service(**service_options)
        driver = webdriver.Firefox(service=service, options=options)
        drivers.append(driver)
        return driver

    yield factory

    for driver in reversed(drivers):
        # Older ESR builds can leave a WebExtension shutdown pending after an
        # external AMO install. Do not let that external lifecycle hold the
        # standalone canary (or its CI artifact upload) indefinitely.
        quit_thread = Thread(target=driver.quit, daemon=True)
        quit_thread.start()
        quit_thread.join(timeout=20.0)
        if not quit_thread.is_alive():
            continue

        service_process = getattr(getattr(driver, "service", None), "process", None)
        if service_process is not None and service_process.poll() is None:
            service_process.terminate()
            try:
                service_process.wait(timeout=5.0)
            except Exception:  # pragma: no cover - emergency live-test cleanup
                service_process.kill()


@pytest.fixture
def firefox_run(
    request: pytest.FixtureRequest, tmp_path: Path, staged_firefox_dir: Path, firefox_driver_factory
):
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
        policy_path = write_policies_json(staged_firefox_dir, document)
        _record_live_evidence(request, policy_path=policy_path)

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
def firefox_run_exported_document(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    staged_firefox_dir: Path,
    firefox_driver_factory,
):
    """Launch Firefox with the exact bytes returned by BPM policy export.

    This deliberately does not invoke ``render_firefox_policies_document``:
    callers must supply a full exported document and can assert byte equality
    between that HTTP response and the policy file Firefox consumes.
    """

    run_index = 0

    def run(
        document_bytes: bytes,
        *,
        headless: bool = True,
        accept_insecure_certs: bool = True,
    ):
        nonlocal run_index
        document = json.loads(document_bytes.decode("utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("policies"), dict):
            raise ValueError("Firefox E2E requires a full exported policies.json document")

        profile_dir = tmp_path / f"profile-{run_index}"
        run_index += 1
        profile_dir.mkdir()
        policy_path = write_policies_json_bytes(staged_firefox_dir, document_bytes)
        _record_live_evidence(request, policy_path=policy_path)

        binary_name = "firefox.exe" if os.name == "nt" else "firefox"
        firefox_binary = staged_firefox_dir / binary_name
        driver = firefox_driver_factory(
            firefox_binary=firefox_binary,
            profile_dir=profile_dir,
            headless=headless,
            accept_insecure_certs=accept_insecure_certs,
        )
        return driver, document, policy_path, staged_firefox_dir, profile_dir

    return run


@pytest.fixture
def static_site(tmp_path: Path):
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
