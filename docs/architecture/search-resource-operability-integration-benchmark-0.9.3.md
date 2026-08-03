# BPM 0.9.3 Search Resource, Operability, And Integration Benchmark

Date: 2026-07-29

Backlog item: `BPM093-M3-04`

Status: **Measured; no engine is selected.**

## Measured On The Target Host

The i5-7200U/7.1 GiB host from M3-03 rebuilt the isolated six-locale Pagefind fixture and ran the
three-candidate relevance harness in 13.56 seconds, with a runner peak RSS of 376,644 KiB. The
resulting Pagefind site occupied 3,825,096 bytes, of which the generated Pagefind bundles occupied
3,810,168 bytes.

The reproducible M3-04 runner re-verified all three supplied artifacts by SHA-256, then measured a
clean 24-document fixture and a deterministic tenfold documentation-growth fixture (240 documents).
Pagefind indexed the baseline in 4.86 seconds / 3,825,090 bytes and the growth fixture in 5.85
seconds / 4,025,378 bytes. For exact identifier `API-VAL-001`, each of the six locale indexes had
five warm-ups and 30 reported attempts: 180 measurements had a 0.54 ms median and 4.28 ms P95.
The first Pagefind query fetched 69,194–73,380 bytes per locale. The ignored summary is retained
under `documentation/reports/benchmark/bpm093-m3-04.*` and can be regenerated only from supplied,
hash-checked artifacts.

Meilisearch Community Edition `1.45.1` was bound only to `127.0.0.1:17704`, with analytics disabled.
After indexing the English compact fixture it started in 136.23 ms, used 54,400 KiB RSS, and its
five-warm-up/30-measured exact-ID query had median 2.49 ms and P95 4.80 ms. The raw timings are
retained in the ignored M3-04 benchmark workspace. Package/binary bytes were: Pagefind npm 10,509,
Pagefind Linux x64 52,776,114, and Meilisearch binary 141,106,992.

## Operability And Failure Isolation

- The relevance runner rejects any candidate artifact with a wrong SHA-256 before execution.
- The Meilisearch process was explicitly terminated; a later private loopback request received
  connection refusal, while the independent current lexical control still returned `API-VAL-001`.
- Pagefind used temporary static assets only; its Search API fetches were guarded to the temporary
  same-origin loopback server. It has no service-down state.
- Current search source passes `node --check`, fetches its index with `credentials: same-origin`,
  validates result URLs under `/help/{locale}/`, and renders text with DOM text nodes.
- The resource runner performed clean static-artifact installation, atomic promotion to the growth
  fixture, and rollback to the baseline. Each transition was verified by a content-tree digest;
  all three checks passed.
- `make test-docs-browser` passed with Chromium/Selenium. It exercises the BPM-owned documentation
  portal over all six locales, responsive layout, keyboard navigation, localized controls, packaged
  asset loading, and contextual-help/browser flows. It is integration evidence for the current
  portal shell, not a claim that the rejected prototypes are production UI.

## Boundary And Outcome

Browser-process RSS and rendered-search P95 are not reported as prototype measurements: neither
Pagefind nor Meilisearch reached the M3-03 per-locale relevance floor, so neither is admitted to
the production browser adapter stage. The current portal's browser accessibility and integration
contract passed independently. Meilisearch has no browser-to-daemon path by design; its loopback
startup, RSS, latency, package size, and service-down behavior remain recorded above.

The resource figures cannot overcome M3-03 relevance failures, and this record selects no engine.
