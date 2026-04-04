# Advanced-only Boundary Register

Date: `2026-04-04`

## Purpose

This register defines which policy areas should remain `handoff-heavy` or `advanced-only by design` even as guided coverage keeps growing.

The goal is to protect the wizard from slowly turning back into a schema mirror.

## Decision Rules

- Keep a cluster in guided mode only when it supports a clear scenario-first user task.
- Keep a cluster as `quick focus + handoff` when the task is real but the underlying structure is still too irregular for a stable guided form.
- Keep a cluster `advanced-only` when it is low-frequency, highly technical, structurally open-ended, or likely to bloat the wizard more than it helps.
- Moving a policy cluster into guided mode does not remove the technical path. Guided promotes the common route; Advanced document stays the canonical full-control fallback.
- When a cluster becomes guided-covered, coverage accounting and export summaries must stop counting it as `advanced-only`.

## Boundary Register

### Keep Advanced-only

1. Low-level preference bundles without a stable task-first story.
   These are often meaningful only to a specialist who already knows the exact preference keys or browser internals they need to override.

2. TLS, cipher, and other niche security internals.
   These controls are operationally sensitive, comparatively rare, and too easy to misrepresent with shallow presets.

3. Open-ended object and dictionary branches with weak scenario cohesion.
   If the shape keeps branching into arbitrary nested keys, it belongs in Advanced document until a strong recurring scenario emerges.

### Keep As Quick Focus + Handoff

1. AI provider and model detail.
   Surface-level AI posture belongs in guided mode, but provider/model internals remain handoff-heavy until they form a more stable admin task.

2. Rare enterprise authentication exceptions.
   Common trust and sign-in posture can be guided, while unusual host exceptions and environment-specific branches continue to live behind advanced fine tuning.

3. Certificates with custom file-import detail.
   Enterprise roots can be guided; direct certificate file management still needs the technical route for full fidelity.

## Current Product Consequence

The finish flow should explain that some areas remain in `Advanced document` deliberately:

- not because coverage was forgotten
- not because serialization would lose them
- but because those areas still work better as precise technical controls than as forced wizard abstractions

## Review Trigger

Revisit an `advanced-only` area only when at least one of the following becomes true:

- a recurring enterprise scenario appears clearly enough to support a task-first flow
- the same area repeatedly shows up in guided-to-advanced handoffs
- the area can be expressed as a compact posture or scenario bundle rather than raw nested structure
