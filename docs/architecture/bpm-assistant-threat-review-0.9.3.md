# BPM 0.9.3 Independent Assistant Threat Review

Backlog item: `BPM093-M8-07`
Review date: 2026-07-30
Status: current M8 surface accepted; eight explicitly owned product-release blockers remain.

## Outcome

The review traced every `AI093-T01` through `AI093-T14` boundary from the M2 threat model through
the implemented model/runtime installers, retrieval and conversation pipeline, scope/content guards,
offline worker, result validation, cancellation, diagnostics and retention. No assistant HTTP route,
browser chat UI or external-web adapter exists, so their absence is a real current control but not
evidence that those future surfaces are safe to enable.

Two high-severity deterministic bypasses were found and closed. First, an explicit `BPM` anchor
could precede a typoglycemia, invisible-format, hex or double-percent encoded instruction override
that escaped the original fixed patterns. Those forms now refuse before semantic admission,
retrieval or inference in all six locale paths. Second, managed-path validation now rejects encoded
separators, backslashes, alternate-stream colons, controls and symlinks in ancestors above the
configured root, rather than checking only descendants.

The fixed regressions do not depend on model output. An adversarial case either reaches zero semantic,
retrieval and worker calls or the test fails. No exception is attributed to model nondeterminism.

## Threat Disposition

| Threats | Disposition | Evidence or release condition |
| --- | --- | --- |
| `T01`, `T03`, `T04`, `T08`, `T09`, `T12` | Closed | Fixed red-team, path/artifact, no-listener, integrity, retention and no-tool tests cover the currently implemented surface. |
| `T02`, `T13` | Release blocker — M9 | Web remains absent. Provider enablement requires fixed-endpoint SSRF/DNS/IP/redirect/proxy controls, consent, minimal disclosure, quarantined content and local-only fallback evidence. |
| `T05`, `T06`, `T07` | Release blocker — M10 | No route/UI exists. M10 must add actual-body bounds, CSRF session rotation and replay rejection, safe text-only rendering/CSP, malicious-render tests and per-session rate limiting before activation. |
| `T10`, `T14` | Release blocker — M11 | Current offline process, diagnostics, clear/expiry, cancellation and unload are closed. Production integration must prove zero post-install network, disabled core/crash dumps, and the full update/rollback/removal/recovery matrix. |
| `T11` | Release blocker — M13 | Model/runtime source, revision, license, size and SHA-256 are pinned. Final packaging still requires locked dependency, advisory and provenance evidence. |

There are no accepted security exceptions or compensating-control waivers. The blockers do not stop
the backlog from moving to M9; they prevent product release or activation of the named future surface
until its owning milestone supplies the evidence.

The review was checked against the current OWASP LLM prompt-injection, SSRF and CSRF cheat sheets and
SLSA 1.2 artifact-verification guidance. In particular, pattern guards are treated as one bounded
layer: security authority remains in deterministic scope, isolation, no-tools, output/citation and
least-privilege controls.

The normative review record is
`documentation/config/bpm-assistant-threat-review-0.9.3.json`.
