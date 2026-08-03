from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import socket
import struct
import subprocess
import threading
import time
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import uvicorn

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DEFAULT_MATRIX = DOCUMENTATION_ROOT / "config/user-guide-screenshot-matrix-0.9.1.json"
DEFAULT_REPORT_ROOT = DOCUMENTATION_ROOT / "reports/screenshots"
DEFAULT_ASSET_ROOT = DOCUMENTATION_ROOT / "assets/screenshots"
DEFAULT_CHROMIUM = "/usr/bin/snap"
DEFAULT_CHROMEDRIVER = "/snap/bin/chromium.chromedriver"
DEFAULT_HOST = "127.0.0.1"
WAIT_SECONDS = 30

LOCALIZED_PROFILE_TEXT = {
    "en": {
        "primary_name": "Documentation Release baseline",
        "secondary_name": "Documentation ESR comparison",
        "primary_description": "Synthetic User Guide capture profile.",
        "secondary_description": "Synthetic ESR profile for comparison screenshots.",
    },
    "ru": {
        "primary_name": "Базовый профиль документации",
        "secondary_name": "Профиль ESR для сравнения",
        "primary_description": "Синтетический профиль для скриншотов руководства.",
        "secondary_description": "Синтетический профиль ESR для скриншота сравнения.",
    },
    "de": {
        "primary_name": "Dokumentationsprofil Release",
        "secondary_name": "Dokumentationsprofil ESR",
        "primary_description": "Synthetisches Profil für User-Guide-Screenshots.",
        "secondary_description": "Synthetisches ESR-Profil für Vergleichs-Screenshots.",
    },
    "zh-CN": {
        "primary_name": "文档 Release 基线",
        "secondary_name": "文档 ESR 对比",
        "primary_description": "用于用户指南截图的合成配置文件。",
        "secondary_description": "用于对比截图的合成 ESR 配置文件。",
    },
    "fr": {
        "primary_name": "Profil de documentation Release",
        "secondary_name": "Profil ESR de comparaison",
        "primary_description": "Profil synthétique pour les captures du guide.",
        "secondary_description": "Profil ESR synthétique pour les captures de comparaison.",
    },
    "es-ES": {
        "primary_name": "Perfil de documentación Release",
        "secondary_name": "Perfil ESR de comparacion",
        "primary_description": "Perfil sintético para capturas de la guía.",
        "secondary_description": "Perfil ESR sintético para capturas de comparación.",
    },
}


class CaptureError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ServerHandle:
    base_url: str
    server: uvicorn.Server
    thread: threading.Thread


