#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

import requests
import uvicorn
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "artifacts" / "local_chromium_ui_audit"
DEFAULT_CHROMIUM = "/snap/bin/chromium"
DEFAULT_CHROMEDRIVER = "/snap/bin/chromium.chromedriver"
DEFAULT_SNAP = "/usr/bin/snap"
DEFAULT_HOST = "127.0.0.1"
WAIT_SECONDS = 25


@dataclass
class AuditCheck:
    name: str
    ok: bool
    details: str = ""
    screenshot: str | None = None


@dataclass
class ViewportRun:
    name: str
    width: int
    height: int
    screenshots: list[str] = field(default_factory=list)
    checks: list[AuditCheck] = field(default_factory=list)


@dataclass
class AuditReport:
    output_dir: str
    base_url: str
    profile_name: str
    profile_id: int | None = None
    viewports: list[ViewportRun] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def add_failure(self, message: str) -> None:
        self.failures.append(message)

    @property
    def ok(self) -> bool:
        return not self.failures and all(
            check.ok for viewport in self.viewports for check in viewport.checks
        )


class AuditError(RuntimeError):
    pass


class UiAuditRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.output_dir = (Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_ROOT / timestamp)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.server_logs_path = self.output_dir / "server.log"
        self.chromedriver_logs_path = self.output_dir / "chromedriver.log"
        self.base_url = (args.base_url or f"http://{DEFAULT_HOST}:{args.port}").rstrip("/")
        self.profile_name = f"BPM Chromium Audit {timestamp}"
        self.profile_owner = "QA automation"
        self.profile_description = "Local Chromium guided and advanced UI audit"
        self.locales = self._load_locales()
        self.report = AuditReport(
            output_dir=str(self.output_dir),
            base_url=self.base_url,
            profile_name=self.profile_name,
        )

    def _load_locales(self) -> dict[str, dict[str, str]]:
        base_url = (self.args.base_url or f"http://{DEFAULT_HOST}:{self.args.port}").rstrip("/")
        locales: dict[str, dict[str, str]] = {}
        for lang in ("en", "ru"):
            response = requests.get(f"{base_url}/i18n/{lang}.json", timeout=10)
            response.raise_for_status()
            locales[lang] = response.json()
        return locales

    def run(self) -> int:
        desktop_view = ViewportRun(name="desktop", width=1440, height=2200)
        self.report.viewports.append(desktop_view)
        profile_id = self.run_desktop_flow(desktop_view)
        self.report.profile_id = profile_id

        mobile_view = ViewportRun(name="mobile", width=390, height=844)
        self.report.viewports.append(mobile_view)
        self.run_mobile_flow(mobile_view, profile_id)

        self.write_report_files()
        return 0 if self.report.ok else 1

    def run_desktop_flow(self, viewport: ViewportRun) -> int:
        driver = self.create_driver(viewport.width, viewport.height, mobile=False)
        try:
            self.bootstrap_browser(driver)
            self.open_and_wait(driver, "/profiles")
            self.capture(driver, viewport, "desktop_library_initial")
            self.record(
                viewport,
                "library_loaded",
                self.is_present(driver, By.ID, "create-profile-link"),
                "Profiles library opened and create action is visible.",
            )

            self.click(driver, By.ID, "create-profile-link")
            self.wait_for(driver, EC.presence_of_element_located((By.ID, "wizard-panel")))
            self.wait_for(driver, EC.presence_of_element_located((By.ID, "wizard-export-save-action")))
            self.capture(driver, viewport, "desktop_new_profile_initial")

            self.set_profile_metadata(driver)
            self.apply_theme(driver, viewport, "dark")
            self.verify_dark_theme(driver, viewport, "desktop_dark_theme_initial")
            self.verify_language_switch(driver, viewport)

            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-scenario-key="shared_devices"]',
                "step1_scenario_shared_devices",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-starter-key="classroom_kiosk"]',
                "step1_starter_classroom_kiosk",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-cis-layer-key="cis_l1"]',
                "step1_cis_l1",
            )
            self.capture(driver, viewport, "desktop_step1_setup")
            self.verify_layout(driver, viewport, "desktop_step1_setup")

            self.go_to_step(driver, 2)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-general-policy-preset="managed"]',
                "step2_general_managed",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-proxy-preset="manual"]',
                "step2_proxy_manual",
            )
            self.fill_input(driver, "wizard-proxy-http", "proxy.internal.local")
            self.fill_input(driver, "wizard-proxy-passthrough", "localhost\n127.0.0.1")
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-network-enterprise-preset="sso"]',
                "step2_network_sso",
            )
            self.toggle_disclosure(driver, "wizard-network-enterprise-fine-tuning-toggle")
            self.capture(driver, viewport, "desktop_step2_general")
            self.verify_layout(driver, viewport, "desktop_step2_general")

            self.go_to_step(driver, 3)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-homepage-shared-preset="portal_locked"]',
                "step3_homepage_shared_portal_locked",
            )
            self.fill_input(driver, "wizard-homepage-url", "https://portal.example.test")
            self.select_by_value(driver, "wizard-homepage-start-page", "homepage")
            self.toggle_section(driver, '[data-home-surface-toggle="new_tab"]')
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-home-overrides-preset="first_run"]',
                "step3_home_overrides_first_run",
            )
            self.toggle_section(driver, '[data-home-surface-toggle="firefox_home"]')
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-firefox-home-preset="focused"]',
                "step3_firefox_home_focused",
            )
            self.capture(driver, viewport, "desktop_step3_home")
            self.verify_layout(driver, viewport, "desktop_step3_home")

            self.go_to_step(driver, 4)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-search-defaults-preset="custom_engines"]',
                "step4_search_defaults_custom",
            )
            self.fill_input(driver, "wizard-search-default-engine", "DuckDuckGo")
            self.open_details(driver, '[data-search-engine-presets-menu] summary')
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-search-engine-preset="duckduckgo"]',
                "step4_search_preset_ddg",
            )
            self.click(driver, By.ID, "wizard-search-engine-add")
            self.fill_css(driver, '[data-search-engine-field="Name"]', "Docs")
            self.fill_css(driver, '[data-search-engine-field="URLTemplate"]', "https://docs.example.test/search?q={searchTerms}")
            self.fill_css(driver, '[data-search-engine-field="Alias"]', "docs")
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-firefox-suggest-preset="private"]',
                "step4_firefox_suggest_private",
            )
            self.capture(driver, viewport, "desktop_step4_search")
            self.verify_layout(driver, viewport, "desktop_step4_search")

            self.go_to_step(driver, 5)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-hardening-preset="strict"]',
                "step5_hardening_strict",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-cleanup-preset="shared"]',
                "step5_cleanup_shared",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-site-data-preset="balanced"]',
                "step5_site_data_balanced",
            )
            self.capture(driver, viewport, "desktop_step5_privacy")
            self.verify_layout(driver, viewport, "desktop_step5_privacy")

            self.go_to_step(driver, 6)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-sync-focus-preset="managed"]',
                "step6_sync_managed",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-language-preset="locales"]',
                "step6_language_locales",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-extension-governance-preset="curated"]',
                "step6_extensions_curated",
            )
            self.select_css_by_value(
                driver,
                '[data-extension-profile="uBlock0@raymondhill.net"][data-extension-field="mode"]',
                "force_installed",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-website-access-posture="allow_only"]',
                "step6_website_allow_only",
            )
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-website-access-handlers="protocols"]',
                "step6_handlers_protocols",
            )
            self.capture(driver, viewport, "desktop_step6_features")
            self.verify_layout(driver, viewport, "desktop_step6_features")

            self.go_to_step(driver, 7)
            self.click_and_verify_pressed(
                driver,
                viewport,
                '[data-ai-posture-preset="mixed"]',
                "step7_ai_mixed",
            )
            self.capture(driver, viewport, "desktop_step7_ai")
            self.verify_layout(driver, viewport, "desktop_step7_ai")

            self.go_to_step(driver, 8)
            self.capture(driver, viewport, "desktop_step8_export_before_save")
            self.verify_layout(driver, viewport, "desktop_step8_export_before_save")
            previous_validation_state = self.text_of(driver, By.ID, "wizard-export-validation-state")
            previous_validation_preview = self.text_of(driver, By.ID, "validation-preview")
            self.click(driver, By.ID, "wizard-export-validate-action")
            self.wait_for_text_change(driver, By.ID, "validation-preview", previous_validation_preview)
            self.dump_export_debug(driver, "after_validate")
            self.record(
                viewport,
                "validation_action_updates_state",
                self.text_of(driver, By.ID, "wizard-export-validation-state") != previous_validation_state
                or self.text_of(driver, By.ID, "validation-preview") != previous_validation_preview,
                self.text_of(driver, By.ID, "validation-preview"),
            )
            self.click(driver, By.ID, "wizard-export-save-action")
            try:
                profile_id = self.wait_for_saved_profile()
            except Exception:
                self.dump_export_debug(driver, "after_save_failure")
                raise
            self.capture(driver, viewport, "desktop_step8_export_after_save")
            self.record(
                viewport,
                "profile_saved_via_ui",
                profile_id > 0,
                f"Profile ID {profile_id} created from guided wizard.",
            )

            self.open_and_wait(driver, f"/profiles?mode=advanced&q={quote(self.profile_name)}")
            self.capture(driver, viewport, "desktop_library_after_save")
            self.record(
                viewport,
                "library_search_contains_profile",
                self.page_contains(driver, self.profile_name),
                f"Found saved profile '{self.profile_name}' in library view.",
            )

            self.open_and_wait(
                driver,
                f"/profiles/{profile_id}/advanced?return=/profiles/{profile_id}/edit",
            )
            self.wait_for(driver, EC.presence_of_element_located((By.ID, "details-panel")))
            self.capture(driver, viewport, "desktop_advanced_details")
            self.verify_dark_theme(driver, viewport, "desktop_advanced_dark_theme")
            self.record(
                viewport,
                "advanced_route_opened",
                self.page_contains(driver, self.profile_name),
                "Advanced route opened for the saved profile.",
            )
            return profile_id
        finally:
            self.shutdown_driver(driver)

    def run_mobile_flow(self, viewport: ViewportRun, profile_id: int) -> None:
        driver = self.create_driver(viewport.width, viewport.height, mobile=True)
        try:
            self.bootstrap_browser(driver)
            self.open_and_wait(driver, "/profiles")
            self.apply_theme(driver, viewport, "dark")
            self.apply_language(driver, viewport, "ru")
            self.capture(driver, viewport, "mobile_library_ru")
            self.verify_dark_theme(driver, viewport, "mobile_library_dark")
            self.verify_layout(driver, viewport, "mobile_library")
            self.fill_input(driver, "search", self.profile_name)
            self.wait_for(driver, lambda d: self.page_contains(d, self.profile_name))
            self.capture(driver, viewport, "mobile_library_filtered")

            self.open_and_wait(driver, f"/profiles/{profile_id}/edit")
            self.wait_for(driver, EC.presence_of_element_located((By.ID, "wizard-panel")))
            self.record(
                viewport,
                "mobile_workspace_scope_guided_active",
                self.attr_equals(driver, By.ID, "workspace-scope-guided", "aria-pressed", "true"),
                "Guided workspace scope is active on mobile edit route.",
            )
            for step in range(1, 9):
                self.go_to_step(driver, step)
                self.capture(driver, viewport, f"mobile_step{step}")
                self.verify_layout(driver, viewport, f"mobile_step{step}")

            self.open_and_wait(
                driver,
                f"/profiles/{profile_id}/advanced?return=/profiles/{profile_id}/edit",
            )
            self.capture(driver, viewport, "mobile_advanced")
            self.verify_layout(driver, viewport, "mobile_advanced")
            self.verify_dark_theme(driver, viewport, "mobile_advanced_dark")
        finally:
            self.shutdown_driver(driver)

    def write_report_files(self) -> None:
        report_json = self.output_dir / "report.json"
        report_md = self.output_dir / "report.md"
        report_json.write_text(
            json.dumps(
                {
                    "ok": self.report.ok,
                    "failures": self.report.failures,
                    "profile_id": self.report.profile_id,
                    "profile_name": self.report.profile_name,
                    "base_url": self.report.base_url,
                    "viewports": [
                        {
                            "name": view.name,
                            "width": view.width,
                            "height": view.height,
                            "screenshots": view.screenshots,
                            "checks": [asdict(check) for check in view.checks],
                        }
                        for view in self.report.viewports
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        lines = [
            "# Local Chromium UI Audit",
            "",
            f"- Result: {'PASS' if self.report.ok else 'FAIL'}",
            f"- Base URL: `{self.report.base_url}`",
            f"- Output directory: `{self.output_dir}`",
            f"- Profile: `{self.report.profile_name}`",
            f"- Profile ID: `{self.report.profile_id}`",
            "",
        ]
        if self.report.failures:
            lines.extend(["## Failures", ""])
            for failure in self.report.failures:
                lines.append(f"- {failure}")
            lines.append("")
        for viewport in self.report.viewports:
            lines.extend([f"## {viewport.name.title()}", ""])
            for check in viewport.checks:
                status = "PASS" if check.ok else "FAIL"
                screenshot = f" ({check.screenshot})" if check.screenshot else ""
                details = f": {check.details}" if check.details else ""
                lines.append(f"- [{status}] {check.name}{details}{screenshot}")
            lines.append("")
        report_md.write_text("\n".join(lines), encoding="utf-8")

    def create_driver(self, width: int, height: int, mobile: bool) -> WebDriver:
        if shutil.which(self.args.chromium_binary) is None and not Path(self.args.chromium_binary).exists():
            raise AuditError(f"Chromium binary not found: {self.args.chromium_binary}")
        if shutil.which(self.args.chromedriver_binary) is None:
            raise AuditError(f"ChromeDriver binary not found: {self.args.chromedriver_binary}")

        debug_port = pick_free_port()
        browser_profile_dir = Path(
            tempfile.mkdtemp(prefix=f"bpm-chromium-{debug_port}-", dir=str(self.output_dir))
        )
        browser_process = self.launch_chromium(
            debug_port=debug_port,
            width=width,
            height=height,
            mobile=mobile,
            profile_dir=browser_profile_dir,
        )
        self.wait_for_debugger(debug_port)

        options = ChromeOptions()
        options.debugger_address = f"{DEFAULT_HOST}:{debug_port}"
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        service = ChromeService(
            executable_path=self.args.chromedriver_binary,
            log_output=str(self.chromedriver_logs_path),
        )
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(width, height)
        driver.set_page_load_timeout(WAIT_SECONDS)
        driver._bpm_browser_process = browser_process
        driver._bpm_browser_profile_dir = browser_profile_dir
        return driver

    def launch_chromium(
        self,
        *,
        debug_port: int,
        width: int,
        height: int,
        mobile: bool,
        profile_dir: Path,
    ) -> subprocess.Popen[str]:
        command = [
            DEFAULT_SNAP,
            "run",
            "chromium",
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
            f"--window-size={width},{height}",
            "about:blank",
        ]
        if self.args.headless:
            command.insert(3, "--headless=new")
        if mobile:
            command.insert(
                3,
                "--user-agent=Mozilla/5.0 (Linux; Android 14; BPM Audit) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
            )
        log_file = (profile_dir / "chromium.log").open("w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        process._bpm_log_file = log_file
        return process

    def wait_for_debugger(self, debug_port: int) -> None:
        debugger_url = f"http://{DEFAULT_HOST}:{debug_port}/json/version"
        deadline = time.time() + WAIT_SECONDS
        while time.time() < deadline:
            try:
                response = requests.get(debugger_url, timeout=2)
                if response.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.25)
        raise AuditError(f"Timed out waiting for Chromium remote debugger at {debugger_url}")

    def bootstrap_browser(self, driver: WebDriver) -> None:
        driver.get(f"{self.base_url}/profiles")
        driver.execute_script(
            """
            window.localStorage.clear();
            window.sessionStorage.clear();
            """
        )
        driver.get(f"{self.base_url}/profiles")
        self.wait_for(driver, EC.presence_of_element_located((By.ID, "lang")))

    def open_and_wait(self, driver: WebDriver, path: str) -> None:
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        driver.get(url)
        self.wait_for(driver, lambda d: d.execute_script("return document.readyState") == "complete")

    def set_profile_metadata(self, driver: WebDriver) -> None:
        driver.execute_script(
            """
            const profileTypeEl = document.getElementById("profile-type");
            if (profileTypeEl && Array.from(profileTypeEl.options).some((option) => option.value === "release-150")) {
                profileTypeEl.value = "release-150";
                profileTypeEl.dispatchEvent(new Event("change", { bubbles: true }));
            }
            """,
        )
        for field_id, value in (
            ("profile-name", self.profile_name),
            ("profile-owner", self.profile_owner),
            ("profile-description", self.profile_description),
        ):
            driver.execute_script(
                """
                const el = document.getElementById(arguments[0]);
                if (!el) throw new Error(`missing field ${arguments[0]}`);
                el.value = arguments[1];
                el.dispatchEvent(new Event("input", { bubbles: true }));
                el.dispatchEvent(new Event("change", { bubbles: true }));
                """,
                field_id,
                value,
            )

    def apply_theme(self, driver: WebDriver, viewport: ViewportRun, mode: str) -> None:
        select = driver.find_element(By.ID, "theme")
        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event("change", { bubbles: true }));
            """,
            select,
            mode,
        )
        self.wait_for(driver, lambda d: d.find_element(By.TAG_NAME, "html").get_attribute("data-theme") == mode)
        self.record(
            viewport,
            f"theme_{mode}_applied",
            True,
            f"HTML data-theme is '{mode}'.",
        )

    def apply_language(self, driver: WebDriver, viewport: ViewportRun, mode: str) -> None:
        select = driver.find_element(By.ID, "lang")
        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event("change", { bubbles: true }));
            """,
            select,
            mode,
        )
        resolved = "en" if mode == "en" else "ru"
        try:
            self.wait_for(driver, lambda d: d.find_element(By.TAG_NAME, "html").get_attribute("lang") == resolved)
        except TimeoutException:
            self.record(
                viewport,
                f"language_{mode}_live_switch",
                False,
                f"Language select did not switch HTML lang to {resolved!r} without reload.",
            )
            driver.execute_script(
                """
                window.localStorage.setItem("bpm-lang-mode", arguments[0]);
                window.location.reload();
                """,
                mode,
            )
            self.wait_for(driver, lambda d: d.execute_script("return document.readyState") == "complete")
            self.wait_for(
                driver,
                lambda d: d.find_element(By.TAG_NAME, "html").get_attribute("lang") == resolved,
            )
        self.record(
            viewport,
            f"language_{mode}_applied",
            True,
            f"HTML lang is '{resolved}'.",
        )

    def verify_language_switch(self, driver: WebDriver, viewport: ViewportRun) -> None:
        selector_to_key = {
            '[data-i18n="profiles.title"]': "profiles.title",
            '[data-i18n="profiles.locale_label"]': "profiles.locale_label",
            '[data-i18n="profiles.theme_label"]': "profiles.theme_label",
            '[data-step="1"] .wizard-step-label': "profiles.wizard_step_one",
            '[data-step="2"] .wizard-step-label': "profiles.wizard_step_two",
            '[data-step="8"] .wizard-step-label': "profiles.wizard_step_eight",
        }
        for mode, opposite in (("en", "ru"), ("ru", "en"), ("en", "ru")):
            self.apply_language(driver, viewport, mode)
            self.capture(driver, viewport, f"locale_{mode}")
            locale = self.locales[mode]
            opposite_locale = self.locales[opposite]
            for selector, key in selector_to_key.items():
                actual = self.text_css(driver, selector)
                expected = locale[key]
                opposite_text = opposite_locale[key]
                actual_normalized = actual.casefold()
                expected_normalized = expected.casefold()
                opposite_normalized = opposite_text.casefold()
                ok = actual_normalized == expected_normalized and actual_normalized != opposite_normalized
                details = f"{selector} => actual={actual!r}, expected={expected!r}"
                self.record(
                    viewport,
                    f"locale_{mode}_{key}",
                    ok,
                    details,
                    screenshot=viewport.screenshots[-1] if viewport.screenshots else None,
                )

    def go_to_step(self, driver: WebDriver, step: int) -> None:
        button = driver.find_element(By.CSS_SELECTOR, f'.wizard-step[data-step="{step}"]')
        self.safe_click(driver, button, locator=(By.CSS_SELECTOR, f'.wizard-step[data-step="{step}"]'))
        self.wait_for(
            driver,
            lambda d: d.find_element(By.CSS_SELECTOR, f'.wizard-step[data-step="{step}"]').get_attribute("aria-current") == "step",
        )
        self.wait_for(
            driver,
            lambda d: d.find_element(By.ID, f"wizard-step-{step}").is_displayed(),
        )

    def wait_for_saved_profile(self) -> int:
        deadline = time.time() + WAIT_SECONDS
        params = {"q": self.profile_name, "include_deleted": "true"}
        while time.time() < deadline:
            response = requests.get(f"{self.base_url}/api/profiles", params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", []) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
            if items:
                return int(items[0]["id"])
            time.sleep(0.5)
        raise AuditError(f"Timed out waiting for profile save: {self.profile_name}")

    def verify_layout(self, driver: WebDriver, viewport: ViewportRun, name: str) -> None:
        result = driver.execute_script(
            """
            const offenders = [];
            const vw = window.innerWidth;
            const root = document.documentElement;
            const horizontalTolerance = Math.max(6, window.innerWidth - root.clientWidth + 2);
            for (const el of document.querySelectorAll("body *")) {
                if (["SCRIPT", "STYLE", "NOSCRIPT", "OPTION"].includes(el.tagName)) continue;
                if (el.closest(".monaco-editor")) continue;
                const style = getComputedStyle(el);
                if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity || "1") === 0) continue;
                const rect = el.getBoundingClientRect();
                if (rect.width < 4 || rect.height < 4) continue;
                if (rect.right > vw + horizontalTolerance || rect.left < -horizontalTolerance) {
                    offenders.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || "",
                        classes: typeof el.className === "string" ? el.className.slice(0, 80) : "",
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        width: Math.round(rect.width),
                    });
                }
                if (offenders.length >= 20) break;
            }
            return {
                scrollWidth: root.scrollWidth,
                clientWidth: root.clientWidth,
                innerWidth: window.innerWidth,
                horizontalTolerance,
                offenders,
            };
            """
        )
        allowed_width = max(result["clientWidth"], result["innerWidth"]) + result["horizontalTolerance"]
        ok = result["scrollWidth"] <= allowed_width and not result["offenders"]
        details = (
            f"scrollWidth={result['scrollWidth']}, clientWidth={result['clientWidth']}, "
            f"innerWidth={result['innerWidth']}, tolerance={result['horizontalTolerance']}, "
            f"offenders={len(result['offenders'])}"
        )
        if result["offenders"]:
            details += f", sample={json.dumps(result['offenders'][:3], ensure_ascii=False)}"
        self.record(viewport, f"{name}_fits_viewport", ok, details)

    def verify_dark_theme(self, driver: WebDriver, viewport: ViewportRun, name: str) -> None:
        result = driver.execute_script(
            """
            function luminance(r, g, b) {
                const channel = (value) => {
                    const normalized = value / 255;
                    return normalized <= 0.03928 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
                };
                return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
            }

            function parseColor(input) {
                const match = input.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/i);
                if (!match) return null;
                return {
                    r: Number(match[1]),
                    g: Number(match[2]),
                    b: Number(match[3]),
                    a: match[4] === undefined ? 1 : Number(match[4]),
                };
            }

            const offenders = [];
            for (const el of document.querySelectorAll("body *")) {
                if (["SCRIPT", "STYLE", "NOSCRIPT", "OPTION", "SVG", "PATH"].includes(el.tagName)) continue;
                const style = getComputedStyle(el);
                if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity || "1") === 0) continue;
                const rect = el.getBoundingClientRect();
                if (rect.width < 8 || rect.height < 8) continue;
                const bg = parseColor(style.backgroundColor);
                if (!bg || bg.a < 0.85) continue;
                const lightness = luminance(bg.r, bg.g, bg.b);
                if (lightness > 0.70) {
                    offenders.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || "",
                        classes: typeof el.className === "string" ? el.className.slice(0, 80) : "",
                        backgroundColor: style.backgroundColor,
                        luminance: Number(lightness.toFixed(3)),
                    });
                }
                if (offenders.length >= 20) break;
            }
            return offenders;
            """
        )
        ok = not result
        details = "No bright backgrounds detected in dark theme."
        if result:
            details = f"Bright backgrounds detected: {json.dumps(result[:5], ensure_ascii=False)}"
        self.record(viewport, f"{name}_no_light_backgrounds", ok, details)

    def click_and_verify_pressed(
        self,
        driver: WebDriver,
        viewport: ViewportRun,
        css_selector: str,
        check_name: str,
    ) -> None:
        already_pressed = self.css_attr(driver, css_selector, "aria-pressed") == "true"
        if not already_pressed:
            self.click_css(driver, css_selector)
            self.wait_for(driver, lambda d: self.css_attr(d, css_selector, "aria-pressed") == "true")
        active_class = self.css_attr(d=driver, css=css_selector, attr="class")
        ok = "active" in active_class or "applied" in active_class or "preview" not in active_class
        self.record(
            viewport,
            check_name,
            ok,
            f"{css_selector} class={active_class!r} already_pressed={already_pressed}",
        )

    def click_css(self, driver: WebDriver, css_selector: str) -> None:
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        self.safe_click(driver, element, locator=(By.CSS_SELECTOR, css_selector))

    def click(self, driver: WebDriver, by: str, value: str) -> None:
        element = driver.find_element(by, value)
        self.safe_click(driver, element, locator=(by, value))

    def fill_input(self, driver: WebDriver, element_id: str, value: str) -> None:
        for attempt in range(3):
            try:
                element = driver.find_element(By.ID, element_id)
                self.scroll_to(driver, element)
                element.clear()
                element.send_keys(value)
                element.send_keys(Keys.TAB)
                return
            except StaleElementReferenceException:
                if attempt == 2:
                    driver.execute_script(
                        """
                        const el = document.getElementById(arguments[0]);
                        if (!el) throw new Error(`missing field ${arguments[0]}`);
                        el.value = arguments[1];
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                        el.dispatchEvent(new Event("blur", { bubbles: true }));
                        """,
                        element_id,
                        value,
                    )
                    return

    def fill_css(self, driver: WebDriver, css_selector: str, value: str) -> None:
        for attempt in range(3):
            try:
                element = driver.find_element(By.CSS_SELECTOR, css_selector)
                self.scroll_to(driver, element)
                element.clear()
                element.send_keys(value)
                element.send_keys(Keys.TAB)
                return
            except StaleElementReferenceException:
                if attempt == 2:
                    driver.execute_script(
                        """
                        const el = document.querySelector(arguments[0]);
                        if (!el) throw new Error(`missing selector ${arguments[0]}`);
                        el.value = arguments[1];
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                        el.dispatchEvent(new Event("blur", { bubbles: true }));
                        """,
                        css_selector,
                        value,
                    )
                    return

    def select_by_value(self, driver: WebDriver, element_id: str, value: str) -> None:
        select = Select(driver.find_element(By.ID, element_id))
        select.select_by_value(value)

    def select_css_by_value(self, driver: WebDriver, css_selector: str, value: str) -> None:
        select = Select(driver.find_element(By.CSS_SELECTOR, css_selector))
        select.select_by_value(value)

    def toggle_disclosure(self, driver: WebDriver, element_id: str) -> None:
        button = driver.find_element(By.ID, element_id)
        self.safe_click(driver, button, locator=(By.ID, element_id))
        self.wait_for(driver, lambda d: d.find_element(By.ID, element_id).get_attribute("aria-expanded") == "true")

    def open_details(self, driver: WebDriver, summary_selector: str) -> None:
        summary = driver.find_element(By.CSS_SELECTOR, summary_selector)
        self.safe_click(driver, summary, locator=(By.CSS_SELECTOR, summary_selector))

    def toggle_section(self, driver: WebDriver, css_selector: str) -> None:
        button = driver.find_element(By.CSS_SELECTOR, css_selector)
        self.safe_click(driver, button, locator=(By.CSS_SELECTOR, css_selector))
        self.wait_for(driver, lambda d: d.find_element(By.CSS_SELECTOR, css_selector).get_attribute("aria-expanded") == "true")

    def capture(self, driver: WebDriver, viewport: ViewportRun, stem: str) -> str:
        filename = f"{viewport.name}_{len(viewport.screenshots)+1:02d}_{self.slugify(stem)}.png"
        target = self.output_dir / filename
        driver.save_screenshot(str(target))
        viewport.screenshots.append(filename)
        return filename

    def record(
        self,
        viewport: ViewportRun,
        name: str,
        ok: bool,
        details: str = "",
        screenshot: str | None = None,
    ) -> None:
        viewport.checks.append(
            AuditCheck(
                name=name,
                ok=ok,
                details=details,
                screenshot=screenshot,
            )
        )
        if not ok:
            self.report.add_failure(f"{viewport.name}: {name}: {details}")

    def wait_for(self, driver: WebDriver, condition: Any) -> Any:
        return WebDriverWait(driver, WAIT_SECONDS).until(condition)

    def wait_until_text_not_empty(self, driver: WebDriver, element_id: str) -> None:
        self.wait_for(
            driver,
            lambda d: bool(d.find_element(By.ID, element_id).text.strip()),
        )

    def wait_for_text_change(self, driver: WebDriver, by: str, value: str, previous: str) -> None:
        self.wait_for(
            driver,
            lambda d: d.find_element(by, value).text.strip() != previous.strip(),
        )

    def safe_click(
        self,
        driver: WebDriver,
        element: Any,
        *,
        locator: tuple[str, str] | None = None,
    ) -> None:
        self.scroll_to(driver, element)
        if locator is not None:
            self.wait_for(driver, EC.element_to_be_clickable(locator))
        try:
            element.click()
            return
        except ElementClickInterceptedException:
            pass
        driver.execute_script("arguments[0].click();", element)

    def shutdown_driver(self, driver: WebDriver) -> None:
        with contextlib.suppress(Exception):
            driver.quit()
        browser_process = getattr(driver, "_bpm_browser_process", None)
        if browser_process is not None:
            with contextlib.suppress(Exception):
                browser_process.terminate()
            with contextlib.suppress(Exception):
                browser_process.wait(timeout=10)
            log_file = getattr(browser_process, "_bpm_log_file", None)
            if log_file is not None:
                with contextlib.suppress(Exception):
                    log_file.close()

    def scroll_to(self, driver: WebDriver, element: Any) -> None:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
            element,
        )

    def is_present(self, driver: WebDriver, by: str, value: str) -> bool:
        try:
            driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def attr_equals(self, driver: WebDriver, by: str, value: str, attr: str, expected: str) -> bool:
        return driver.find_element(by, value).get_attribute(attr) == expected

    def css_attr(self, d: WebDriver, css: str, attr: str) -> str:
        return d.find_element(By.CSS_SELECTOR, css).get_attribute(attr) or ""

    def text_css(self, driver: WebDriver, css_selector: str) -> str:
        return driver.find_element(By.CSS_SELECTOR, css_selector).text.strip()

    def text_of(self, driver: WebDriver, by: str, value: str) -> str:
        return driver.find_element(by, value).text.strip()

    def page_contains(self, driver: WebDriver, text: str) -> bool:
        return text in driver.page_source

    def dump_export_debug(self, driver: WebDriver, stem: str) -> None:
        ui_state = driver.execute_script(
            """
            const monacoModel = window.monaco?.editor?.getModels?.()?.[0] || null;
            let editorValue = "";
            let parsedDocument = null;
            let parsedFlags = null;
            let parseError = null;
            try {
                editorValue = monacoModel?.getValue?.() || "";
                const mode = document.getElementById("mode")?.value || "json";
                parsedDocument = window.BPMProfilesData?.parseEditorPolicyDocument?.(editorValue, mode) || null;
                parsedFlags = window.BPMProfilesData?.fromEditorValue?.(editorValue, mode) || null;
            } catch (error) {
                parseError = String(error?.message || error);
            }
            const readText = (id) => document.getElementById(id)?.textContent?.trim?.() || "";
            return {
                profileName: document.getElementById("profile-name")?.value || "",
                profileOwner: document.getElementById("profile-owner")?.value || "",
                profileDescription: document.getElementById("profile-description")?.value || "",
                profileType: document.getElementById("profile-type")?.value || "",
                mode: document.getElementById("mode")?.value || "",
                htmlLang: document.documentElement.lang || "",
                status: readText("status"),
                dockStatusText: readText("dock-status-text"),
                validationPreview: readText("validation-preview"),
                exportValidationState: readText("wizard-export-validation-state"),
                exportReadyState: readText("wizard-export-ready-state"),
                editorValue,
                parsedDocument,
                parsedFlags,
                parseError,
            };
            """
        )
        (self.output_dir / f"{stem}_ui_state.json").write_text(
            json.dumps(ui_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        document_payload = ui_state.get("parsedDocument")
        if isinstance(document_payload, dict):
            validate_response = self.debug_validate_request(
                str(ui_state.get("profileType") or ""),
                document_payload,
            )
            (self.output_dir / f"{stem}_validate_response.json").write_text(
                json.dumps(validate_response, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        flags_payload = ui_state.get("parsedFlags")
        if isinstance(flags_payload, dict):
            save_response = self.debug_save_request(ui_state, flags_payload)
            (self.output_dir / f"{stem}_save_response.json").write_text(
                json.dumps(save_response, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def debug_validate_request(self, profile_type: str, document_payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/validate/{quote(profile_type)}",
            json={"document": document_payload},
            timeout=20,
        )
        return self._format_http_debug(response)

    def debug_save_request(self, ui_state: dict[str, Any], flags_payload: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "name": ui_state.get("profileName") or self.profile_name,
            "owner": ui_state.get("profileOwner") or self.profile_owner,
            "description": ui_state.get("profileDescription") or self.profile_description,
            "schema_version": ui_state.get("profileType") or "release-150",
            "flags": flags_payload,
        }
        response = requests.post(
            f"{self.base_url}/api/profiles",
            json=payload,
            timeout=20,
        )
        debug = self._format_http_debug(response)
        debug["request_payload"] = payload
        return debug

    @staticmethod
    def _format_http_debug(response: requests.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except Exception:
            body = response.text
        return {
            "status_code": response.status_code,
            "ok": response.ok,
            "body": body,
        }

    @staticmethod
    def slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((DEFAULT_HOST, 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def maybe_start_server(args: argparse.Namespace, output_dir: Path) -> Any:
    if args.base_url:
        yield
        return

    port = args.port or pick_free_port()
    args.port = port
    env = os.environ.copy()
    env.setdefault("BPM_DATABASE_URL", f"sqlite+aiosqlite:////tmp/bpm-local-chromium-audit-{port}.db")
    previous_cwd = Path.cwd()
    os.chdir(REPO_ROOT)
    os.environ.update(env)
    from app.main import app

    config = uvicorn.Config(
        app=app,
        host=DEFAULT_HOST,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        base_url = f"http://{DEFAULT_HOST}:{port}"
        deadline = time.time() + WAIT_SECONDS
        ready = False
        while time.time() < deadline:
            try:
                probe_url = f"{base_url}/i18n/en.json"
                response = requests.get(probe_url, timeout=10)
                print(f"[audit] server probe {probe_url} -> {response.status_code}", flush=True)
                if response.status_code == 200:
                    ready = True
                    break
            except requests.RequestException:
                print(f"[audit] server probe failed for {base_url}/i18n/en.json", flush=True)
            time.sleep(0.5)
        if not ready:
            raise AuditError(f"Timed out waiting for local BPM server at {base_url}")
        print(f"[audit] server ready at {base_url}", flush=True)
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        os.chdir(previous_cwd)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local Chromium UI audit against the BPM product.",
    )
    parser.add_argument("--base-url", help="Use an existing BPM server instead of starting a local one.")
    parser.add_argument("--port", type=int, default=0, help="Local port for the spawned server.")
    parser.add_argument("--output-dir", help="Directory for screenshots and reports.")
    parser.add_argument(
        "--chromium-binary",
        default=DEFAULT_CHROMIUM,
        help="Path to local Chromium binary.",
    )
    parser.add_argument(
        "--chromedriver-binary",
        default=DEFAULT_CHROMEDRIVER,
        help="Path to matching ChromeDriver binary.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run headed instead of headless.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    args.headless = not args.headed
    if not args.base_url and args.port == 0:
        args.port = pick_free_port()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_ROOT / time.strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with maybe_start_server(args, output_dir):
            runner = UiAuditRunner(args)
            code = runner.run()
            print(f"Audit report: {runner.output_dir / 'report.md'}")
            print(f"Screenshots: {runner.output_dir}")
            return code
    except Exception as exc:
        traceback.print_exc()
        print(f"UI audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
