# 0006. One corpus, many channels

**Status:** Accepted
**Date:** 2026-09-17
**Depends on:** [0005](0005-ai-consumption-audience.md)

## Context

[ADR 0005](0005-ai-consumption-audience.md) puts two audiences in scope, reached by different means. Humans browse a site. Coding agents call tools. Assistants retrieve files. End users running AnythingLLM can load a corpus into their own workspace, since the target is itself a retrieval application.

That is four delivery surfaces over the same material, and four surfaces is where documentation systems usually go wrong. The predictable failure modes:

- Each surface grows its own copy of the content, and they drift.
- Target-specific knowledge leaks into shared code to satisfy a particular surface, breaking the reusability the PRD requires (NFR-5, G6).
- A surface starts *generating* rather than rendering — summarizing a page for a context file, say — which spends capacity against a fixed ceiling ([ADR 0002](0002-model-access-via-claude-subscription.md)), produces text with no provenance, and creates a second path by which unreviewed prose can reach the public.

The site being the oldest surface makes this worse, not better. It is easy to treat Docusaurus as the product and everything else as an export, which puts site-shaped assumptions — sidebar structure, MDX components, Netlify redirects — into material that other channels have to undo.

## Decision

There is one canonical corpus. Everything else renders it.

**The corpus** is the reviewed Markdown committed under `targets/<name>/docs/`, together with the provenance front matter each page carries (FR-7). It is the single source for every channel. It is produced by `pipeline/`, scored by `eval/`, and gated by human review.

**A channel** is a deterministic transformation of that corpus into one delivery format. Channels live under a new top-level `channels/` directory (MIT, target-agnostic, alongside `pipeline/` and `eval/`):

| Channel | Audience | Output |
|---|---|---|
| `channels/site/` → `site/` | Humans; portfolio reviewers | Docusaurus HTML |
| `channels/llms-txt/` | Assistants and crawlers | `llms.txt`, `llms-full.txt`, raw Markdown at page URLs |
| `channels/mcp/` | Integrating developers, via a coding agent | MCP server over the corpus |
| `channels/workspace/` | End users, inside their own AnythingLLM | Ingestible document bundle |

Three rules make the separation load-bearing rather than aspirational.

### A channel never invokes a model

No channel imports `claude_client.py` or shells out to `claude`. Channels are pure functions of the corpus: same input, same output, no capacity consumed, no network required.

This follows directly from ADR 0002 — CI invokes no model, and channel builds run in CI. It also means every channel is testable with ordinary fixtures, and that nothing a channel emits can be text no human reviewed.

### A channel never reads upstream

Only `pipeline/` and `eval/` read `targets/*/upstream/` and `targets/*/official-docs/`. A channel that reaches into the submodules is reimplementing generation, and its output would carry no provenance.

### The review gate holds at the corpus, not per channel

A page whose provenance has `reviewed_by: null` is excluded by the corpus loader that every channel uses, so the gate is enforced once. Re-implementing it per channel would mean four chances to get it wrong; CLAUDE.md's prohibition on publishing unreviewed content would hold for the site and quietly fail for the MCP server.

## Consequences

**The site is a channel, not the product.** It remains the primary human surface and the portfolio artifact, and nothing about its importance changes — but it gets no privileged access to the corpus, and site-shaped structure does not belong in the corpus. Anything a page needs in order to render in Docusaurus and nowhere else is a site concern.

**Adding a channel touches no shared code.** If a new channel requires a change to `pipeline/` or `eval/`, that is the signal that something belongs in the corpus and does not yet exist there. The correct fix is to add it to the corpus for every channel, not to special-case one.

**NFR-5 now has a second dimension.** The PRD isolates target-specific material so the pipeline stays reusable across targets. The same isolation now also has to hold across channels. `channels/` is target-agnostic; anything specific to AnythingLLM stays under `targets/anythingllm/`.

**The corpus format is a public interface.** Four consumers depend on its shape, and per ADR 0005 one of them is external. Front matter changes need the same care as an API change.

**`channels/workspace/` is a channel, not an integration.** It emits files. It does not talk to a running AnythingLLM instance, hold credentials, or call an API. Loading the bundle is the user's action in their own workspace. This keeps the target read-only in the operational sense as well as the licensing one, and keeps the channel testable without a live server.

**Determinism is checkable, so check it.** Because channels are pure functions, CI can build each one twice and compare. That turns the central rule of this record into a test rather than a convention.

**Some duplication is accepted.** Four renderers of the same content share less code than seems ideal — an `llms.txt` generator and an MCP server have little in common beyond the loader. Factoring them together prematurely would couple channels whose only real commonality is their input. The shared piece is the corpus loader and the provenance model; below that, duplication is cheaper than the wrong abstraction.