@dataclass(frozen=True, slots=True)
class BrowserHandle:
    driver: Any
    process: subprocess.Popen[str]
    profile_dir: Path
    log_file: Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_free_port(host: str = DEFAULT_HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise CaptureError(f"{path} is not a PNG file")
    return struct.unpack(">II", header[16:24])


def _reset_sqlite_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-shm", "-wal"):
        candidate = db_path.with_name(f"{db_path.name}{suffix}")
        if candidate.exists():
            candidate.unlink()


@contextlib.contextmanager
def _run_app_server(*, db_path: Path, host: str = DEFAULT_HOST) -> Iterator[ServerHandle]:
    _reset_sqlite_database(db_path)
    os.environ["BPM_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

    from app.main import create_app

    app = create_app()
    port = _pick_free_port(host)
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://{host}:{port}"
    deadline = time.time() + WAIT_SECONDS
    last_error = ""

    try:
        while time.time() < deadline:
            try:
                response = requests.get(f"{base_url}/i18n/en.json", timeout=2)
                if response.status_code == 200:
                    break
                last_error = f"probe returned {response.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)
            time.sleep(0.2)
        else:
            raise CaptureError(f"Timed out waiting for BPM capture server: {last_error}")

        yield ServerHandle(base_url=base_url, server=server, thread=thread)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def _wait_for_debugger(debugger_url: str, process: subprocess.Popen[str], log_path: Path) -> None:
    deadline = time.time() + WAIT_SECONDS
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            last_error = log_path.read_text(encoding="utf-8", errors="ignore")
            break
        try:
            response = requests.get(debugger_url, timeout=2)
            if response.status_code == 200:
                return
            last_error = f"debugger probe returned {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise CaptureError(f"Chromium debugger did not become ready: {last_error}")


def _build_browser(
    *,
    report_root: Path,
    chromium_binary: str,
    chromedriver_binary: str,
) -> BrowserHandle:
    if not Path(chromium_binary).exists():
        raise CaptureError(f"Chromium snap launcher is not available at {chromium_binary}")
    if not Path(chromedriver_binary).exists():
        raise CaptureError(f"ChromeDriver binary is not available at {chromedriver_binary}")

    webdriver = __import__("selenium.webdriver", fromlist=["webdriver"])
    chrome_service = __import__("selenium.webdriver.chrome.service", fromlist=["Service"])

    debug_port = _pick_free_port()
    profile_dir = report_root / "browser-profiles" / f"chromium-{debug_port}"
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True)
    browser_log_path = profile_dir / "chromium.log"
    chromedriver_log_path = profile_dir / "chromedriver.log"
    browser_log = browser_log_path.open("w", encoding="utf-8")

    process = subprocess.Popen(
        [
            chromium_binary,
            "run",
            "chromium",
            "--headless=new",
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={debug_port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-popup-blocking",
            "--lang=en-US",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile_dir}",
            "--window-size=1440,1000",
            "about:blank",
        ],
        cwd=REPOSITORY_ROOT,
        stdout=browser_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    _wait_for_debugger(
        f"http://127.0.0.1:{debug_port}/json/version",
        process,
        browser_log_path,
    )

    options = webdriver.ChromeOptions()
    options.debugger_address = f"127.0.0.1:{debug_port}"
    service = chrome_service.Service(
        executable_path=chromedriver_binary,
        log_output=str(chromedriver_log_path),
    )
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(WAIT_SECONDS)
    return BrowserHandle(
        driver=driver,
        process=process,
        profile_dir=profile_dir,
        log_file=browser_log,
    )


def _close_browser(handle: BrowserHandle) -> None:
    try:
        handle.driver.quit()
    finally:
        if handle.process.poll() is None:
            handle.process.terminate()
            try:
                handle.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                handle.process.kill()
        handle.log_file.close()


def _request_json(method: str, url: str, **kwargs: Any) -> Any:
    response = requests.request(method, url, timeout=20, **kwargs)
    if response.status_code >= 400:
        raise CaptureError(f"{method} {url} failed: {response.status_code} {response.text}")
    if response.content:
        return response.json()
    return None


def _profile_payload(locale: str, fixture_id: str) -> dict[str, Any]:
    text = LOCALIZED_PROFILE_TEXT[locale]
    if fixture_id == "doc-profile-release-baseline":
        return {
            "name": text["primary_name"],
            "description": text["primary_description"],
            "schema_version": "release-153",
            "flags": {
                "DisableTelemetry": True,
                "Homepage": {
                    "URL": "https://portal.example.test/",
                    "Locked": True,
                },
                "Preferences": {
                    "browser.startup.homepage": {
                        "Value": "https://portal.example.test/",
                        "Status": "locked",
                        "Type": "string",
                    },
                    "browser.tabs.warnOnClose": {
                        "Value": True,
                        "Status": "locked",
                        "Type": "boolean",
                    },
                },
            },
            "compliance": {
                "framework": "cis",
                "benchmark_id": "bpm-doc-synthetic",
                "benchmark_version": "0.9.1",
                "layer": "documentation-screenshot",
                "summary": {"review_required": 1},
                "decisions": [
                    {
                        "path": ["Homepage"],
                        "decision": "manual_review_kept_base",
                        "selected_source": "base",
                        "base_value": {
                            "URL": "https://portal.example.test/",
                            "Locked": True,
                        },
                        "cis_value": {
                            "URL": "https://portal.example.test/",
                            "Locked": True,
                        },
                        "selected_value": {
                            "URL": "https://portal.example.test/",
                            "Locked": True,
                        },
                        "recommendation_ids": ["bpm-doc.synthetic.homepage-review"],
                        "merge_rule": "manual_review_required",
                        "review_required": True,
                        "reason": "Synthetic review state for localized User Guide screenshots.",
                    }
                ],
            },
        }
    if fixture_id == "doc-profile-esr-archived":
        return {
            "name": text["secondary_name"],
            "description": text["secondary_description"],
            "schema_version": "esr-140.13",
            "flags": {
                "DisableTelemetry": True,
                "DisableFirefoxStudies": True,
                "Preferences": {
                    "browser.shell.checkDefaultBrowser": {
                        "Value": False,
                        "Status": "locked",
                        "Type": "boolean",
                    },
                },
            },
        }
    raise CaptureError(f"Unknown screenshot fixture state: {fixture_id}")


def _seed_locale_profiles(base_url: str, locale: str) -> dict[str, int]:
    _request_json("DELETE", f"{base_url}/api/profiles/reset")
    profile_ids: dict[str, int] = {}
    for fixture_id in ("doc-profile-release-baseline", "doc-profile-esr-archived"):
        profile = _request_json(
            "POST",
            f"{base_url}/api/profiles",
            json=_profile_payload(locale, fixture_id),
        )
        profile_ids[fixture_id] = int(profile["id"])
    return profile_ids


def _configure_viewport(driver: Any, viewport: dict[str, int]) -> None:
    width = int(viewport["width"])
    height = int(viewport["height"])
    scale = int(viewport.get("device_scale_factor", 1))
    driver.set_window_size(width, height)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": height,
            "deviceScaleFactor": scale,
            "mobile": width < 700,
        },
    )


