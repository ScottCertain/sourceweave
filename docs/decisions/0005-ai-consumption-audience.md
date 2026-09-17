# 0005. AI-mediated consumption serves two audiences, not three

**Status:** Accepted
**Date:** 2026-09-17
**Establishes:** PRD §15

## Context

The PRD assumes a human reader throughout. Success metrics measure style adherence, factual accuracy, and human edit ratio (§10). Publishing means Docusaurus to Netlify (§7.6). The only machine-readable artifacts named are inputs — the OpenAPI spec (FR-5) — or internal bookkeeping — provenance front matter (FR-7).

That assumption no longer matches how documentation is reached. A growing share of documentation consumption is mediated: a person asks an assistant, the assistant retrieves and summarizes, and the person never opens the page. Nothing in the PRD says whether SourceWeave serves that path, and the one adjacent requirement — `noIndex` until quality thresholds are met (FR-22) — governs search-engine crawlers only. Leaving the question unanswered does not produce neutrality; it produces whatever Docusaurus and Netlify do by default.

The decision that has to come first is not technical. **An AI is never the beneficiary of documentation — it is a channel.** Every question about what to expose resolves into a question about which human is on the other side of the agent and what they are trying to do. Three candidate audiences were considered.

### End users of AnythingLLM

People running the application, asking a general-purpose assistant how to configure a provider, set an environment variable, or fix a failing deployment. They need task-shaped answers that are correct for the version they are running. Reach is mostly passive: pages are retrievable and citable, or they are not.

### Developers integrating against AnythingLLM

People building a client, calling the API, or embedding the widget — typically working in an editor alongside a coding agent. They need request and response shapes, authentication, error semantics, and examples that actually run. Reach here is active: an agent fetches deliberately, through a tool call or a context file, rather than stumbling on a page.

### Developers contributing upstream to AnythingLLM

People working inside `anything-llm` itself. This audience is **excluded**, for three independent reasons, any one of which would be sufficient:

1. **The source is already in their context.** Their agent can read the actual implementation. Generated prose describing that implementation is strictly derivative of material the agent already has, and carries a risk the source does not: it can be wrong.
2. **The pin makes our output stale for them by construction.** Per [ADR 0003](0003-upstream-integration.md), `upstream/` is pinned to a release tag. A contributor works on `master`. Serving them documentation that is deliberately behind the code they are editing is worse than serving them nothing.
3. **It contradicts a stated non-goal.** PRD §4 excludes contributing code or documentation upstream.

This is the one case where SourceWeave's output would be *worse than the alternative already available*, which makes it worth excluding explicitly rather than merely deprioritizing.

## Decision

AI-mediated consumption serves **end users** and **integrating developers**. Upstream contributors are out of scope and no channel is designed for them.

**Integrating developers are the primary target.** The reasoning is that this is the audience whose needs coincide with what the pipeline uniquely produces.

A general web crawl can give an agent prose about AnythingLLM. What it cannot give is the version that prose was verified against, whether the code sample in it executes, or how the claim was checked. SourceWeave produces exactly those artifacts already, for its own internal purposes:

| Need of an integrating developer's agent | Existing SourceWeave artifact |
|---|---|
| Which version does this describe? | Pinned submodule tag (ADR 0003), recorded per page (FR-7) |
| Does this example actually work? | Code samples executed at the pinned version (FR-14) |
| Is this claim supported by the source? | Accuracy scoring against source inputs (FR-12) |
| What changed that affects me? | Drift detection against `master` (FR-3, FR-17) |

These were designed as internal quality machinery. Exposing them is a packaging change, not new capability — which is what makes this audience the efficient one to serve first.

End users remain in scope and are served, but through lower-effort surfaces: retrievable, citable pages and an ingestible corpus. No channel is built specifically to satisfy them that would not also exist anyway.

A fourth consumer — model training crawlers ingesting the corpus into weights — is **not an audience**. It is served whether or not it is designed for. It gets a policy line, recorded in PRD §15, not a delivery channel.

## Consequences

**The definition of "documentation quality" gains a second axis.** Prose can satisfy the style guide and be factually accurate while still failing an agent: content locked in tabs, examples split from the call they illustrate, versions stated only in page chrome. Retrieval fitness is a distinct property from readability and is measured separately (PRD §15).

**Provenance becomes an external contract.** FR-7 was internal bookkeeping for incremental regeneration. Once it is returned to calling agents, its shape is something consumers depend on, and changing it is a breaking change. This is a real cost of the decision and the main thing it makes harder.

**Excluding contributors bounds the work.** No need to track `master` for a second, unpinned documentation stream, and no obligation to describe internal architecture, build tooling, or test layout — all of which an integrating developer does not need and a contributor should read the source for.

**The `noIndex` gate needs a sibling.** FR-22 withholds search indexing until quality thresholds are met. AI crawlers are a separate mechanism and require a separate, explicit policy. Recorded in PRD §15; the specific stance is an open question (§13 Q13).

**A portfolio tension is accepted knowingly.** For the end-user audience, success means the reader gets a correct answer *without visiting the site* — which is in direct tension with PRD §2's use of the project as a visible portfolio artifact. The mitigation is citation rather than traffic: stable URLs, page-level attribution that survives summarization, and citation rate tracked as a metric (§10). The trade is made deliberately, not discovered later.

**Reach through this channel does not inherit the official docs' authority.** Direct navigation favors the official documentation, and that is expected. Retrieval does not work that way — an assistant cites what is most retrievable and best structured, not what is most official. Whether SourceWeave outperforms the official docs in that channel is therefore an empirical question, and PRD §15 requires measuring it rather than assuming either outcome.
