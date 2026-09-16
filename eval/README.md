# eval/

Evaluation. Scores generated output and tracks quality over time.

Licensed MIT.

## What gets scored

| Dimension | Requirement | Method |
|---|---|---|
| Style-guide adherence | PRD FR-11 | Deterministic rules where expressible (Vale), model-scored where not |
| Factual accuracy | PRD FR-12 | Claim extraction, then lookup against the pinned source |
| Code sample correctness | PRD FR-14 | Execute samples against a running instance at the pinned version |

## Two-layer scoring

Style rules split into two kinds, and the split matters:

- **Mechanically checkable** — heading order, sentence length, banned words, passive voice, link text. These belong in Vale or a linter. They are free, deterministic, and run in CI on every commit.
- **Judgment-requiring** — does this explanation actually explain, is the example well-chosen, is the ordering sensible. These need a model.

Push every rule into the first layer that can live there. A model-scored rule spends capacity budget on every run; a linter rule spends none and never drifts.

## Model tier

Evaluation uses a different tier than generation (Sonnet vs. Opus, per [ADR 0002](../docs/decisions/0002-model-access-via-claude-subscription.md)). This reduces shared blind spots less than a different vendor would. The mitigation is the one already in the PRD: calibrate automated scores against human judgment on a sample of pages, and track whether they agree.

**Calibration is not optional.** An evaluation harness nobody has checked against human judgment is a number generator, not a measurement. Build the calibration sample alongside the first scores in M4.

## Structured output

Scoring uses the CLI's `--json-schema` flag so results come back as structured data rather than prose to be parsed. `ClaudeClient.evaluate()` handles this and raises if structured output is missing.

## What is committed

Summarized scores are committed so quality trends are visible in history. Raw run logs are **not** (PRD FR-15) — they live under `.runs/`, which is gitignored.
