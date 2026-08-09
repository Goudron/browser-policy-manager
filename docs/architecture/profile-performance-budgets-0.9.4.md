# BPM 0.9.4 Profile Performance Budgets

## Purpose And Scope

`make profile-performance-gate` is the M2-04 executable anti-regression
guardrail for the six profile routes and their selected unit, API, and rendered
UI-contract layers. It is not a replacement for the broader M8 and M12 test,
browser, coverage, package-install, or CI critical-path gates.

The authoritative data is
`tools/profile_performance_budgets_0_9_4.json`. Its original measurements
were produced on 2026-08-04; M12-07 then replaced the stale per-layer timing
references with two clean, matching 2026-08-10 runs after the guided-route
payload reduction. The JSON reports remain deliberately ignored local
evidence, while the reviewed budget manifest is versioned source.

## Comparable Measurement Rule

The gate always creates a fresh ignored-local report under
`artifacts/performance/gate/`. It requires all six routes,
the exact in-memory one-profile fixture, one excluded warm-up, three measured
requests, sample-derived medians, and successful measured test layers. It also
records the host/process/cache/git manifest through the M2-03 harness.

Supplying `--report` is inspection only. It cannot be combined with
`--enforce-release-targets`; a checked-in, edited, stale, or partial report is
therefore never release evidence.

## Variance And Integrity

Wall-clock ceilings use the reviewed reference median multiplied by 1.25 plus
0.5 seconds. This accommodates ordinary workstation and CI noise without
hiding a material regression. Response bytes, route set, fixture, warm-up and
sample count, query/validation counters, collected-test floors, test source
SHA-256 values, and test exit status are exact requirements. The gate rejects
missing samples, a hand-edited median, a reduced fixture, a deleted/shrunk
test layer, skipped work, or source/test identity drift.

Owned source and package footprints have a five-percent-plus-4096-byte
guardrail. Maximum AST complexity cannot exceed the reference value. A planned
change that legitimately changes an exact identity or ceiling must update this
manifest and this decision record in the same reviewed task; the gate must not
learn a new baseline by itself.

## Current Guardrail Versus Release Target

`make profile-performance-gate` enforces the current, reproducible
anti-regression guardrail. `make profile-performance-release-gate` additionally
enforces the backlog's final one-second route median, response-size reductions,
90-second selected-layer target, and 100-percent configured coverage threshold.
M12-07 makes those targets true: the guided route now embeds only the catalog
needed for first paint and requests one validated CIS merge only when the user
selects that layer. The selected test-layer ceilings use the median of two
fresh M12-07 runs and retain the same 1.25-times-plus-0.5-second variance rule;
they are not learned by the command.

The configured CI coverage threshold and the release threshold are both 100
percent. Any future reduction is a release-gate failure, not an exception to
this performance record.

## Commands

```bash
make profile-performance
make profile-performance-gate
make profile-performance-release-gate
```

When the guardrail fails, retain the generated local report, identify whether
the run is comparable, and fix a product regression or submit a separately
reviewed budget change with fresh evidence. Do not retry until a faster value
appears, lower the repetition count, omit a layer, or replace the fresh run
with an external JSON file.
