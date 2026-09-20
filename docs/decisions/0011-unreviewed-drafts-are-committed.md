# 0011. Unreviewed drafts are committed; the loader gate is what publishes

**Status:** Accepted
**Date:** 2026-09-20
**Supersedes:** one row of [0008](0008-docusaurus-reads-a-synced-copy.md)'s protection table; see below
**Refines:** PRD FR-8; makes the *human edit ratio* in PRD §10 measurable
**Settles:** issue 53

## Context

Two things need the generated text as it was before a human touched it.

**PRD §10, human edit ratio** — "share of generated text changed during review (should fall as the pipeline improves)". It is the instrument that shows review getting cheaper as the style guide and prompts improve. Without the pre-edit text there is nothing to compute.

**M3** — "edit the M2 output; write the first style guide from those edits" (PRD §11, FR-9). The style guide is built *from* the edits. They have to be visible somewhere.

The repository's current rule loses that text. `.gitignore` excludes `**/docs/**/*.draft.md`, with the comment *"Drafts awaiting human review. Only reviewed output is committed."* Review happens by editing the draft in place. The moment it is edited, the generated version is gone — and the first review pass is unrepeatable, because a second generation produces different text.

This is decided before the first draft exists because the first Workspaces run ([ADR 0010](0010-api-reference-pages-are-one-per-operation.md)) is the first data point.

## Options

**A. Commit unreviewed pages.** The generator writes `page.md` with `reviewed_by: null`, committed as generated. Review is ordinary commits on top. The edit ratio is `git diff` between the generation commit and the review commit — exact, free, and in history.

**B. Keep drafts out of git.** Drafts stay gitignored; the generator also writes a pre-review copy to `.runs/`; the ratio is computed at review time and only the number is committed (FR-15). The record of *what* was edited lives in a gitignored directory on one machine.

## Decision

**A. Generated pages are committed as generated, with `reviewed_by: null`. Review is commits on top. Publication is gated by the corpus loader, not by what is in the repository.**

The `*.draft.md` convention is retired. There is no rename step, and no filename distinguishes a draft from a reviewed page. The distinction is the `reviewed_by` field, which is a property of the page checked mechanically — the thing [ADR 0008](0008-docusaurus-reads-a-synced-copy.md) already argued was the real protection:

> The filename convention is a human habit. The front-matter gate is a property of the page, checked mechanically.

## Consequences

**The review gate is now the only gate, and it is load-bearing.** 0008's table listed two protections against publishing unreviewed content: the gitignore rule, guarding against committing a draft by accident, and the loader gate, guarding against publishing one. The first row is superseded by this record — committing an unreviewed page is now the intended path, not an accident. The loader gate (FR-26) and its CI verification against the built site carry the whole rule. That check is not defence in depth; it is the defence.

**The edits are in history.** Every review pass is a readable diff against the generated text, which is what FR-8 asked for and what M3 consumes. A regeneration is reviewed the same way: as a diff against the previously approved version, not as a fresh read. This is the largest single lever on review cost, and it exists only because the pre-edit text is committed.

**"Publish" and "commit" mean different things, and the difference is stated.** CLAUDE.md's rule — *do not publish unreviewed generated content* — is unchanged. `main` may contain pages with `reviewed_by: null`; no channel may render them. A reader of the repository sees drafts; a reader of any channel does not.

**Regeneration resets review, visibly.** When a page's sources change and it regenerates, `reviewed_by` returns to `null` in the same commit that changes the text. The page drops out of every channel until someone approves it again. That is the behaviour 0008 wanted and could not get from a filename.

**`.gitignore` loses a rule.** The `**/docs/**/*.draft.md` entry and its comment are removed with this record. The `.runs/` and `.checkpoints/` entries stay; they hold machine state, not pages.

**Option B's one advantage is given up.** With B, a page could not reach `main` without a human having seen it. With A, a bad generation lands on `main` unreviewed. That is accepted: it reaches no reader, it is visible in the PR that carried it, and reverting a commit is cheaper than losing the review record.
