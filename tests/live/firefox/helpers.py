from __future__ import annotations

import contextlib
import errno
import json
import os
import shutil
import ssl
import subprocess
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.parse import urljoin


def resolve_binary_path(
    env_var_value: str | None,
    candidate_paths: list[Path],
) -> Path | None:
    """Resolve an executable path from env override or project-local defaults."""

    if env_var_value:
        env_path = Path(env_var_value).expanduser()
        if env_path.is_file():
            return env_path.resolve()
        return None

    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate.resolve()
    return None


def write_policies_json(firefox_dir: Path, document: dict[str, Any]) -> Path:
    """Write the enterprise policy file next to the tested Firefox binary."""
    distribution_dir = firefox_dir / "distribution"
    distribution_dir.mkdir(parents=True, exist_ok=True)
    output_path = distribution_dir / "policies.json"
    output_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return output_path


def write_policies_json_bytes(firefox_dir: Path, document_bytes: bytes) -> Path:
    """Install an already-exported ``policies.json`` without changing its bytes.

    The persisted-profile E2E uses this path specifically to prove that Firefox
    receives the document returned by BPM's public export endpoint, rather than
    a second rendering of a convenient in-test fixture.
    """

    distribution_dir = firefox_dir / "distribution"
    distribution_dir.mkdir(parents=True, exist_ok=True)
    output_path = distribution_dir / "policies.json"
    output_path.write_bytes(document_bytes)
    return output_path


def clear_policies_json(firefox_dir: Path) -> None:
    """Remove the enterprise policy file from the project-local Firefox sandbox."""

    output_path = firefox_dir / "distribution" / "policies.json"
    with contextlib.suppress(FileNotFoundError):
        output_path.unlink()


def clone_firefox_installation(source_dir: Path, destination_dir: Path) -> Path:
    """Copy an immutable provisioned Firefox tree into one writable test root.

    Provisioning intentionally never exposes an install tree as a writable
    policy root.  Every live test receives this short-lived copy before it
    writes ``distribution/policies.json``.
    """

    # Copying a Firefox tree byte-for-byte for every case would retain hundreds
    # of megabytes in pytest's temporary directory.  Hard links keep immutable
    # executable assets deduplicated while each directory (and therefore each
    # policy root) remains independent.  We never chmod linked files: that
    # would alter the immutable source inode as well.
    def link_or_copy(source: str, destination: str) -> str:
        try:
            os.link(source, destination)
            return destination
        except OSError as error:
            if error.errno != errno.EXDEV:
                raise
            # pytest's default /tmp can be a different filesystem from the
            # immutable project cache.  Retain isolation over deduplication.
            return shutil.copy2(source, destination)

    shutil.copytree(source_dir, destination_dir, copy_function=link_or_copy)
    for path in destination_dir.rglob("*"):
        if path.is_dir():
            path.chmod(path.stat().st_mode | 0o200)
    destination_dir.chmod(destination_dir.stat().st_mode | 0o200)
    return destination_dir


def body_text(driver: Any) -> str:
    return driver.find_element("tag name", "body").text


def open_about_policies_active(driver: Any) -> None:
    driver.get("about:policies#active")


def open_about_policies_errors(driver: Any) -> None:
    driver.get("about:policies#errors")


def assert_policy_active(driver: Any, policy_name: str) -> None:
    open_about_policies_active(driver)
    assert policy_name in driver.page_source


def assert_no_policy_errors(driver: Any, policy_names: list[str] | None = None) -> None:
    """
    Best-effort check that Firefox did not report policy parsing/application errors.

    The DOM of about:policies is not guaranteed to stay fully stable across Firefox
    versions, so the assertion intentionally stays text-based and conservative.
    """

    open_about_policies_errors(driver)
    page = driver.page_source
    text = body_text(driver).lower()

    accepted_empty_states = (
        "no errors",
        "there are no errors",
        "errors have not been found",
    )
    if any(state in text for state in accepted_empty_states):
        return

    # Some Firefox builds keep the "Active" tab selected even when navigating
    # to the errors fragment. If the page still clearly shows active policies,
    # do not treat that as a real policy error.
    if "policy name policy value" in text:
        return

    if policy_names and all(name not in page for name in policy_names):
        return

    raise AssertionError(f"Firefox reported policy errors:\n{text}")


