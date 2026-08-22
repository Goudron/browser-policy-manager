"""Focused Chromium proof for BPM096-M9-03 certificate reference editing."""

from __future__ import annotations

import json
import uuid

import pytest
import requests

from tests.browser.harness import (
    build_chromium_driver,
    close_chromium_driver,
    scoped_test_app_server,
)

pytestmark = [
    pytest.mark.browser_ui,
    pytest.mark.usefixtures("browser_test_context", "browser_product_server"),
]


def _seed_flags() -> dict[str, object]:
    return {
        "Certificates": {
            "Install": ["/etc/firefox/company-root.pem", "C:\\Corp\\client-chain.der"],
            "ImportEnterpriseRoots": True,
        },
        "Authentication": {
            "SPNEGO": ["intranet.example"],
            "AllowNonFQDN": {"fileserver": True},
            "Locked": True,
        },
        "SecurityDevices": {
            "Add": {"Corporate token": "C:\\Program Files\\Vendor\\pkcs11.dll"},
            "Delete": ["Legacy token"],
        },
    }


def _create_profile(base_url: str) -> dict[str, object]:
    created = requests.post(
        f"{base_url}/api/profiles/prepare/new",
        json={
            "name": f"M9-03 certificates {uuid.uuid4().hex}",
            "target_schema_id": "release-153",
            "starter_id": "blank",
            "cis_baseline_id": "none",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
        timeout=10,
    )
    assert created.status_code == 201, created.text
    profile = created.json()
    saved = requests.patch(
        f"{base_url}/api/profiles/{profile['id']}",
        json={"flags": _seed_flags(), "expected_revision": profile["revision"]},
        timeout=10,
    )
    assert saved.status_code == 200, saved.text
    return saved.json()


def _create_prepared_provenance_profile(base_url: str) -> dict[str, object]:
    created = requests.post(
        f"{base_url}/api/profiles/prepare/new",
        json={
            "name": f"M9-04 certificate provenance {uuid.uuid4().hex}",
            "target_schema_id": "release-153",
            "starter_id": "basic_corporate",
            "cis_baseline_id": "cis_l1",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
        timeout=10,
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_certificate_device_lists_edit_save_reopen_and_export_without_file_io():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    keys = pytest.importorskip("selenium.webdriver.common.keys")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        profile = _create_profile(base_url)
        profile_id = profile["id"]
        driver = build_chromium_driver()
        wait = ui.WebDriverWait(driver, 20)
        try:
            driver.get(f"{base_url}/profiles/{profile_id}/edit?step=certificates_trust")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-stepper")))
            # The certificate list itself lives in a non-first wizard panel;
            # activate its normal keyboard/button owner before interacting.
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(by.By.CSS_SELECTOR, '.wizard-step[data-step="4"]'),
            )
            wait.until(
                ec.visibility_of_element_located((by.By.ID, "wizard-certificate-install-reference"))
            )
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "certificates_trust"
                )
            )
            assert (
                driver.execute_script(
                    "return document.querySelectorAll('#wizard-step-4 input[type=file]').length;"
                )
                == 0
            )
            initial_state = driver.execute_script(
                """
                return {
                  certificateRows: document.querySelectorAll('#wizard-certificate-install-list [role=listitem]').length,
                  certificateEmptyHidden: document.getElementById('wizard-certificate-install-empty').hidden,
                  trustChoice: document.getElementById('wizard-certificate-enterprise-roots').value,
                  monacoText: document.querySelector('.monaco-editor')?.innerText || '',
                  embeddedFlags: JSON.parse(document.getElementById('profiles-initial-profile')?.textContent || '{}').flags || {},
                  provenance: document.getElementById('wizard-certificate-provenance-status')?.textContent.trim(),
                  runtimeStatus: document.getElementById('status')?.textContent || '',
                };
                """
            )
            assert initial_state["certificateRows"] == 2, json.dumps(initial_state, indent=2)
            assert "Manual change" in initial_state["provenance"]

            certificate_reference = driver.find_element(
                by.By.ID, "wizard-certificate-install-reference"
            )
            certificate_reference.send_keys("/srv/firefox/new-root.pem")
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(
                    by.By.CSS_SELECTOR, "#wizard-certificate-install-form button[type=submit]"
                ),
            )
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "#wizard-certificate-install-list [role=listitem]"
                        )
                    )
                    == 3
                )
            )

            # Edit the newly added reference in place; no file selection or
            # filesystem access is involved in this UI action.
            new_row = driver.find_elements(
                by.By.CSS_SELECTOR, "#wizard-certificate-install-list [role=listitem]"
            )[-1]
            driver.execute_script(
                "arguments[0].click();",
                new_row.find_elements(by.By.CSS_SELECTOR, ".wizard-managed-list-actions button")[
                    -1
                ],
            )
            edit_input = new_row.find_element(by.By.CSS_SELECTOR, "input.soft-input")
            edit_input.send_keys(keys.Keys.CONTROL, "a")
            edit_input.send_keys("/srv/firefox/final-root.pem")
            driver.execute_script(
                "arguments[0].click();",
                new_row.find_elements(by.By.CSS_SELECTOR, ".wizard-managed-list-actions button")[0],
            )

            auth_field = driver.find_element(by.By.ID, "wizard-certificate-authentication-field")
            auth_field.find_element(by.By.CSS_SELECTOR, 'option[value="NTLM"]').click()
            auth_host = driver.find_element(by.By.ID, "wizard-certificate-authentication-host")
            auth_host.send_keys("ntlm.example")
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(
                    by.By.CSS_SELECTOR,
                    "#wizard-certificate-authentication-form button[type=submit]",
                ),
            )

            device_name = driver.find_element(by.By.ID, "wizard-security-device-name")
            device_path = driver.find_element(by.By.ID, "wizard-security-device-path")
            device_name.send_keys("Linux token")
            device_path.send_keys("/usr/lib64/pkcs11/vendor.so")
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(
                    by.By.CSS_SELECTOR, "#wizard-security-device-add-form button[type=submit]"
                ),
            )
            delete_name = driver.find_element(by.By.ID, "wizard-security-device-delete-name")
            delete_name.send_keys("Retired token")
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(
                    by.By.CSS_SELECTOR, "#wizard-security-device-delete-form button[type=submit]"
                ),
            )

            driver.execute_script("arguments[0].click();", driver.find_element(by.By.ID, "save"))
            wait.until(
                lambda current_driver: (
                    "signal-chip--saved"
                    in current_driver.find_element(by.By.ID, "workspace-signal").get_attribute(
                        "class"
                    )
                )
            )
            saved = requests.get(f"{base_url}/api/profiles/{profile_id}", timeout=10)
            exported = requests.get(
                f"{base_url}/api/export/profiles/{profile_id}/firefox/policies.json", timeout=10
            )
            assert saved.status_code == exported.status_code == 200
            flags = saved.json()["flags"]
            assert flags["Certificates"]["Install"] == [
                "/etc/firefox/company-root.pem",
                "C:\\Corp\\client-chain.der",
                "/srv/firefox/final-root.pem",
            ]
            assert flags["Authentication"]["NTLM"] == ["ntlm.example"]
            assert flags["SecurityDevices"]["Add"] == {
                "Corporate token": "C:\\Program Files\\Vendor\\pkcs11.dll",
                "Linux token": "/usr/lib64/pkcs11/vendor.so",
            }
            assert flags["SecurityDevices"]["Delete"] == ["Legacy token", "Retired token"]
            assert exported.json() == {"policies": flags}

            driver.refresh()
            wait.until(
                lambda current_driver: (
                    len(
                        current_driver.find_elements(
                            by.By.CSS_SELECTOR, "#wizard-certificate-install-list [role=listitem]"
                        )
                    )
                    == 3
                )
            )
            rendered = driver.execute_script(
                """
                return {
                  certificateRows: document.querySelectorAll('#wizard-certificate-install-list [role=listitem]').length,
                  authRows: document.querySelectorAll('#wizard-certificate-authentication-list [role=listitem]').length,
                  deviceRows: document.querySelectorAll('#wizard-security-device-add-list [role=listitem]').length,
                  rawFallback: document.getElementById('wizard-security-devices-raw').hidden,
                  clientSelection: document.getElementById('wizard-certificate-client-selection-status').textContent.trim(),
                };
                """
            )
            assert rendered["certificateRows"] == 3
            assert rendered["authRows"] >= 3
            assert rendered["deviceRows"] == 2
            assert rendered["rawFallback"] is True
            assert rendered["clientSelection"]
        finally:
            close_chromium_driver(driver)


