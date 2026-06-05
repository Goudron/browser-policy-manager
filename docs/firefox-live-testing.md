# Firefox Live Testing

These tests run against a real Firefox binary without touching your everyday browser profile.

They validate the live Firefox runtime behavior of exported `policies.json` documents. They do
not drive the BPM `/profiles` UI, wizard flow, or Chromium product audit path.

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

## Sandbox lifecycle

Treat `.bpm-test-browsers/` as disposable local state:

- it is intentionally ignored by git;
- it can be several hundred megabytes after Firefox and geckodriver are installed;
- it is safe to remove when you need to reclaim disk space or force a fresh browser install;
- it should not be copied into docs, screenshots, release bundles, or frontend vendor assets.

Use the explicit cleanup target when you want to remove the sandbox together with other ignored
local artifacts:

```bash
make clean-local-artifacts
```

After cleanup, run `make setup-firefox-live-browsers` again before the next live Firefox suite.
For a quick local size check without deleting anything, run `make repo-health` and review the
`Ignored Local Artifacts` section.

## Quick setup

Linux helper:

```bash
make setup-firefox-live-browsers
```

The helper downloads the latest Linux Firefox Release build into `.bpm-test-browsers/` and prints
the installed Firefox and geckodriver versions at the end. For the current BPM release channel, the
expected target is Firefox `150.x`.

To install the ESR sandbox instead, pass the channel through Make:

```bash
make setup-firefox-live-browsers FIREFOX_CHANNEL=esr
```

Then run:

```bash
make test-firefox-live
```

The default `pytest` run excludes `firefox_live` and `firefox_live_amo`, so use
the explicit Make target above when you want the deterministic real-browser suite.

## AMO canary

The main `firefox_live` suite stays deterministic and avoids dependencies on external add-on services.

Real AMO extension-install coverage lives in a separate canary suite:

```bash
make test-firefox-live-amo
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

These scenarios intentionally focus on the Firefox policy engine itself:

- the harness renders a canonical `policies.json`
- writes it into the isolated Firefox sandbox
- launches real Firefox with Selenium
- verifies either live browser behavior or runtime Firefox state

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
