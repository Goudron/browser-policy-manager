# Documentation Tools

This directory owns documentation-only build, validation, manifest, search-index, localization, and
screenshot adapters. Tools may consume approved BPM contract sources at build time but must not be
imported by the BPM runtime.

`bootstrap_toolchain.py` implements the pinned, repository-local DITA-OT, Temurin JRE, and Python
test-environment bootstrap. Use it through `make setup-docs-toolchain`; it verifies upstream
SHA-256 values, rejects unsafe archives and unsupported platforms, checks tool versions, and runs a
minimal DITA 1.3 HTML5 smoke build.

`validate_metadata.py` validates fixed conditional values and grouped policy/CIS/API identities
against `metadata-vocabulary.json` and the maintained inventories. Run it from the repository root
with `./.venv/bin/python documentation/tools/validate_metadata.py`.

`generate_firefox_policy_skeletons.py` regenerates the committed Firefox policy DITA skeletons,
generated map, and skeleton index from the maintained Firefox policy documentation inventory and
topic model while preserving reviewed regions.

`build_docs.py` is the offline six-locale build and packaging authority behind `make docs-validate`,
`make docs-build`, `make docs-install-dev`, `make docs-reproducibility-check`, `make docs-package`, and
`make docs-package-verify`. It validates metadata, XML, local source links, keys and fragments; runs
the locked DITA-OT HTML5 transform against staged copies of maintained source with explicit
locale/timezone/encoding/temp/output inputs; wraps generated pages in the deterministic accessible
portal shell; copies first-party CSS theme assets into every locale output; generates and validates
`manifest.json`, `ui-target-map.json`, and the current six placeholder search indexes; rejects
source mutation, broken generated links, invalid shell landmarks, active content, inline styles,
manifest/target-map/schema drift, bad artifact references, and absolute workspace-path leaks;
publishes atomically to ignored `documentation/build/site`; compares two clean trees byte for byte;
and emits a deterministic ignored release-candidate archive plus checksum under
`documentation/dist/`. `make docs-install-dev` promotes the validated local build into ignored
`app/documentation/site` for maintainer review through `make dev`; release package extraction remains
separate.
