# style-guide/

The human-authored style guide. Licensed CC BY 4.0.

## This directory is deliberately empty

The style guide is written **from** editing generated output, not before it (PRD G2, M3). Writing rules first would produce guesses about what the pipeline gets wrong. Writing them from real edits produces rules that address real failures.

The sequence is fixed:

1. **M2** — generate a bounded section (API reference from the OpenAPI spec).
2. **M3** — edit that output by hand. Keep every edit.
3. **M3** — read the edits back. Each recurring edit is a candidate rule.
4. **M3** — write the rule, and push it into Vale if it can be expressed mechanically.

A rule earns its place by having been applied by hand at least twice.

## Planned structure

| Path | Contents |
|---|---|
| `STYLE.md` | The guide itself, human-readable |
| `rules/` | Individual rules, one per file, each citing the edits that motivated it |
| `vale/` | Vale styles implementing the mechanically checkable rules (PRD FR-10) |
| `edits/` | The edit log from M3 — before/after pairs that justify each rule |

Keeping `edits/` is what makes the guide defensible rather than arbitrary, and it is the portfolio evidence that the guide came from practice.

## Dual expression

Every rule is written for a human. Rules that *can* also be machine-checked *must* also be machine-checked (PRD FR-10) — a rule only a person can apply is a rule that gets applied inconsistently, and it spends evaluation budget every run.

Each rule file states which form it has:

```markdown
# Rule: <name>

**Machine-checkable:** yes (vale/SourceWeave/<Rule>.yml) | no (judgment required)
**Motivated by:** edits/<file>#<anchor>

<the rule>

## Why
<what went wrong without it>

## Examples
<before / after, taken from real edits>
```