def _wait_for(driver: Any, condition: str, *args: Any, timeout: float = WAIT_SECONDS) -> Any:
    deadline = time.time() + timeout
    last_value: Any = None
    while time.time() < deadline:
        last_value = driver.execute_script(condition, *args)
        if last_value:
            return last_value
        time.sleep(0.15)
    raise CaptureError(f"Timed out waiting for browser condition: {condition!r}; last={last_value!r}")


def _set_locale_and_theme(driver: Any, locale: str, theme: str) -> None:
    driver.execute_script(
        """
        localStorage.setItem("bpm-lang-mode", arguments[0]);
        localStorage.setItem("bpm-theme-mode", arguments[1]);
        const lang = document.getElementById("lang");
        if (lang && lang.value !== arguments[0]) {
          lang.value = arguments[0];
          lang.dispatchEvent(new Event("change", { bubbles: true }));
        }
        const theme = document.getElementById("theme");
        if (theme && theme.value !== arguments[1]) {
          theme.value = arguments[1];
          theme.dispatchEvent(new Event("change", { bubbles: true }));
        }
        """,
        locale,
        theme,
    )
    _wait_for(driver, "return document.documentElement.lang === arguments[0];", locale)
    _wait_for(driver, "return document.documentElement.dataset.theme === arguments[0];", theme)


def _stabilize_page(driver: Any, scenario_id: str) -> None:
    driver.execute_script(
        """
        if (!document.getElementById("bpm-doc-screenshot-stabilizer")) {
          const style = document.createElement("style");
          style.id = "bpm-doc-screenshot-stabilizer";
          style.textContent = `
            *, *::before, *::after {
              animation-duration: 0s !important;
              animation-delay: 0s !important;
              transition-duration: 0s !important;
              caret-color: transparent !important;
            }
          `;
          document.head.appendChild(style);
        }
        if (arguments[0] === "all-settings-review") {
          const target = document.getElementById("all-settings-list")
            || document.getElementById("all-settings-list-panel");
          if (target) {
            window.scrollTo({
              top: Math.max(0, target.getBoundingClientRect().top + window.scrollY - 12),
              left: 0,
              behavior: "instant",
            });
          }
        } else {
          window.scrollTo(0, 0);
        }
        """
        ,
        scenario_id,
    )
    time.sleep(0.35)


def _set_input_value(driver: Any, selector: str, value: str) -> None:
    driver.execute_script(
        """
        const element = document.querySelector(arguments[0]);
        if (!element) return false;
        element.focus();
        element.value = arguments[1];
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
        return true;
        """,
        selector,
        value,
    )


def _click_selector(driver: Any, selector: str) -> None:
    clicked = driver.execute_script(
        """
        const element = document.querySelector(arguments[0]);
        if (!element) return false;
        element.scrollIntoView({ block: "center", inline: "center" });
        element.click();
        return true;
        """,
        selector,
    )
    if not clicked:
        raise CaptureError(f"Could not click selector: {selector}")


