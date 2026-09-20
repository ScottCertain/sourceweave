# 0010. API reference pages are one per operation, grouped by tag

**Status:** Accepted
**Date:** 2026-09-19
**Refines:** [0009](0009-pages-record-the-context-they-were-generated-from.md), which named this as the choice to make alongside it, and corrects its worked example; bounds the M2 scope in PRD §11
**Settles:** issue 47

## Context

[ADR 0009](0009-pages-record-the-context-they-were-generated-from.md) decided that a page records exactly the context that went into its prompt. It then noted what that leaves open:

> Page granularity now has a cost attached. Nine tag-grouped pages and sixty per-path pages have very different blast radii when a shared schema moves. That choice should be made alongside this one, not after.

The reason it cannot wait is the same one that made 0009 urgent. Granularity is part of every page's fingerprint — which units a page records depends on what a page *is*. Revising it after a corpus exists reports every page stale at once, and a full-corpus regeneration is what the capacity ceiling ([ADR 0002](0002-model-access-via-claude-subscription.md)) makes impractical. So this is settled before the first page, for the same reason.

It also decides something 0009 did not name: how much a human reviews when a page regenerates. Every published page carries a reviewer's name (PRD §4 non-goal on autonomous publishing), and regeneration resets that. Steady-state review cost is therefore upstream churn multiplied by page size. The choice here sets the multiplier.

### The pinned spec, measured

`server/swagger/openapi.json` at `v1.16.1`, read from the submodule rather than assumed:

| | |
|---|---|
| Paths | 60 |
| Operations | 63 — three paths carry two methods each (`/v1/admin/users/{id}`, `/v1/workspace/{slug}`, `/v1/embed/{embedUuid}`) |
| Tags | 9 — Admin 13, Documents 13, Workspaces 11, Embed 6, System Settings 6, Workspace Threads 6, OpenAI Compatible Endpoints 5, User Management 2, Authentication 1 |
| Operations without a tag | 0 |
| Operations with an `operationId` | 0 |
| Component schemas | **1** — `InvalidAPIKey`, the 403 response body |
| `$ref` occurrences | 122, **every one pointing at `InvalidAPIKey`** |

Two of those rows matter more than they look.

**Request and response bodies are inline.** There is no `Workspace` schema; the shape of a workspace is written out inside each operation that uses it. 0009's worked example used `/components/schemas/Workspace` as the shared source that pulls pages along when it moves. In this spec that source does not exist. The only shared unit is the error body, and every operation references it.

**There is no `operationId`.** The stable identity of an operation is its method and path, and nothing else. That has to be the page's identity too.

## Options

| | One page per tag | One page per operation |
|---|---|---|
| Pages at `v1.16.1` | 9 | 63 |
| Invocations for the full section | 9 | 63 |
| Sources per page | every operation in the tag, plus `InvalidAPIKey` | one operation, plus `InvalidAPIKey` |
| One operation changes upstream | the tag page regenerates — up to 13 operations re-drafted to update one | one page regenerates |
| `InvalidAPIKey` changes upstream | all 9 regenerate | all 63 regenerate |
| A regeneration is reviewed as | a long page, most of it unchanged | a short page, most of it changed |
| Retrieval unit at M5 (FR-30) | a page that must survive chunking | the page itself |
| Overview prose for a group | has a natural home | has none |

The `InvalidAPIKey` row is the same event under both options — the whole section regenerates — so it does not distinguish them. It is the one full-regeneration trigger this spec contains, and it is recorded below as a known cost rather than left to be discovered.

A third option, one page per *path* (60 pages), was considered and rejected briefly: it merges `GET` and `DELETE /v1/workspace/{slug}` into one unit, and those change independently. It saves three pages and costs the property the whole record exists to protect.

## Decision

**One page per operation, identified by method and path, grouped by tag for navigation.**

