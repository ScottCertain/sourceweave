# 0007. Citation rate is measured on a schedule and published

**Status:** Accepted
**Date:** 2026-09-17
**Depends on:** [0002](0002-model-access-via-claude-subscription.md), [0005](0005-ai-consumption-audience.md), [0006](0006-one-corpus-many-channels.md)
**Amends:** PRD §10, PRD §15.6

## Context

[ADR 0005](0005-ai-consumption-audience.md) put AI-mediated reach in scope and treated citation rate as a passive observation — something to notice, not something to act on. That understates it.

Citation rate is the only available feedback signal on whether retrieval-fitness work actually changes anything. Every other metric in §10 measures the text; this one measures whether the text is *reached*. Without it, the optimization requirements in §15.2 are unfalsifiable: rules would be followed because they sound right, with no evidence they matter. A documentation system that cannot tell whether its distribution strategy works is missing the loop that makes it a system.

Published on the site, it also does something the other metrics do not — it shows a measurement practice running over time, in public, which is a stronger claim to competence than any single score.

Three constraints make this harder than it sounds.

**It conflicts with two standing rules.** [ADR 0002](0002-model-access-via-claude-subscription.md) establishes that generation is local and supervised and that *CI invokes no model*, and pins settings that deny `WebSearch` and `WebFetch` so generation cannot reach the network. A scheduled citation probe needs all three of the things those rules withhold: a model, network access, and unattended execution.

**Most assistants are not reachable.** The consumer products people actually use mostly have no API that reproduces their search behavior. Claude with web search is reachable through the existing subscription path. Perplexity has an API, but a metered one, which contradicts the no-marginal-cost premise of ADR 0002. ChatGPT's consumer search behavior, Google's AI Overviews, and Copilot have no equivalent programmatic surface. Any claim to poll "the assistants" would be fiction.

**Attribution is genuinely weak.** One site, no control group, and a dozen confounds — upstream releases, crawler cadence, model updates, competing content, question-set drift. A rise after an optimization change is not evidence that the change caused it.

## Decision

Citation rate is measured on a schedule, published on the site, and used as directional evidence for optimization experiments. It is **not** a release gate and **not** a success threshold.

### Scope of measurement

A fixed, versioned question set of realistic AnythingLLM questions. Each run records, per question, whether SourceWeave was cited, whether the official docs were cited, and the answer's accuracy against the pinned source.

That last field matters more than the citation flag. If an assistant answers correctly while citing nobody, the documentation still worked. If it cites SourceWeave and answers wrongly, that is a defect, and it is detectable here and nowhere else in the metric set.

**Only reachable engines are automated.** Claude with web search, through the existing subscription credential path. Other engines are spot-checked by hand at low cadence and recorded as manual observations, clearly labeled as such. The published page states exactly which engines are automated, which are manual, and which are not covered at all. Understating coverage honestly is worth more here than a dashboard implying reach the method does not have.

### Carve-out from ADR 0002

`eval/citation/` is the **only** component permitted to invoke a model with network access, and the only model-invoking component permitted to run unattended on a schedule. The carve-out is narrow and explicit:

- It reads no upstream source and writes nothing into the corpus. It cannot affect generated documentation.
- It uses its own settings file with `WebSearch` enabled, separate from `pipeline/claude-settings.json`, which stays network-denied. Generation's grounding guarantee is untouched.
- It is capacity-bounded: a fixed question count at weekly cadence, sized so a run cannot consume a window that generation needs.
- It never uses `--bare`, like everything else in this repository.

Without this record, a scheduled job invoking a model would read as drift from ADR 0002 rather than a decision. The rule that CI invokes no model still holds for generation and for every channel.

### Optimization experiments and the holdout

Retrieval-fitness changes are treated as experiments with recorded hypotheses and dates, not as improvements assumed to work.

To make within-window comparison possible, a **holdout set** of corpus pages is excluded from optional retrieval-fitness enhancements. The line is strict: the holdout may differ only in *discoverability* affordances — inclusion in `llms.txt`, summary blocks, structured metadata. It never differs in accuracy, completeness, readability, or review status. Shipping knowingly worse documentation to real readers to serve an experiment is not acceptable, and the holdout design exists inside that limit.

### Publication

The citation page is **channel-native site content** under [ADR 0006](0006-one-corpus-many-channels.md) — it describes SourceWeave, not AnythingLLM, so it is not corpus, carries no upstream provenance, and is generated by `channels/site/` from committed evaluation output.

Consistent with FR-15: summarized history is committed; raw assistant responses go to `.runs/` and are not.

## Consequences

**A second credential path now runs unattended.** CI gains a scheduled job with model and network access. It touches nothing the documentation pipeline touches, but it is the first automation in this repository that can spend capacity without a human watching. The bound is the question-set size, which makes that number load-bearing — it is the only thing standing between a weekly job and a consumed window.

**Published numbers will sometimes be unflattering.** A public citation page will show low rates early, and may show the official docs cited more often indefinitely. That is the honest outcome and it is published anyway; a metric that only appears when favorable is not a measurement practice. The credible portfolio claim is the method and its limits, not the number.

**Causal claims stay bounded.** Even with the holdout, this is a small sample against uncontrolled external systems. Results support "consistent with" and not "caused by," and the page says so. Overclaiming here would be more damaging to the portfolio goal than reporting a weak signal plainly.

**The question set becomes a maintained asset.** It has to stay fixed for comparability, yet stay representative as AnythingLLM changes. Those pull against each other. Versioning it and breaking the trend line on purpose when it changes is better than silently editing questions and comparing across a discontinuity.

**Accuracy-when-cited is the sleeper value.** Measuring whether assistants answer *correctly* using SourceWeave catches a failure mode nothing else in §10 reaches: content that is accurate on the page but misleads once retrieved out of context. That is a real defect class for the primary audience in ADR 0005, and this is the only instrument that sees it.
