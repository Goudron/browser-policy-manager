# BPM documentation delivery layout

This directory is the future delivery location for BPM documentation PDFs. The authoritative,
versioned layout contract is
[`documentation/config/future-distribution-documentation-layout-0.9.3.json`](../../documentation/config/future-distribution-documentation-layout-0.9.3.json).

The generator atomically promotes exactly one version directory only after it has verified the
twelve declared PDFs, `manifest.json`, `checksums.sha256`, and `NOTICE.txt`. Do not add files
manually. Rebuild and verify with `make docs-pdf-build`, `make docs-pdf-verify`,
`make docs-pdf-deliver`, and `make docs-pdf-delivery-verify`.

The intended delivery shape is:

```text
distributions/documentation/<bpm-version>/
├── manifest.json
├── checksums.sha256
├── NOTICE.txt
└── pdf/
    ├── en/
    │   ├── browser-policy-manager-user-guide-en-<bpm-version>.pdf
    │   └── browser-policy-manager-administrator-guide-en-<bpm-version>.pdf
    └── … five remaining supported locales
```

The full locale matrix and ownership, rebuild and removal rules are in the contract.
