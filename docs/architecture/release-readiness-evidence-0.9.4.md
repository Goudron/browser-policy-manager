# BPM 0.9.4 Release-Readiness Evidence

Date: 2026-08-10

Status: **Accepted for reviewed commit and CI handoff; this record is not a release, tag, or push.**

Backlog item: `BPM094-M12-08`

## Scope

This closeout replaces the provisional 0.9.4 changelog status with verified
outcomes. It links maintained source records only. Local build output, reports,
caches, installed sites, browser artifacts, and other ignored evidence are not
release authorities and are not modified by this task.

## Verified evidence

| Acceptance area | Maintained evidence | Verified outcome |
| --- | --- | --- |
| Current release ownership | [Current system map](current-system-map.md), [release/incubation boundary](release-incubation-development-boundary-0.9.4.md), and [current artifact owners](../../tests/fixtures/current_artifact_owners_0_9_4.json) | The current target is 0.9.4. Release delivery, optional AI incubation, development tooling, and historical ownership are explicitly separated. |
| Dependency and browser inputs | [Dependency currency decision](dependency-currency-0.9.4.md) and [dependency/SBOM audit](dependency-audit-sbom-0.9.4.md) | Approved dependency/toolchain updates and the checksum-verified Firefox Release 153.0.1, ESR 140.13.0esr, and geckodriver 0.37.1 inputs are recorded by their owners. |
| Documentation and PDF acceptance | [Editorial/PDF release review](../../documentation/config/documentation-editorial-pdf-release-review-0.9.4.json) | The review is `accepted`, has no blocking findings, covers every User, Administrator, Firefox Policy, and CIS guide family in all six locales, and records passing DITA/site, PDF build/verification, delivery/package, reproducibility, and final documentation-release checks. |
| PDF optimization/reproducibility | [PDF pipeline benchmark](../../documentation/config/pdf-pipeline-optimization-benchmark-0.9.4.json) | The final cold build rebuilt 12 PDF pairs, the warm build reused 12 verified pairs, all 12 PDFs matched the baseline SHA-256, and cache-bypass reproducibility matched the 12 PDFs plus manifest. |
| README boundary | [README](../../README.md) and [epic-backlog creation runbook](../epic-backlog-creation-runbook.md) | README is version-neutral: it contains no BPM release-number anchor, release-history entry, target-version plan, or completion claim. |
| Documentation history and index | [Documentation index](../docs-index.md) and [docs-index contract](../../tests/contract/docs/general/test_docs_index.py) | Each maintained `docs/` record is indexed exactly once with an existing link. Historical/versioned records remain traceable, while the index states that an `active` status does not make an older version the current target. |

## Reconfirmed M11 acceptance

The M11 editorial/PDF review is the release-blocking documentation authority for
this closeout. Its accepted record confirms the six-locale review and the final
`make docs-release-check` result of 1029 passing documentation contracts after
remediation. Its PDF evidence records clean independent reproducibility across
24 locale-guide build phases and all 12 PDFs plus the manifest.

## History and release boundary

The 0.9.3 changelog section and versioned technical records are retained as
historical evidence. They are not rewritten as 0.9.4 outcomes. Conversely, no
current owner, README surface, or changelog status presents new work as 0.9.3;
the active product target is 0.9.4.

## Remaining handoff

This record closes only `BPM094-M12-08`. `BPM094-M12-09` must still make the
reviewed commit, and `BPM094-M12-10` must still push it and observe required CI
to a terminal state. A failed or incomplete handoff reopens release readiness
for maintainer direction.
