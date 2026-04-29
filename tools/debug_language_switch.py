#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.run_local_chromium_ui_audit import UiAuditRunner, ViewportRun, maybe_start_server, pick_free_port


class DebugArgs:
    base_url = None
    port = pick_free_port()
    output_dir = str(Path("artifacts/local_chromium_ui_audit/debug_language"))
    chromium_binary = "/snap/bin/chromium"
    chromedriver_binary = "/snap/bin/chromium.chromedriver"
    headed = False
    headless = True


def main() -> int:
    args = DebugArgs()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with maybe_start_server(args, output_dir):
        runner = UiAuditRunner(args)
        viewport = ViewportRun(name="debug", width=1440, height=2200)
        driver = runner.create_driver(viewport.width, viewport.height, mobile=False)
        try:
            runner.bootstrap_browser(driver)
            runner.open_and_wait(driver, "/profiles/new")
            runner.capture(driver, viewport, "before")
            print("initial", driver.execute_script("return {lang: document.documentElement.lang, mode: document.documentElement.dataset.langMode, select: document.getElementById('lang').value};"))
            runner.apply_language(driver, viewport, "en")
            print("after_en", driver.execute_script("return {lang: document.documentElement.lang, mode: document.documentElement.dataset.langMode, select: document.getElementById('lang').value, local: window.localStorage.getItem('bpm-lang-mode')};"))
            print("console_en", json.dumps(driver.get_log("browser"), ensure_ascii=False))
            runner.apply_language(driver, viewport, "ru")
            print("after_ru", driver.execute_script("return {lang: document.documentElement.lang, mode: document.documentElement.dataset.langMode, select: document.getElementById('lang').value, local: window.localStorage.getItem('bpm-lang-mode')};"))
            print("console_ru", json.dumps(driver.get_log("browser"), ensure_ascii=False))
            before_click = driver.execute_script(
                """
                const button = document.querySelector('[data-scenario-key="shared_devices"]');
                return {aria: button?.getAttribute('aria-pressed'), className: button?.className};
                """
            )
            print("scenario_before", before_click)
            runner.click_css(driver, '[data-scenario-key="shared_devices"]')
            after_click = driver.execute_script(
                """
                const button = document.querySelector('[data-scenario-key="shared_devices"]');
                return {aria: button?.getAttribute('aria-pressed'), className: button?.className};
                """
            )
            print("scenario_after", after_click)
            print("console_after_click", json.dumps(driver.get_log("browser"), ensure_ascii=False))
            runner.capture(driver, viewport, "after")
            return 0
        finally:
            runner.shutdown_driver(driver)


if __name__ == "__main__":
    raise SystemExit(main())
