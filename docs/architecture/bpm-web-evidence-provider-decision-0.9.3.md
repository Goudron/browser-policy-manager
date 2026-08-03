# BPM 0.9.3 Optional Web-Evidence Provider Decision ADR

Date: 2026-07-30
Backlog item: `BPM093-M9-01`
Status: Brave Search API `LLM Context` selected as a contract only; web mode remains disabled and
no credential, route, network call or browser UI is added.

## Decision

BPM selects the Brave Search API `POST https://api.search.brave.com/res/v1/llm/context` endpoint as
its only eligible optional web-evidence provider. The endpoint returns raw pre-extracted source
content intended for RAG, while generation stays in BPM's selected local Qwen worker. Brave Answers,
Web rich callbacks, direct page fetching and every user/model-supplied destination remain forbidden.

The integration is bring-your-own-key. An administrator uses their own Brave Search API subscription
token; BPM ships no shared credential and the token never enters browser code, URLs, logs or model
input. Brave currently lists Search at USD 5 per 1,000 requests with USD 5 monthly credit and
requires payment information. Provider quotas remain authoritative, while BPM's stricter rule is one
call per explicitly consented question with no automatic retry.

## Comparison

| Candidate | Decision | Main reason |
| --- | --- | --- |
| Brave Search API LLM Context | Selected | Fixed HTTPS API, POST, raw RAG context, language preferences, hard result/token bounds, strict relevance and inline source filtering. |
| Google Custom Search JSON API | Rejected | Closed to new customers and scheduled for discontinuation on 2027-01-01. |
| Microsoft Bing Search APIs | Rejected | Retired and fully decommissioned on 2025-08-11; Azure AI Agents would add an unwanted hosted-agent boundary. |
| SearXNG | Rejected as default | It is a metasearch proxy, not an owned index; it forwards queries to changing upstream engines, and its own documentation warns that search syntax such as `site:` is not enforced by every engine. Public instances add another operator. |
| Brave Answers | Rejected | Hosted generation duplicates the local model and weakens BPM's output, privacy and reproducibility boundaries. |

## Privacy And Terms

Brave's privacy notice says standard API query logs may be retained for up to 90 days for billing,
troubleshooting and abuse prevention; Zero Data Retention is an enterprise option. M9-02 must show
the exact outgoing query, Brave as the recipient in the United States, locale-derived language and
that retention warning before every call. Conversation history, local evidence/citations, profiles,
session identifiers, device location and other machine data are never sent.

Provider results are transient evidence for the current BPM answer only. They are not cached,
persisted, indexed, embedded, redistributed as raw results, or used to train, fine-tune, evaluate or
benchmark a model/service. Live results are inherently time-dependent; deterministic tests use
project-owned fixtures. Terms, privacy, pricing, retention, schema or ownership drift disables the
provider pending a new review.

## Source And Request Policy

The request uses the exact consented query only, limited to 400 characters and 50 words, with the
six-locale language mapping, spellcheck off, strict relevance, local/POI recall off, at most five
URLs and 2,048 provider tokens. A fixed inline Goggle discards everything except the four Mozilla
hosts. BPM then independently validates exact HTTPS host/path pairs: Mozilla enterprise policy
templates, Firefox enterprise source documentation, Mozilla enterprise/release pages and Mozilla
Support. The provider-side filter is never treated as authorization.

BPM connects only to `api.search.brave.com:443`. It never follows a result URL. It accepts only a
bounded JSON response's `grounding.generic` section, validates URLs, strips active/hidden/control
content, labels snippets external and untrusted, and keeps them below current local documentation in
authority. No external statement can create or override BPM product support.

## Data Flow And Failure

```text
same-locale question -> BPM scope allow -> explicit disclosure/consent (M9-02)
  -> one fixed bounded Brave POST -> exact host/path post-filter -> inert external EvidencePack
  -> local Qwen generation -> server output/citation validation -> labelled answer -> memory clear
```

Missing consent or credentials, an overlong query, offline/DNS/TLS/provider/rate/schema failure, a
rejected URL, or unsafe content makes no retry and returns local-only behavior. M9-03 must implement
this adapter before provider content can reach inference; M9-05 remains the release security gate.

Official evidence reviewed: [LLM Context API](https://api-dashboard.search.brave.com/documentation/services/llm-context),
[authentication](https://api-dashboard.search.brave.com/documentation/guides/authentication),
[pricing](https://api-dashboard.search.brave.com/documentation/pricing),
[rate limits](https://api-dashboard.search.brave.com/documentation/guides/rate-limiting),
[Goggles](https://api-dashboard.search.brave.com/documentation/resources/goggles),
[terms](https://api-dashboard.search.brave.com/documentation/resources/terms-of-service), and
[privacy](https://api-dashboard.search.brave.com/privacy-policy).

The normative record is
`documentation/config/bpm-web-evidence-provider-trust-policy-0.9.3.json`.
