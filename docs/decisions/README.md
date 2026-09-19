# Architecture decision records

Each file records one decision: the context, the choice, and the consequences accepted.

Records are immutable once merged. To change a decision, add a new record that supersedes the old one and update the old record's status line to point at it.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-pipeline-language.md) | Python for pipeline and evaluation, Node for the site | Accepted — one consequence superseded by [0008](0008-docusaurus-reads-a-synced-copy.md) |
| [0002](0002-model-access-via-claude-subscription.md) | Generation operates under a fixed capacity budget | Accepted |
| [0003](0003-upstream-integration.md) | Upstream repos as pinned Git submodules | Accepted |
| [0004](0004-licensing-split.md) | MIT for code, CC BY 4.0 for prose | Accepted |
| [0005](0005-ai-consumption-audience.md) | AI-mediated consumption serves two audiences, not three | Accepted |
| [0006](0006-one-corpus-many-channels.md) | One corpus, many channels | Accepted |
| [0007](0007-citation-tracking.md) | Citation rate is measured on a schedule and published | Accepted |
| [0008](0008-docusaurus-reads-a-synced-copy.md) | Docusaurus reads a synced copy, not the corpus directly | Accepted |
| [0009](0009-pages-record-the-context-they-were-generated-from.md) | A page records exactly the context it was generated from | Accepted |

## Relationship to the PRD

[PRD.md](../../PRD.md) states *what* the system must do and tracks open questions in §13. These records state *how* and *why*, and close those questions. Where a record closes a PRD open question, it says so explicitly.

## Template

```markdown
# NNNN. Title

**Status:** Proposed | Accepted | Superseded by [NNNN](NNNN-....md)
**Date:** YYYY-MM-DD
**Closes:** PRD §13 Qn (if applicable)

## Context
What forced a decision. Constraints that were real at the time.

## Decision
The choice, stated plainly.

## Consequences
What this makes easy, what it makes hard, and what is now load-bearing.
```