def test_certificate_step_shows_baseline_cis_sources_and_final_review_jumps_to_its_owner():
    by = pytest.importorskip("selenium.webdriver.common.by")
    ec = pytest.importorskip("selenium.webdriver.support.expected_conditions")
    ui = pytest.importorskip("selenium.webdriver.support.ui")

    with scoped_test_app_server() as base_url:
        profile = _create_prepared_provenance_profile(base_url)
        assert profile["certificate_provenance"]["paths"] == {
            "/Authentication/NTLM": "cis",
            "/Certificates/ImportEnterpriseRoots": "baseline",
        }
        # The selected CIS layer has unrelated manual-review decisions.  The
        # certificate owner must not promote that benchmark claim, while its
        # own zero-count message remains specific to certificate paths.
        assert profile["baseline_provenance"]["cis"]["display_status"] == "manual-review"
        driver = build_chromium_driver()
        # The product server and all data are local and deterministic here;
        # bound only this focused M9-04 check to the interactive browser gate.
        wait = ui.WebDriverWait(driver, 10)
        try:
            driver.get(f"{base_url}/profiles/{profile['id']}/edit?step=certificates_trust")
            wait.until(ec.presence_of_element_located((by.By.ID, "wizard-stepper")))
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(by.By.CSS_SELECTOR, '.wizard-step[data-step="4"]'),
            )
            wait.until(
                lambda current_driver: current_driver.find_element(
                    by.By.ID, "wizard-certificate-provenance-status"
                ).text.strip()
            )
            attribution = driver.find_element(by.By.ID, "wizard-certificate-provenance-status").text
            cis_status = driver.find_element(by.By.ID, "wizard-certificate-cis-status").text
            assert "Starter baseline" in attribution
            assert "CIS layer" in attribution
            assert cis_status == "No certificate-specific CIS review is currently required."

            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(by.By.CSS_SELECTOR, '.wizard-step[data-step="8"]'),
            )
            jump = wait.until(
                ec.presence_of_element_located(
                    (by.By.ID, "wizard-export-summary-certificates-jump")
                )
            )
            driver.execute_script("arguments[0].click();", jump)
            wait.until(
                lambda current_driver: (
                    current_driver.find_element(
                        by.By.CSS_SELECTOR, ".wizard-step[aria-current=step]"
                    ).get_attribute("data-step-id")
                    == "certificates_trust"
                )
            )
            assert driver.execute_script(
                "return document.getElementById('wizard-step-4-attribution') === document.activeElement "
                "|| document.activeElement.closest('#wizard-step-4') !== null;"
            )
        finally:
            close_chromium_driver(driver)