- **Identity.** A page *is* one `method + path` pair. That is the only stable identity the spec offers, and it is what a reader is looking for. `GET` and `DELETE` on the same path are two pages.
- **Sources**, per 0009: the operation's own subtree under `#/paths/<path>/<method>`, plus every unit reached by resolving its `$ref`s transitively. At `v1.16.1` that is the operation and `InvalidAPIKey`, and nothing else. The assembler emits the list; nothing declares it separately.
- **Grouping is presentation.** A page lives in a directory named for its tag, so the site's sidebar follows the spec's own grouping. The tag is *where* the page is, not *what* it is: if upstream re-tags an operation, the page moves and its content does not change. The tag is therefore not a recorded source, and re-tagging does not regenerate.
- **The group directory carries no prose.** A tag directory holds pages and whatever the channel needs for navigation (`_category_.json`). It is not a place for an overview paragraph. Anything that describes AnythingLLM is corpus and carries provenance ([ADR 0006](0006-one-corpus-many-channels.md)); a hand-written "about workspaces" blurb in a category file would be prose about the target that no source produced and no digest guards.

### What "one bounded section" means for M2

PRD §11 scopes M2 to "one bounded section end to end". Per operation, the section is 63 pages, and 63 Opus invocations plus 63 review passes is more than one capacity window and more than one sitting of review. Rather than let "bounded" be reinterpreted midway, the bound is stated here:

- **The section is the API reference.** All 63 operations are in M2's scope.
- **Generation proceeds one tag group at a time.** The generator takes a tag; a run is one group.
- **The exit criterion is met when the first tag group is published and reviewed.** The remaining groups continue under M2 as capacity and review time allow. The milestone closes on its exit criterion, not on the last tag; any groups still unpublished at close move to M7 (Expansion) without reopening this record.
- **The first group is Workspaces** — 11 operations, central to what an integrating developer does first, and the group 0009 already used as its example.

## Consequences

**Sixty-three invocations for the full section.** That is the cost of the finest blast radius, and it is why the bound above exists. Under the ceiling a full pass is a multi-window run; `RateLimited` and checkpointing ([ADR 0002](0002-model-access-via-claude-subscription.md)) are what make that a resumable inconvenience rather than a wall.

**A spec change costs one page.** `v1.15.0 → v1.16.0` added one endpoint. Under this record that is one new page and zero regenerations. Under per-tag it would have been one regenerated tag page, re-drafting every neighbouring operation to add one.

**One change regenerates everything, and it is known in advance.** `InvalidAPIKey` is referenced by all 63 operations. If its shape changes, every page is stale — correctly, since every page documents that response — and the full section regenerates over several windows. This is the single full-regeneration trigger in the spec at `v1.16.1`. Nothing about it is a surprise, and no option avoided it.

**Review cost is per operation.** A regeneration puts one short page in front of a reviewer, most of it changed for a reason the diff shows. That is the shape human review needs to be in for the edit ratio (PRD §10) to fall rather than plateau: the reviewer reads what moved, not thirteen operations to find the one that did.

**The page is already the retrieval unit.** FR-30 asks that sections survive chunking. A page describing one operation does not need to be chunked, so the M5 retrieval surface and the MCP channel get the right unit for free on this section.

**Group-level explanation has no home here, on purpose.** "How workspaces relate to threads and documents" is explanation content (FR-6), not reference, and it is grounded in code rather than in the spec. It is a different content type with a different generation path, and it arrives at M7. Until then the reference section is reference only, and the tag directories stay empty of prose.

**Re-tagging moves a URL.** If upstream re-tags an operation, its page changes directory and its site URL changes, with no content change. That is a presentation concern: the corpus page is unchanged, and any redirect belongs to `channels/site/`, not here.

**This holds for the API reference.** Other sections — configuration, how-tos, anything grounded in JavaScript rather than in a structured file — face the harder case 0009 already flagged, where units are files and blast radius is whatever the file happens to contain. Those get their own decision when they arrive.
