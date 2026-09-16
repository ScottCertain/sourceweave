# 0001. Python for pipeline and evaluation, Node for the site

**Status:** Accepted
**Date:** 2026-09-16
**Closes:** PRD §13 Q2

## Context

The PRD left the implementation language open: Node/TypeScript to match Docusaurus, Python, or a mix.

The workloads are not alike. The site is a Docusaurus project and is unavoidably Node. The pipeline and evaluation harness do context assembly, text processing, structured scoring, and trend analysis over evaluation results — work where Python's ecosystem is stronger, and where the code is closer to data analysis than to web tooling.

Evaluation (PRD FR-11, FR-12, FR-15) is the part most likely to grow: claim extraction, scoring aggregation, calibration against human judgment, and quality trends over time.

## Decision

- `pipeline/` and `eval/` are Python 3.11+, managed by a single root `pyproject.toml`.
- `site/` is a standalone Node project, the Netlify base directory.
- The two sides communicate through the filesystem and through committed artifacts, not through a shared runtime. The pipeline writes Markdown and provenance sidecars into `targets/<name>/docs/`; Docusaurus reads that directory.

## Consequences

- Two toolchains to install, two sets of CI steps, two dependency files. Accepted.
- The filesystem boundary keeps `site/` swappable. If Docusaurus is ever replaced, the pipeline does not change.
- Generated output must be plain Markdown with front matter, not Docusaurus-specific MDX components, or the boundary leaks. Where an MDX component is genuinely needed, the pipeline emits it as content and the component lives in `site/`.
- Python's weaker story for consuming the Docusaurus build means link-checking and build verification (FR-13) run on the Node side, in CI, rather than in `eval/`.
