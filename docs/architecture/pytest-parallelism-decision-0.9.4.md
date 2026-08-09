# Pytest Parallelism Decision for BPM 0.9.4

Updated: 2026-08-05
Backlog item: `BPM094-M8-08`

## Decision

No mandatory pytest parallel layer is selected for BPM 0.9.4. The authoritative mandatory
product contour remains serial. `make test-unit-xdist XDIST_WORKERS=2` remains an explicit,
manual diagnostic pilot; it is not a default target and is not added to mandatory CI.

The smallest stable parallel candidate is a fixed two-shard unit split, but it is also not adopted
as a mandatory CI job. It would require a new, non-overlapping coverage/job design to shorten the
existing critical path. Adding it beside the current complete serial coverage job would duplicate
work and leave that coverage job as the critical path.

## Reference runner and method

- Date: 2026-08-05; Linux, 4 logical CPUs, 7.1 GiB RAM.
- Python 3.14.4; pytest 9.1.1; pytest-xdist 3.8.0.
- The measured contour was `unit and not ai_incubation`: 271 selected, 831 deselected tests.
- Each serial, xdist, and shard configuration ran three times. GNU `time` recorded wall time,
  user+system CPU time, and maximum RSS for the coordinator/process. Shard RSS is the sum of the
  two independently measured process peaks, so it is an upper-bound comparison rather than a
  synchronized process-group peak.
- The timing matrix disabled random ordering so that scheduler overhead, not randomizer overhead,
  is compared. Fixed shards use the collected node-id order, alternate item assignment, and unique
  `PYTEST_XDIST_WORKER` values to retain isolated temporary database roots.

## Timing matrix

| Configuration | Workers / shards | Median wall | Median CPU | Median max RSS | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| serial | 1 | 50.61 s | 47.26 s | 208,080 KiB | 3/3, 271 passed |
| xdist | 2 | 49.78 s | 72.96 s | 207,808 KiB | 3/3, 271 passed |
| xdist | 4 | 53.02 s | 84.19 s | 194,572 KiB | 3/3, 271 passed |
| fixed unit shards | 2 | 40.17 s critical wall | 66.53 s combined | 318,240 KiB summed peaks | 3/3, 271 passed |

Two-worker xdist improves median wall time by only 0.83 s (1.6%) and costs 54% more CPU. Four
workers regress wall time by 2.41 s (4.8%) and cost 78% more CPU. Two fixed shards are 20.6%
quicker than the serial median, but do not reduce the current CI critical path: the serial coverage
job still executes the complete contour and would remain required.

## Order and flake evidence

`pytest-randomly` 4.1.0 was installed only for this one-off audit; it is not a project dependency
and does not alter the ordinary test order. Its three explicit seeds exercised the same contour in
both serial and two-worker xdist modes:

| Seed | Serial | xdist, 2 workers |
| ---: | --- | --- |
| 1101 | 271 passed | 271 passed |
| 2202 | 271 passed | 271 passed |
| 3303 | 271 passed | 271 passed |

All six seeded executions passed. Their median wall/CPU/RSS was 57.81 s / 54.30 s / 209,052 KiB
serial and 53.62 s / 73.84 s / 207,528 KiB for two-worker xdist. The difference proves stability,
not a new performance baseline, because randomizer work is intentionally outside the timing matrix.

The three old `pytest.mark.order` annotations on independently isolated SQLite migration tests were
removed. No `order` marker remains registered: there is no order-enforcement plugin in the supported
test runtime, so retaining the marker would falsely suggest an execution guarantee.

## Maintainer test-layer commands and revisit conditions

Choose the primary layer from the owning path, not from a central filename
registry. `unit`, `integration`, `contract`, `browser`, and `live` are mutually
exclusive primary layers; domain markers such as `db`, `docs`, and `ui` refine
the selected layer but do not replace it. The ownership manifests under
`tests/` and `documentation/tests/` reject unknown or duplicate ownership at
collection time.

```bash
# Deterministic product layers
make test-unit
make test-integration
make test-contract

# Database integration: SQLite locally; PostgreSQL is mandatory in its CI job
make test-db-integration
make test-postgres-integration

# Browser and live layers are explicit, isolated contours
make test-browser
make test-live

# Explicit diagnostic pilot, never a default or mandatory CI command
make test-unit-xdist XDIST_WORKERS=2

# One-off order-dependence audit; do not add this package to ordinary commands
python -m pip install 'pytest-randomly==4.1.0'
pytest -o addopts= -q -m 'unit and not ai_incubation' --randomly-seed=1101
pytest -o addopts= -q -m 'unit and not ai_incubation' --randomly-seed=1101 -n 2
```

Reconsider mandatory sharding only if a proposed CI split removes, rather than duplicates, serial
coverage work; retains identical selected node IDs and coverage semantics; proves worker roots,
ports, artifacts, and caches isolated; and records at least three clean hosted-runner repetitions
with a material critical-path reduction. Browser and live Firefox contours remain serial until their
per-worker runtime, profile, port, and artifact isolation is separately proven.
