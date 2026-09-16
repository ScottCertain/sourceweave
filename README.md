# SourceWeave

A generation-focused documentation system. It reads an open-source project's source code and releases, drafts documentation with AI, evaluates that output against a human-authored style guide and against the source of truth, and publishes the reviewed result as a Docusaurus site.

The first target is [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) by Mintplex Labs.

See [PRD.md](PRD.md) for the full product requirements, and [docs/decisions/](docs/decisions/) for the architecture decision record.

---

## ⚠️ Independent and unofficial

SourceWeave is an independent, unofficial project. It is **not affiliated with, endorsed by, or supported by Mintplex Labs**. It is not official AnythingLLM documentation, and it is not authoritative.

For official AnythingLLM documentation, see [docs.anythingllm.com](https://docs.anythingllm.com).

## 🤖 AI generation disclosure

Documentation in this repository is **drafted by an automated pipeline using a large language model**, then evaluated against a style guide and against the pinned upstream source, and reviewed by a human before publication.

Generated prose may contain errors. Every published page records its provenance: the source files it was generated from, the upstream version it describes, the model used, and the prompt version. Pages are labeled with the AnythingLLM version they describe.

The site is published with `noIndex: true` until output quality meets the thresholds in PRD §10.

---

## How it works

```
upstream source (pinned)  ──►  pipeline/  ──►  draft
                                                 │
                       style-guide/  ──►  eval/  ┤  scored for style + accuracy
                                                 │
                                          human review
                                                 │
                                targets/*/docs/  ──►  site/  ──►  Netlify
```

1. **Pin** — upstream repos are Git submodules pinned to a release tag.
2. **Generate** — `pipeline/` assembles grounded context from the pinned source and drafts pages. Generation is grounded in the pinned inputs, not model memory.
3. **Evaluate** — `eval/` scores drafts for style-guide adherence and factual accuracy against source.
4. **Review** — a human edits the output. Those edits feed back into `style-guide/`.
5. **Publish** — reviewed output is committed, built with Docusaurus, and deployed to Netlify.

## Repository layout

| Path | Contents | License |
|---|---|---|
| [pipeline/](pipeline/) | Generation scripts, prompts, CI glue (Python) | MIT |
| [eval/](eval/) | Style-adherence and accuracy scoring (Python) | MIT |
| [style-guide/](style-guide/) | Human-authored style guide | CC BY 4.0 |
| [targets/anythingllm/](targets/anythingllm/) | Target-specific submodules and generated output | CC BY 4.0 (docs) |
| [site/](site/) | Docusaurus project, Netlify base directory | MIT |
| [docs/decisions/](docs/decisions/) | Architecture decision records | CC BY 4.0 |
| [.github/workflows/](.github/workflows/) | CI | MIT |

Target-specific material is isolated under `targets/<name>/` so the pipeline and evaluation code stay reusable across targets (PRD NFR-5, G6).

## Requirements

| Tool | Version | Used for |
|---|---|---|
| Python | 3.11+ | `pipeline/`, `eval/` |
| Node.js | 20+ | `site/` (Docusaurus) |
| Claude Code CLI | current | Model access — see below |
| Git | with submodule support | Upstream pinning |

### Model access

Generation and evaluation invoke the **Claude Code CLI** (`claude -p`), which authenticates with a Claude subscription. No Anthropic API key is required.

This means the pipeline operates under a **fixed capacity ceiling** rather than an elastic metered budget — and that constraint is a design input, not a workaround. A pipeline that can regenerate everything on every run never has to answer which pages are actually stale, what is worth regenerating, or how a run survives interruption. Those questions are answered here in the design: per-file digests drive incremental regeneration, and a run that reaches the ceiling checkpoints and resumes.

See [ADR 0002](docs/decisions/0002-model-access-via-claude-subscription.md) for the full reasoning, including the reproducibility trade-off it accepts.

## Getting started

```bash
git clone --recurse-submodules https://github.com/ScottCertain/sourceweave.git
cd sourceweave

# Python side
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"

# Verify model access (should print the CLI version, not an auth error)
claude --version
```

Copy `.env.example` to `.env` for local configuration. `.env` is gitignored and must never hold secrets that belong in CI.

## Status

Milestone **M0: Foundation** — repo scaffold. See PRD §11 for the milestone plan.

| Milestone | Status |
|---|---|
| M0 Foundation | 🟡 In progress |
| M1 Upstream wiring | ⬜ Not started |
| M2 First generation slice | ⬜ Not started |
| M3 Style guide v1 | ⬜ Not started |
| M4 Evaluation v1 | ⬜ Not started |
| M5 Comparison | ⬜ Not started |
| M6 Expansion | ⬜ Not started |

## Acknowledgments

Gap and drift analysis compares SourceWeave output against the official [AnythingLLM documentation](https://github.com/Mintplex-Labs/anythingllm-docs) (MIT). Official docs are read-only input for comparison and are never copied or republished here.

AnythingLLM and the Mintplex Labs name are the property of their respective owners. SourceWeave uses no Mintplex branding.

## License

- **Code** — pipeline, evaluation, CI, and site configuration: [MIT](LICENSE)
- **Prose** — style guide, generated documentation, decision records, and write-ups: [CC BY 4.0](LICENSE-docs)