@contextlib.contextmanager
def firefox_chrome_context(driver: Any):
    """Temporarily switch Selenium into Firefox chrome context."""

    if not hasattr(driver, "set_context"):
        raise RuntimeError("Firefox chrome context is unavailable in this Selenium session")

    driver.set_context("chrome")
    try:
        yield
    finally:
        driver.set_context("content")


def get_string_pref(driver: Any, pref_name: str) -> str:
    """Read a runtime Firefox string preference from the live browser."""

    with firefox_chrome_context(driver):
        return driver.execute_script(
            """
            const prefName = arguments[0];
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            return servicesModule.Services.prefs.getStringPref(prefName, "");
            """,
            pref_name,
        )


def get_int_pref(driver: Any, pref_name: str) -> int:
    """Read a runtime Firefox integer preference from the live browser."""

    with firefox_chrome_context(driver):
        return driver.execute_script(
            """
            const prefName = arguments[0];
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            return servicesModule.Services.prefs.getIntPref(prefName, -1);
            """,
            pref_name,
        )


def get_bool_pref(driver: Any, pref_name: str) -> bool:
    """Read a runtime Firefox boolean preference from the live browser."""

    with firefox_chrome_context(driver):
        return driver.execute_script(
            """
            const prefName = arguments[0];
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            return servicesModule.Services.prefs.getBoolPref(prefName, false);
            """,
            pref_name,
        )


def is_pref_locked(driver: Any, pref_name: str) -> bool:
    """Return whether a runtime Firefox preference is locked."""

    with firefox_chrome_context(driver):
        return driver.execute_script(
            """
            const prefName = arguments[0];
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            return servicesModule.Services.prefs.prefIsLocked(prefName);
            """,
            pref_name,
        )


def is_policy_allowed(driver: Any, policy_name: str) -> bool | None:
    """Return whether Firefox runtime policy API allows the given capability."""

    with firefox_chrome_context(driver):
        return driver.execute_script(
            """
            const policyName = arguments[0];
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            const policyService = servicesModule.Services.policies;
            if (!policyService || typeof policyService.isAllowed !== "function") {
                return null;
            }
            return policyService.isAllowed(policyName);
            """,
            policy_name,
        )


def get_requested_locales(driver: Any) -> list[str]:
    """Read Firefox requested locales from the live browser locale service."""

    with firefox_chrome_context(driver):
        return driver.execute_script("""
            const servicesModule = typeof Services === "object"
                ? { Services }
                : ChromeUtils.importESModule("resource://gre/modules/Services.sys.mjs");
            return Array.from(servicesModule.Services.locale.requestedLocales || []);
            """)


def get_update_preferences_state(driver: Any) -> dict[str, bool | dict[str, Any] | str | None]:
    """Read the runtime update permission and any version-specific preferences controls."""

    driver.get("about:preferences#general")
    with firefox_chrome_context(driver):
        return driver.execute_script("""
            const doc = content.document;
            const describe = (id) => {
                const el = doc.getElementById(id);
                if (!el) {
                    return null;
                }
                return {
                    hidden: !!el.hidden,
                    disabled: "disabled" in el ? !!el.disabled : null,
                    text: (el.innerText || el.textContent || "").trim(),
                };
            };
            return {
                href: content.location?.href || null,
                appUpdateAllowed: Services.policies.isAllowed("appUpdate"),
                updateAllowDescription: describe("updateAllowDescription"),
                updateSettingsContainer: describe("updateSettingsContainer"),
                updateRadioGroup: describe("updateRadioGroup"),
            };
            """)


