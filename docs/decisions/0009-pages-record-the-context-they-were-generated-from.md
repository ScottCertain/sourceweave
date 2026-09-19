# 0009. A page records exactly the context it was generated from

**Status:** Accepted
**Date:** 2026-09-19
**Refines:** PRD FR-7; sets the basis for the incremental regeneration required by [ADR 0002](0002-model-access-via-claude-subscription.md)

## Context

Every generated page carries a list of what it was made from — `Provenance.sources`, today a file path and a SHA-256 per entry. When something on that list changes, the page is stale and gets regenerated.

That list is a bigger decision than it looks, because it does two jobs that pull in opposite directions.

**Staleness detection** wants the list *small*. Under a fixed capacity ceiling, regenerating pages that did not need it is the cost that matters.

**Provenance** (FR-7) wants the list *complete*. It is the record of what the page was written from, and FR-12 checks the page's claims against it. A curated list makes provenance an editorial claim rather than a fact.

### What the two look like

Take one page, describing `POST /v1/workspace/new`.

**A broad list:**

```
page: create-a-workspace.md
  made from →  openapi.json            ← the entire 70,390-char file

an unrelated endpoint is added elsewhere in that file
                   ↓
      the file changed → this page regenerates
                   ↓
             wasted work
```

**A narrow list:**

```
page: create-a-workspace.md
  made from →  openapi.json · /paths//v1/workspace/new      (~1,100 chars)
  made from →  openapi.json · /components/schemas/Workspace

an unrelated endpoint is added elsewhere in that file
                   ↓
      neither piece changed → the page sits still
                   ↓
            correct, and free
```

This is not hypothetical. `v1.15.0 → v1.16.0` changed the spec by `+97 / −2` — one new endpoint. With broad lists, **all 63 endpoints' pages regenerate to add one**. With narrow lists, nothing regenerates and one page appears.

### The failure modes are not symmetric

| | When it is wrong | Do you find out? |
|---|---|---|
| Too broad | Regenerates constantly, spending capacity on unchanged pages | **Yes.** Obvious and irritating. |
| Too narrow | Misses a real change. The page is wrong and *looks* current. | **No.** Silent. |

Leave `Workspace` off that list, let the schema change, and the page keeps describing the old shape while its provenance asserts freshness. That is the more dangerous error, and it is the one a well-meaning attempt to save capacity produces.

## Decision

**A page records exactly the context that went into its prompt.** No more, no less.

Not a curated subset chosen for regeneration behaviour, and not the whole file for safety.

This cannot be too broad, because the generator only reads what it needs. It cannot be too narrow, because everything read is recorded. And the record is mechanically true rather than a judgement — which is what FR-12 needs, since accuracy scoring checks claims against it.

The consequence is that **this is really a decision about context assembly.** Recording follows from it. A prompt carrying 70 KB of spec to describe one endpoint was already wasteful and already diluted attention; provenance just makes that cost visible.

### Sources are addressed at semantic units

`SourceRef.path` stops meaning only "a file". Where a source is structured, an entry addresses the unit actually read:

```
server/swagger/openapi.json#/paths/~1v1~1workspace~1new
server/swagger/openapi.json#/components/schemas/Workspace
server/endpoints/api/workspace/index.js            ← unstructured: whole file
```

The digest covers the extracted, canonicalised unit, not the containing file.

### Resolving `$ref` is free, not a new cost

The pinned spec contains 122 `$ref` occurrences, so a path subtree alone is incomplete — `POST /v1/workspace/new` cannot be described without the `Workspace` schema it points at.

Resolving those refs looks like a provenance expense. It is not: **the model needs the resolved schema to write the page at all.** Refs are resolved to build the prompt; recording what was resolved costs nothing extra. If a schema is missing from the list, it was missing from the prompt, and the page was generated blind.

### `ambient_context` keeps its separate job

Some inputs are read for every page and should not trigger regeneration of every page. The style guide is the clear case: a style change arguably *should* invalidate the corpus, but a full-corpus regeneration is what the capacity ceiling forbids.

`Provenance.ambient_context` already exists for exactly this — drift that is **detectable but not regenerating**. The style guide belongs there. `sources` stays for content inputs that define what the page says.

## Consequences

**Context assembly and provenance become the same operation.** Sources are emitted by the assembler rather than declared separately. You cannot record the wrong list without having prompted with the wrong list — the two failures collapse into one, and the remaining one is visible in the output.

**Page granularity now has a cost attached.** Nine tag-grouped pages and sixty per-path pages have very different blast radii when a shared schema moves. That choice should be made alongside this one, not after.

**Code-grounded prose is the floor case, and it is worse.** A JavaScript file cannot be reliably subdivided, so those entries stay file-level — and `v1.15.0 → v1.16.0` touched 142 files under `server/`. A page grounded in a handler regenerates whenever anything in that file moves, including changes that do not affect it. There is no clean fix. It arrives with prose generation at M6–M7 rather than with the API reference at M2, and it is the point at which this decision starts to hurt.

**Changing this later is expensive.** Source addressing is part of every page's fingerprint. Revising it after a corpus exists reports every page as stale at once — a full-corpus regeneration, which is precisely what the ceiling makes impractical. This is settled now, before the first page, for that reason.

**A missing source is now a generation bug, not a bookkeeping one.** If a page's list is incomplete, the prompt was incomplete, and the page was written without something it needed. That reframing is the point: an incomplete list stops being a provenance tidiness issue and becomes evidence the page may be wrong.
