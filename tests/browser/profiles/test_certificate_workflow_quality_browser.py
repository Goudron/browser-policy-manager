"""BPM096-M9-05 Chromium proof for certificate/trust ownership and safety."""

from __future__ import annotations

import uuid

import pytest
import requests

from tests.browser.harness import (
    build_chromium_driver,
    close_chromium_driver,
    scoped_test_app_server,
)
from tests.browser.profiles.pages import load_locale_catalog, set_locale

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]


_ACTIVE_SCHEMAS = ("release-153", "esr-153.0", "esr-140.13", "esr-115.39")


def _certificate_flags() -> dict[str, object]:
    return {
        "Certificates": {
            "Install": ["/etc/firefox/company-root.pem"],
            "ImportEnterpriseRoots": True,
        },
        "Authentication": {
            "SPNEGO": ["intranet.example"],
            "Delegated": ["delegate.example"],
            "NTLM": ["ntlm.example"],
            "AllowNonFQDN": {"fileserver": True},
            "AllowProxies": {"proxy.example": True},
            "Locked": True,
            "PrivateBrowsing": False,
        },
        "SecurityDevices": {
            "Add": {"Corporate token": "/usr/lib/pkcs11/corporate.so"},
            "Delete": ["Legacy token"],
        },
        "DisableSecurityBypass": {"InvalidCertificate": False},
        "WindowsSSO": True,
        "Preferences": {
            "security.enterprise_roots.enabled": {
                "Status": "locked",
                "Type": "boolean",
                "Value": True,
            }
        },
    }


