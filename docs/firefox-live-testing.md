# Firefox Live Testing

These tests run against a real Firefox binary without touching your everyday browser profile.

## Isolation model

- Firefox runs in `headless` mode by default.
- Every test creates its own temporary Firefox profile.
- The harness reuses a project-local Firefox install under `.bpm-test-browsers/`.
- Enterprise policies are written into that isolated project-local Firefox as `distribution/policies.json`.
- Your normal Firefox profile and settings are not reused.

## Project-local sandbox

The live harness looks for browser binaries in this hidden project folder first:

- `.bpm-test-browsers/firefox/firefox/firefox`
- `.bpm-test-browsers/geckodriver/geckodriver`

If you prefer explicit paths, you can still use:

- `BPM_FIREFOX_BIN`
- `BPM_GECKODRIVER_BIN`

## Quick setup

Linux helper:

```bash
bash tools/setup_firefox_live_browsers.sh release
```

Then run:

```bash
.venv/bin/pytest -m firefox_live -q
```

The default `pytest` run excludes `firefox_live` and `firefox_live_amo`, so use
the explicit marker command above when you want the real-browser suite.

## AMO canary

The main `firefox_live` suite stays deterministic and avoids dependencies on external add-on services.

Real AMO extension-install coverage lives in a separate canary suite:

```bash
.venv/bin/pytest -m firefox_live_amo -q
```

This currently verifies that Firefox can force-install `uBlock Origin` from AMO through
`ExtensionSettings`.

## Current live scenarios

- `BlockAboutConfig`: Firefox loads the policy and blocks `about:config`.
- `WebsiteFilter`: Firefox loads the policy and blocks a local test page.
- `Homepage`: Firefox loads the policy and updates runtime startup preferences inside the live browser.
- `Preferences`: Firefox applies and locks a managed runtime preference.
- `DisablePrivateBrowsing`: Firefox disables private browsing surfaces through policy.
- `RequestedLocales`: Firefox updates runtime locale preferences and locale service state.
- `OverrideFirstRunPage`: Firefox overrides the first-run welcome target and disables default welcome flow.
- `DisableAppUpdate`: Firefox hides managed update controls in `about:preferences`.
- `Proxy`: Firefox routes real HTTP traffic through a managed proxy and updates proxy prefs.
- `Certificates.Install`: Firefox trusts a managed CA and successfully opens a local HTTPS page that otherwise fails certificate validation.

## Current AMO scenario

- `ExtensionSettings` + AMO: Firefox force-installs `uBlock Origin` from
  `https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi`
  and the test confirms the installed add-on via Firefox `AddonManager`.

## CI jobs

- `.github/workflows/ci.yml`
  Runs the main deterministic `firefox_live` suite after the regular lint/unit test job.
- `.github/workflows/firefox-live.yml`
  Runs the same deterministic live suite on a nightly schedule.
- `.github/workflows/firefox-live-amo.yml`
  Runs the separate AMO canary suite on a nightly schedule and by manual dispatch.