def _prepare_scenario(driver: Any, scenario_id: str) -> None:
    if scenario_id == "library-overview":
        _wait_for(driver, "return document.querySelectorAll('#list [data-library-profile-id]').length > 0;")
        driver.execute_script(
            """
            const sort = document.getElementById("sort");
            const order = document.getElementById("order");
            if (sort) sort.value = "name";
            if (order) order.value = "asc";
            sort?.dispatchEvent(new Event("change", { bubbles: true }));
            order?.dispatchEvent(new Event("change", { bubbles: true }));
            """
        )
        _wait_for(driver, "return document.querySelectorAll('#list [data-library-profile-id]').length > 0;")
        return

    if scenario_id == "guided-editor-overview":
        _wait_for(driver, "return Boolean(document.querySelector('#wizard-panel .wizard-step--active'));")
        return

    if scenario_id == "guided-settings-search":
        _wait_for(driver, "return Boolean(document.querySelector('#wizard-settings-search-input'));")
        _set_input_value(driver, "#wizard-settings-search-input", "homepage")
        _wait_for(
            driver,
            "return document.querySelectorAll('#wizard-settings-search-results "
            "[data-settings-search-target]').length > 0;",
        )
        return

    if scenario_id == "all-settings-review":
        _wait_for(driver, "return document.querySelectorAll('#all-settings-list [data-settings-entry-id]').length > 0;")
        _click_selector(driver, '[data-settings-list-filter="configured"]')
        _wait_for(
            driver,
            "return document.querySelectorAll('#all-settings-list "
            "[data-settings-entry-state=\"configured\"]').length > 0;",
        )
        _click_selector(driver, "#all-settings-list [data-settings-entry-id]")
        _wait_for(
            driver,
            "return !document.querySelector('#all-settings-detail-panel .wizard-shell-empty');",
        )
        return

    if scenario_id == "json-editor":
        _wait_for(driver, "return Boolean(document.querySelector('#editor-panel'));")
        _wait_for(
            driver,
            "return Boolean(document.querySelector('#editor .monaco-editor')) "
            "|| /Workspace ready|loaded|загружен|bereit|cargado|chargé|已/.test("
            "document.getElementById('status')?.textContent || '');",
        )
        return

    if scenario_id == "compare-profiles":
        _wait_for(
            driver,
            "return document.querySelectorAll('[data-compare-selected-profile] "
            ".compare-selected-profile__name').length >= 2;",
        )
        _wait_for(driver, "return document.querySelectorAll('#compare-settings-rows tr').length > 0;")
        return

    raise CaptureError(f"Unknown screenshot scenario: {scenario_id}")


def _asset_target(row: dict[str, Any], asset_root: Path) -> Path:
    return asset_root / str(row["locale"]) / str(row["filename"])


def _route_for_row(row: dict[str, Any], profile_ids: dict[str, int]) -> str:
    route = str(row["route"])
    if "{profile_id}" in route:
        route = route.format(profile_id=profile_ids[str(row["fixture_state"])])
    if row["scenario_id"] == "all-settings-review":
        separator = "&" if "?" in route else "?"
        route = f"{route}{separator}settingsMode=configured"
    if row["scenario_id"] == "compare-profiles":
        secondary = row.get("secondary_fixture_state")
        if not secondary:
            raise CaptureError("compare-profiles row is missing secondary_fixture_state")
        separator = "&" if "?" in route else "?"
        route = (
            f"{route}{separator}left={profile_ids[str(row['fixture_state'])]}"
            f"&right={profile_ids[str(secondary)]}"
        )
    return route


