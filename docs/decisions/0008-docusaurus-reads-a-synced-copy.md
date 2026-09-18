# 0008. Docusaurus reads a synced copy, not the corpus directly

**Status:** Accepted
**Date:** 2026-09-18
**Supersedes:** one consequence of [0001](0001-pipeline-language.md); see below
**Closes:** issue #12

## Context

Two merged records disagree about how the site gets its content.

[ADR 0001](0001-pipeline-language.md), under Consequences:

> The pipeline writes Markdown and provenance sidecars into `targets/<name>/docs/`; Docusaurus reads that directory.

[ADR 0006](0006-one-corpus-many-channels.md) rejects exactly that arrangement:

> Pointing Docusaurus directly at `targets/<name>/docs/` would remove the sync step but bypass the review gate entirely — Docusaurus would render `reviewed_by: null` pages — and would force Docusaurus-shaped front matter into the corpus, which is the coupling this record exists to prevent.

Records are immutable once merged, so neither can be edited to agree with the other. ADR 0006 never declared itself as superseding anything, and ADR 0001's status line still read plain `Accepted` — so a reader working through the records in order got the wrong answer, with nothing marking it as stale.

Nothing depended on the resolution until now. M2 produces the first generated page, which is the moment something has to actually read the corpus.

## Decision

**ADR 0006 wins.** `channels/site/` loads the corpus, applies the review gate, and writes Markdown into `site/docs/`, which is derived and gitignored. Docusaurus never reads `targets/<name>/docs/`.

PRD FR-26 already records this as Decided: *"A shared corpus loader enforces the review gate, excluding pages with `reviewed_by: null` from every channel."*

The rest of ADR 0001 stands unchanged — Python for `pipeline/` and `eval/`, Node for `site/`, and the filesystem boundary between them. Only the sentence naming Docusaurus as a direct reader is superseded. ADR 0001's status line now points here.

### Why the direct read loses, given it is simpler

It is genuinely simpler: no sync step, no derived directory, no gitignore entry, and Docusaurus supports a `path` pointing outside the site directory. The reason to reject it is where the review gate ends up.

There are already two protections against publishing unreviewed content, and they guard different things:

| Mechanism | Guards against | Weakness |
|---|---|---|
| `**/docs/**/*.draft.md` in `.gitignore` | Committing a draft by accident | A filename convention. A page written as `page.md` with `reviewed_by: null` passes it. |
| `reviewed_by: null` excluded by the loader | Publishing a page nobody approved | Needs something to do the excluding |

The filename convention is a human habit. The front-matter gate is a property of the page, checked mechanically — which matters most for a page **regenerated in place**, where the filename never changes and review status silently resets.

A direct read has nowhere to put that check. Docusaurus renders what is in the directory. Adding the gate would mean a Docusaurus plugin — site-specific code enforcing a rule that applies to every channel, which is precisely the coupling ADR 0006 exists to prevent. The MCP server and `llms.txt` would each need their own copy, and CLAUDE.md's prohibition on publishing unreviewed content would hold for the site and quietly fail elsewhere.

One gate, in the shared loader, is the arrangement that makes the rule true for every channel at once.

## Consequences

**`site/docs/` is derived and gitignored.** It is a build artifact. Committing it would double every regeneration diff and undercut FR-8, whose purpose is readable diffs on reviewed output.

**The Netlify build needs the sync to run before `docusaurus build`.** That puts a Python step in a Node build. If it proves fragile, committing the synced copy is the documented fallback — a fallback, not the default.

**This does not cause issue #32.** Netlify's base directory is `site/`, so a corpus-only change fails to trigger a build whichever way Docusaurus reads. That is a separate fix.

**The corpus format is now load-bearing for four consumers.** Front matter changes need the care of an API change, as ADR 0006 already noted.

**Records can drift silently, and nothing catches it.** ADR 0006 contradicted 0001 for two days with no signal. The only reason it surfaced was writing `site/README.md` and having to state which was true. There is no mechanical check for this the way there is for FR-22 or the merge method — worth remembering that the decision record is the one part of this project still guarded only by attention.
