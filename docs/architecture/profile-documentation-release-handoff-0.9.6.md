# BPM 0.9.6 profile documentation release handoff

Date: 2026-08-21

Backlog item: `BPM096-M10-09`

Status: completed. This record closes the documentation release, package, and
development-install handoff for the delivered BPM 0.9.6 profile workflow. It
uses the already verified M10-07 site candidate and M10-08 PDF delivery as
inputs; it does not start a development server or change generated artifacts
by hand.

## Authoritative release gate

`make docs-release-check` was run once after the current source, site, and PDF
owners had completed. The owner first built and validated a disposable DITA
candidate: source validation and candidate validation completed `2/2`, and
each HTML5 locale completed in order: `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`. The editorial release gate accepted all six locales. The final
documentation-contract suite completed successfully: `1002 passed in 42.78s`.

No source, locale, manifest, search, API-example, or editorial drift was
reported, so no earlier owner stage needed to be re-opened.

## Package and integrity

The owner commands completed in this order:

| Command | Result |
| --- | --- |
| `make docs-package` | Completed `4/4`: source validation, artifact tree, archive SHA-256 verification, and atomic promotion. The artifact is `documentation/dist/bpm-documentation-0.9.6.tar.gz`. |
| `make docs-package-verify` | Passed with archive SHA-256 `2e53f3bc8caf61e476fd99c100105ea82a1331ca8f1fde9a3d100888b16c5fac`. |
| `make docs-install-dev` | Completed site publication `3/3` and atomic development-site installation `2/2` at `app/documentation/site`. |

The package and installation were made only through their owners; no archive,
site tree, PDF, manifest, or checksum was manually edited.

## Installed-version proof and boundary

The product version is read from `pyproject.toml`, whose active value is
`0.9.6`. The installed `app/documentation/.site-dev-install.json` records
`bpm_version: "0.9.6"`; the installed site manifest records both
`bpm_version` and `documentation_version` as `0.9.6`. The visible portal
header on every installed locale root (`en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`) renders `v0.9.6`.

`make docs-install-dev` only writes the static development-site artifact. No
`make dev`, web server, or other development server was started by this task.

## Follow-up verification

After this authored evidence and its index registration were recorded, the
maintained docs-index and current-artifact-ownership contract pair passed
`7/7`. It validates the evidence registration without rebuilding or editing
the already accepted generated outputs.