def _create_profile(base_url: str, schema_id: str, flags: dict[str, object]) -> int:
    response = requests.post(
        f"{base_url}/api/profiles",
        json={
            "name": f"M9-05 certificates {schema_id} {uuid.uuid4().hex}",
            "schema_version": schema_id,
            "flags": flags,
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


def _assert_document_fits(driver) -> None:
    metrics = driver.execute_script(
        """
        return {
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
        };
        """
    )
    assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, metrics


def test_certificate_step_is_the_only_runtime_owner_in_all_schemas_and_locales():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    select_module = pytest.importorskip("selenium.webdriver.support.select")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            last_profile_id = 0
            for schema_id in _ACTIVE_SCHEMAS:
                last_profile_id = _create_profile(base_url, schema_id, _certificate_flags())
                driver.set_window_size(1280, 960)
                driver.get(f"{base_url}/profiles/{last_profile_id}/edit?step=certificates_trust")
                wait.until(
                    ec.presence_of_element_located(
                        (by.By.ID, "wizard-certificate-install-reference")
                    )
                )
                wait.until(
                    lambda current_driver: (
                        current_driver.find_element(
                            by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                        ).get_attribute("data-step-id")
                        == "certificates_trust"
                    )
                )
                surface = driver.execute_script(
                    """
                    const step = document.getElementById("wizard-step-4");
                    const outside = Array.from(document.querySelectorAll(
                      '[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                      + '#wizard-certificate-system-trust, '
                      + '[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                      + '#wizard-certificate-enterprise-roots, '
                      + '[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                      + '#wizard-certificate-error-bypass, '
                      + '[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                      + '#wizard-certificate-windows-sso, '
                      + '[data-wizard-step-id]:not([data-wizard-step-id="certificates_trust"]) '
                      + '#wizard-certificate-entra-sso'
                    ));
                    return {
                      active: step.classList.contains("is-active"),
                      files: step.querySelectorAll('input[type="file"]').length,
                      status: [
                        "wizard-certificate-trust-schema-status",
                        "wizard-certificate-provenance-status",
                        "wizard-certificate-cis-status",
                      ].map((id) => {
                        const element = document.getElementById(id);
                        return [element?.getAttribute("role"), element?.getAttribute("aria-live")];
                      }),
                      formLabels: [
                        "wizard-certificate-install-reference",
                        "wizard-certificate-authentication-field",
                        "wizard-certificate-authentication-host",
                        "wizard-security-device-name",
                        "wizard-security-device-path",
                        "wizard-security-device-delete-name",
                      ].every((id) => Boolean(document.getElementById(id)?.closest("label"))),
                      outside: outside.length,
                      entraHidden: document.getElementById("wizard-certificate-entra-row").hidden,
                    };
                    """
                )
                assert surface["active"] is True
                assert surface["files"] == 0
                assert surface["status"] == [["status", "polite"]] * 3
                assert surface["formLabels"] is True
                assert surface["outside"] == 0
                assert surface["entraHidden"] is (schema_id == "esr-115.39")

            driver.set_window_size(320, 900)
            for locale in ("ru", "de", "zh-CN", "fr", "es-ES", "en"):
                catalog = load_locale_catalog(locale)
                set_locale(
                    driver,
                    wait,
                    ui,
                    locale=locale,
                    expected_text=catalog["profiles.wizard_step_four"],
                )
                assert (
                    driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "certificates_trust"
                )
                _assert_document_fits(driver)

            # The last (ESR 115) profile must stay on its real owner while a
            # locale change is applied; no hidden 153-only Entra control leaks in.
            assert last_profile_id
            assert (
                driver.find_element(by.By.ID, "wizard-certificate-entra-row").is_displayed()
                is False
            )
            select_module.Select(driver.find_element(by.By.ID, "theme")).select_by_value("dark")
            _assert_document_fits(driver)
        finally:
            close_chromium_driver(driver)


def test_certificate_strings_are_rendered_as_text_and_invalid_typed_input_is_non_mutating():
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    hostile = '<img src=x onerror="alert(91)"> certificate.pem'
    hostile_device = '<svg onload="alert(92)"> token'
    flags = {
        "Certificates": {"Install": [hostile]},
        "Authentication": {"SPNEGO": [hostile]},
        "SecurityDevices": {"Add": {hostile_device: "/usr/lib/pkcs11/corporate.so"}},
    }
    with scoped_test_app_server() as base_url:
        profile_id = _create_profile(base_url, "release-153", flags)
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "window.__m9CertificateAlerts = 0; window.alert = () => { window.__m9CertificateAlerts += 1; };",
                },
            )
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=certificates_trust")
            wait.until(
                lambda current_driver: current_driver.execute_script(
                    "return document.querySelectorAll('#wizard-certificate-install-list [role=listitem]').length === 1;"
                )
            )
            rendered = driver.execute_script(
                """
                const selectors = [
                  "#wizard-certificate-install-list",
                  "#wizard-certificate-authentication-list",
                  "#wizard-security-device-add-list",
                ];
                return {
                  alerts: window.__m9CertificateAlerts,
                  dangerousElements: selectors.flatMap((selector) => Array.from(
                    document.querySelectorAll(`${selector} img, ${selector} svg, ${selector} script`)
                  )).length,
                  certificateText: document.getElementById("wizard-certificate-install-list").innerText,
                  authenticationText: document.getElementById("wizard-certificate-authentication-list").innerText,
                  deviceText: document.getElementById("wizard-security-device-add-list").innerText,
                  files: document.querySelectorAll('#wizard-step-4 input[type="file"]').length,
                  certificateRows: document.querySelectorAll('#wizard-certificate-install-list [role=listitem]').length,
                };
                """
            )
            assert rendered["alerts"] == 0
            assert rendered["dangerousElements"] == 0
            assert rendered["certificateText"].find(hostile) >= 0
            assert rendered["authenticationText"].find(hostile) >= 0
            assert rendered["deviceText"].find(hostile_device) >= 0
            assert rendered["files"] == 0

            submitted_value = driver.execute_script(
                """
                const input = document.getElementById("wizard-certificate-install-reference");
                const form = document.getElementById("wizard-certificate-install-form");
                input.value = " leading-whitespace.pem";
                form.requestSubmit();
                return input.value;
                """
            )
            assert submitted_value == " leading-whitespace.pem"
            after = driver.execute_script(
                """
                return {
                  rows: document.querySelectorAll('#wizard-certificate-install-list [role=listitem]').length,
                  alerts: window.__m9CertificateAlerts,
                };
                """
            )
            assert after["rows"] == rendered["certificateRows"]
            assert after["alerts"] == 0
        finally:
            close_chromium_driver(driver)