def get_installed_addons(driver: Any) -> list[dict[str, Any]]:
    """Read installed Firefox add-ons from the live browser runtime."""

    with firefox_chrome_context(driver):
        result = driver.execute_async_script("""
            const done = arguments[arguments.length - 1];
            (async () => {
                try {
                    const addonModule = ChromeUtils.importESModule(
                        "resource://gre/modules/AddonManager.sys.mjs"
                    );
                    const addons = await addonModule.AddonManager.getAllAddons();
                    done({
                        ok: true,
                        addons: addons.map((addon) => ({
                            id: addon.id,
                            name: addon.name,
                            type: addon.type,
                            version: addon.version,
                            isActive: addon.isActive,
                            hidden: addon.hidden,
                            isBuiltin: addon.isBuiltin,
                            sourceURI: addon.sourceURI?.spec || null,
                        })),
                    });
                } catch (error) {
                    done({
                        ok: false,
                        error: String(error),
                    });
                }
            })();
            """)

    if not result.get("ok"):
        raise AssertionError(f"Failed to read installed Firefox add-ons: {result.get('error')}")

    addons = result.get("addons")
    if not isinstance(addons, list):
        raise AssertionError(f"Unexpected Firefox add-on payload: {result!r}")
    return addons


def wait_for_addon_install(
    driver: Any,
    addon_id: str,
    *,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
) -> dict[str, Any]:
    """Wait until the given add-on appears in Firefox AddonManager."""

    deadline = time.monotonic() + timeout_seconds
    last_seen_ids: list[str] = []
    while time.monotonic() < deadline:
        addons = get_installed_addons(driver)
        last_seen_ids = sorted(
            addon.get("id")
            for addon in addons
            if isinstance(addon, dict) and isinstance(addon.get("id"), str)
        )
        for addon in addons:
            if addon.get("id") == addon_id:
                return addon
        time.sleep(poll_interval_seconds)

    raise AssertionError(
        f"Firefox did not install add-on {addon_id!r} within {timeout_seconds:.0f}s. "
        f"Seen add-ons: {last_seen_ids}"
    )


@dataclass(frozen=True)
class StaticSite:
    base_url: str
    root_dir: Path

    def url(self, path: str = "/") -> str:
        return urljoin(self.base_url, path.lstrip("/"))


@dataclass(frozen=True)
class ProxySite:
    proxy_address: str
    requests: list[str]

    def url(self, path: str = "/proxy-check", host: str = "example.invalid") -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"http://{host}{normalized_path}"


@dataclass(frozen=True)
class HttpsSite:
    base_url: str
    root_dir: Path
    ca_cert_path: Path

    def url(self, path: str = "/") -> str:
        return urljoin(self.base_url, path.lstrip("/"))


@contextlib.contextmanager
def serve_static_site(root_dir: Path):
    """Serve a small local HTTP site for live browser behavior checks."""

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(root_dir), **kwargs)

        def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    site = StaticSite(base_url=f"http://127.0.0.1:{server.server_port}/", root_dir=root_dir)
    try:
        yield site
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def serve_http_proxy():
    """Serve a small local HTTP proxy that records requested absolute URLs."""

    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(self.path)
            body = (f"<html><body><h1>PROXY_OK</h1><p>{self.path}</p></body></html>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    site = ProxySite(
        proxy_address=f"127.0.0.1:{server.server_port}",
        requests=requests,
    )
    try:
        yield site
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def serve_https_site(root_dir: Path, openssl_binary: str):
    """Serve a local HTTPS site with a disposable CA for certificate policy tests."""

    ca_key = root_dir / "ca.key"
    ca_cert = root_dir / "ca.pem"
    server_key = root_dir / "server.key"
    server_csr = root_dir / "server.csr"
    server_cert = root_dir / "server.pem"
    server_ext = root_dir / "server.ext"
    server_ext.write_text(
        "subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            openssl_binary,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(ca_key),
            "-out",
            str(ca_cert),
            "-days",
            "1",
            "-subj",
            "/CN=BPM Live Test CA",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            openssl_binary,
            "req",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(server_key),
            "-out",
            str(server_csr),
            "-subj",
            "/CN=localhost",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            openssl_binary,
            "x509",
            "-req",
            "-in",
            str(server_csr),
            "-CA",
            str(ca_cert),
            "-CAkey",
            str(ca_key),
            "-CAcreateserial",
            "-out",
            str(server_cert),
            "-days",
            "1",
            "-sha256",
            "-extfile",
            str(server_ext),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(root_dir), **kwargs)

        def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=str(server_cert), keyfile=str(server_key))
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    site = HttpsSite(
        base_url=f"https://127.0.0.1:{server.server_port}/",
        root_dir=root_dir,
        ca_cert_path=ca_cert,
    )
    try:
        yield site
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
