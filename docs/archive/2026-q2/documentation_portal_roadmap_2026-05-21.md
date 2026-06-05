# Documentation Portal Roadmap

Date: 2026-05-21

## Purpose

Capture the future product idea for a structured BPM documentation portal before it is split
into backlog issues.

The goal is to evolve BPM documentation from static project notes into a contextual,
searchable documentation system for Firefox Enterprise policies, BPM workflows, and CIS
hardening guidance.

## Product Idea

Build a documentation module based on DITA tooling, with smart search and contextual links
from the BPM interface.

The documentation module should initially live inside BPM, but it should be designed so it can
later become a standalone project, product, or reusable documentation/search tool.

The documentation should cover:

- user documentation for all target BPM locales, starting from the active runtime catalogs and
  expanding with the six-locale UI matrix;
- Firefox policy documentation with examples and version notes;
- CIS layer documentation, either as a dedicated section or integrated with the related Firefox
  policy topics;
- contextual UI help that opens the relevant documentation topic or anchor from a BPM control.

## Why This Fits BPM

BPM already has stable identifiers that can become documentation anchors:

- Firefox policy IDs, such as `AppUpdatePin`, `LocalNetworkAccess`, and `ExtensionSettings`;
- schema channels, such as `release-151` and `esr-140.11`;
- UI targets, such as `policy:AppUpdatePin` and known managed preference targets;
- CIS mapping IDs, generated layers, and preset identifiers;
- guided-editor steps and All settings categories.

This makes it realistic to connect UI controls, policy schema metadata, examples, CIS rationale,
and localized user documentation through a single documentation manifest.

## Suggested Architecture

Use DITA sources as the structured authoring layer:

- source topics under a future `docs-src/dita/` tree or a separate documentation repository;
- generated static output kept out of hand-edited source;
- stable topic IDs and anchors;
- DITA maps for user docs, Firefox policy docs, and CIS docs;
- conditional content for Release / ESR differences;
- locale-specific publishing for the BPM UI locale matrix: `en`, `ru`, `de`, `zh-CN`, `fr`, and
  `es-ES`.

BPM should consume generated documentation artifacts rather than hard-code documentation text
directly into UI templates.

A future generated manifest could look like this:

```json
{
  "version": "0.7.7",
  "locales": ["en", "ru", "de", "zh-CN", "fr", "es-ES"],
  "topics": [],
  "anchors": {},
  "policy_docs": {
    "AppUpdatePin": {
      "href": "/docs/en/firefox/policies/app-update-pin.html",
      "title": "AppUpdatePin"
    }
  }
}
```

## Contextual Help Model

Introduce a stable mapping from BPM UI targets to documentation targets.

Example:

```json
{
  "policy:AppUpdatePin": {
    "topic": "firefox/policies/app-update-pin",
    "anchor": "usage",
    "locales": ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
  }
}
```

This mapping should allow the user to open documentation from:

- Guided editor cards;
- All settings rows and detail panels;
- JSON editor validation messages;
- CIS preset and compliance-layer explanations;
- import/export validation errors.

## Smart Search Direction

Build smart search in layers.

First layer: deterministic documentation search.

- full-text search over generated topics;
- policy ID lookup;
- synonyms and aliases;
- tags and categories;
- schema channel filtering;
- CIS level and control filtering;
- locale-aware result ranking.

Second layer: question answering over documentation.

- build embeddings from generated DITA topics or chunks;
- retrieve relevant passages by locale, policy, CIS layer, and schema version;
- answer with source links and citations;
- keep model output grounded in the indexed documentation instead of relying on model memory.

This should be treated as retrieval-augmented documentation, not as an undocumented assistant
that answers from opaque training data.

## Content Model

Suggested topic families:

- user tasks: create a profile, import `policies.json`, edit All settings, export Firefox policy
  documents, review validation errors;
- policy reference: one topic per important Firefox policy, with examples, supported versions,
  caveats, and related BPM controls;
- policy examples: reusable DITA fragments for `policies.json` snippets;
- CIS guidance: control rationale, policy mappings, preset behavior, and generated layer notes;
- troubleshooting: schema mismatch, unsupported policy, raw fallback, validation errors, live
  Firefox testing caveats.

## MVP Path

1. Add a documentation manifest format and stable UI-to-doc target mapping.
2. Add DITA source for a small set of high-value topics and policy references.
3. Generate static localized docs and serve them from BPM.
4. Add contextual help links from selected UI controls.
5. Add deterministic full-text search.
6. Add policy/CIS cross-links and schema-version filtering.
7. Add retrieval-based question answering after the content and anchors are stable.
8. Reassess whether the documentation module should become a separate product.

## Risks And Constraints

- DITA is powerful but heavier than Markdown; it is best justified if BPM needs reuse,
  conditional publishing, localization, and long-term structured docs.
- Documentation source, generated output, search index, and UI anchor mappings must have clear
  ownership boundaries to avoid mixing product code and generated documentation.
- ML answers must cite documentation sources and should not invent policy behavior.
- Contextual links need stable IDs, otherwise UI refactors can break help navigation.
- Policy documentation must track Firefox Release / ESR differences and should be updated as part
  of the schema bump process.

## Open Questions

- Should the first implementation use DITA-OT directly, or a smaller wrapper around DITA tooling?
- Should generated documentation be committed, built in CI, or packaged separately?
- Should search run fully in-browser for offline/self-hosted deployments, or use a backend index?
- Which ML provider or local model strategy fits BPM's privacy and deployment expectations?
- How much of Mozilla policy documentation can be reused, linked, or summarized without creating
  licensing or maintenance issues?
- Should CIS documentation be a separate map or embedded into policy topics as compliance notes?

## Later Backlog Split

This roadmap intentionally does not define implementation tickets yet.

When ready, split it into backlog items around:

- documentation source structure;
- DITA build pipeline;
- generated docs serving;
- docs manifest;
- UI contextual help links;
- deterministic search;
- policy/CIS topic model;
- localization workflow;
- retrieval and question-answering prototype.
