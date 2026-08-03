# BPM 0.9.3 Six-Locale Browser Search Tuning Benchmark

Status: accepted evidence for `BPM093-M4-04`.

## Decision

The selected BPM-owned browser ranker retains its locale-aware normalization, reviewed aliases,
bounded typo matching, technical identifier protection, compound-token handling, and CJK full-run,
unigram, and bigram behavior. No vendor dependency or broad fuzzy rule is added.

The benchmark executes the maintained `bpm-docs-search.js` ranker through Node against the frozen
M3 synthetic corpus. The control is the preserved M3 current-static scoring mirror. The candidate
projects the same compact documents with the reviewed locale alias groups that the selected BPM
index emits. The runner makes no request and does not read a generated site.

## Result

All 244 cases passed. Each locale is no worse on Top-1, MRR, Recall@5, and no-result recall; each
strictly improves Top-1, MRR, and Recall@5. Values below are exact runner results.

| Locale | Frozen Top-1 / MRR / R@5 / no-result | Selected browser Top-1 / MRR / R@5 / no-result |
| --- | --- | --- |
| `en` | .96875 / .96875 / .96875 / .42857 | 1 / 1 / 1 / 1 |
| `ru` | .96875 / .96875 / .96875 / 1 | 1 / 1 / 1 / 1 |
| `de` | .71875 / .73438 / .75 / .85714 | .9375 / .9375 / .9375 / 1 |
| `zh-CN` | .71875 / .73438 / .75 / 1 | 1 / 1 / 1 / 1 |
| `fr` | .97222 / .97222 / .97222 / .85714 | 1 / 1 / 1 / 1 |
| `es-ES` | .96875 / .96875 / .96875 / .85714 | 1 / 1 / 1 / 1 |

M4-05 reran this unchanged benchmark after retiring unreachable browser legacy code. The run used
browser-script SHA-256 `ca9c8bebdae90a776f000c2b6ab660388841c56dcba3de844818e3aa121190f9` and corpus SHA-256
`0993aec89fe2991d6ef15de251bfedfa87ea99ae6498e5ef73a84f2d6b1aff52`.

## Reproduction

Run:

```bash
./.venv/bin/python documentation/tools/run_browser_search_tuning_benchmark_0_9_3.py \
  --output documentation/reports/benchmark/bpm093-m4-04.json
```

The output is ignored evidence, not hand-authored source. The runner exits non-zero if any locale
regresses on a protected metric or does not strictly improve a relevance metric.
