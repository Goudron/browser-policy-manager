# BPM 0.9.4 Dependency Audit and CycloneDX Evidence

Date: 2026-08-05

Status: **Active — `BPM094-M10-03`.**

## Decision

Mandatory CI treats dependency security as a separate fail-closed release gate. It
does not modify declared dependencies, lock files, or source: it only resolves
clean temporary Python environments, reads the npm lock file, queries advisory
services, and writes transient review evidence.

The gate has three independently reviewable scopes:

| Scope | Resolved input | Vulnerability check | SBOM evidence |
| --- | --- | --- | --- |
| Python base | Clean temporary environment after `pip install .` | `pip check`, then `pip-audit --strict` over its exact generated requirements | `python-base.cdx.json` |
| Python optional | Clean temporary environment after `pip install ".[dev,postgres,ai]"` | `pip check`, then `pip-audit --strict` over its exact generated requirements | `python-all-extras.cdx.json` |
| npm | Committed `package-lock.json`, with `npm ci` before the gate | `npm audit --package-lock-only` | `npm.cdx.json` from `cyclonedx-npm --package-lock-only` |

There is intentionally no Python lock file in this project. The two generated
`python-*-resolved-requirements.txt` files are therefore evidence of the exact
environments actually audited, rather than an attempt to claim that the
declaration ranges are a lock. npm's committed lock is its authority.
`browser-policy-manager` itself is retained as the CycloneDX root component but
is omitted from `pip-audit`: it is local first-party source, not a PyPI
distribution against which that service can query advisories.

`pip-audit==2.10.1`, `cyclonedx-bom==7.3.1`, and
`@cyclonedx/cyclonedx-npm@6.0.0` are exact, maintained audit/SBOM tool pins.
The temporary Python environments bootstrap `pip==26.2.1` before resolution;
this avoids treating the older venv seed package as an unowned security
exception. CycloneDX output uses reproducible JSON and validates against
specification 1.6.

## Failure and Exception Policy

Any known dependency advisory fails the job. The audit never runs `pip-audit
--fix`, `npm audit fix`, a package-manager update, or a lockfile-writing command.

The checked-in `tools/dependency_audit_suppressions.json` is empty. A future
Python exception must have exactly these non-empty fields:

- advisory ID;
- technical rationale;
- accountable owner; and
- ISO `expires_on` date that has not elapsed.

The runner rejects malformed and expired entries. npm has no safe per-advisory
suppression path in this workflow, so its exception list must remain empty;
an npm advisory must be remediated rather than hidden.

## Operation and Retention

After installing the development audit tools and running `npm ci`, use:

```bash
make dependency-audit
```

CI runs the same command in `dependency-audit`, with pip and npm caches, a
15-minute timeout, and a 14-day uploaded artifact. Local and CI outputs are
under `artifacts/dependency-audit/`, which is ignored by Git. They are evidence
for one resolution date and must not be committed as a stale release claim.

The 2026-08-05 full local run found zero vulnerabilities in 40 base Python
dependencies, 135 all-extras Python dependencies, and 184 npm SBOM components;
the corresponding CycloneDX component counts were 41, 137, and 184. These
numbers are point-in-time evidence, not a promise about future registry or
advisory data.