def _capture_row(
    *,
    driver: Any,
    base_url: str,
    matrix: dict[str, Any],
    row: dict[str, Any],
    profile_ids: dict[str, int],
    asset_root: Path,
) -> dict[str, Any]:
    contract = matrix["capture_state_contract"]
    scenario_state = contract["scenario_ui_states"][row["scenario_id"]]
    viewport = contract["viewports"][row["viewport"]]
    asset_path = _asset_target(row, asset_root)
    route = _route_for_row(row, profile_ids)
    context = {
        "locale": row["locale"],
        "topic_id": row["topic_id"],
        "route": row["route"],
        "resolved_route": route,
        "state_id": scenario_state["state_id"],
        "matrix_row_id": row["id"],
        "scenario_id": row["scenario_id"],
        "viewport": row["viewport"],
        "theme": row["theme"],
        "schema_channel": scenario_state["schema_channel"],
        "fixture_state": row["fixture_state"],
        "asset_path": str(asset_path.relative_to(REPOSITORY_ROOT)),
    }

    try:
        _configure_viewport(driver, viewport)
        driver.get(f"{base_url}{route}")
        _wait_for(driver, "return document.readyState === 'complete';")
        _set_locale_and_theme(driver, str(row["locale"]), str(row["theme"]))
        _prepare_scenario(driver, str(row["scenario_id"]))
        _stabilize_page(driver, str(row["scenario_id"]))
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(asset_path))
        width, height = _read_png_size(asset_path)
        expected_width = int(viewport["width"])
        expected_height = int(viewport["height"])
        if (width, height) != (expected_width, expected_height):
            raise CaptureError(
                f"PNG dimensions {width}x{height} do not match "
                f"{expected_width}x{expected_height}"
            )
    except Exception as exc:
        payload = json.dumps(context, ensure_ascii=False, sort_keys=True)
        raise CaptureError(f"Screenshot capture failed: {payload}") from exc

    return {
        **context,
        "width": width,
        "height": height,
        "bytes": asset_path.stat().st_size,
    }


def capture_screenshots(
    *,
    matrix_path: Path,
    asset_root: Path,
    report_root: Path,
    chromium_binary: str,
    chromedriver_binary: str,
    locales: set[str] | None = None,
    scenarios: set[str] | None = None,
) -> dict[str, Any]:
    matrix = _load_json(matrix_path)
    rows = [
        row
        for row in matrix["matrix"]
        if (not locales or row["locale"] in locales)
        and (not scenarios or row["scenario_id"] in scenarios)
    ]
    rows_by_locale: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_locale[str(row["locale"])].append(row)

    report_root.mkdir(parents=True, exist_ok=True)
    runtime_db = report_root / "runtime/user-guide-screenshots-0.9.1.db"
    captured: list[dict[str, Any]] = []

    with _run_app_server(db_path=runtime_db) as server:
        browser = _build_browser(
            report_root=report_root,
            chromium_binary=chromium_binary,
            chromedriver_binary=chromedriver_binary,
        )
        try:
            for locale in matrix["locales"]:
                if locale not in rows_by_locale:
                    continue
                print(f"[screenshots] locale={locale} seed profiles", flush=True)
                profile_ids = _seed_locale_profiles(server.base_url, locale)
                for row in rows_by_locale[locale]:
                    print(
                        f"[screenshots] capture {row['id']} -> {row['asset_path']}",
                        flush=True,
                    )
                    captured.append(
                        _capture_row(
                            driver=browser.driver,
                            base_url=server.base_url,
                            matrix=matrix,
                            row=row,
                            profile_ids=profile_ids,
                            asset_root=asset_root,
                        )
                    )
        finally:
            _close_browser(browser)

    report = {
        "schema_version": 1,
        "backlog_item": "BPM091-M5-02",
        "matrix_id": matrix["matrix_id"],
        "target_bpm_version": matrix["target_bpm_version"],
        "capture_command": (
            "./.venv/bin/python documentation/tools/capture_user_guide_screenshots.py"
        ),
        "runtime_database": str(runtime_db.relative_to(REPOSITORY_ROOT)),
        "asset_root": str(asset_root.relative_to(REPOSITORY_ROOT)),
        "rows_captured": len(captured),
        "rows_expected": len(rows),
        "captured": captured,
    }
    report_path = report_root / "user-guide-screenshots-0.9.1.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture the BPM 0.9.1 minimal User Guide screenshot matrix.",
    )
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--asset-root", type=Path, default=DEFAULT_ASSET_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--chromium-binary", default=DEFAULT_CHROMIUM)
    parser.add_argument("--chromedriver-binary", default=DEFAULT_CHROMEDRIVER)
    parser.add_argument("--locale", action="append", dest="locales")
    parser.add_argument("--scenario", action="append", dest="scenarios")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = capture_screenshots(
        matrix_path=args.matrix,
        asset_root=args.asset_root,
        report_root=args.report_root,
        chromium_binary=args.chromium_binary,
        chromedriver_binary=args.chromedriver_binary,
        locales=set(args.locales) if args.locales else None,
        scenarios=set(args.scenarios) if args.scenarios else None,
    )
    print(
        f"[screenshots] captured {report['rows_captured']} of {report['rows_expected']} rows",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
