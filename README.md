# SourceWeave

A generation-focused documentation system. It reads an open-source project's source code and releases, drafts documentation with AI, evaluates that output against a human-authored style guide and against the source of truth, and publishes the reviewed result as a Docusaurus site.

The first target is [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) by Mintplex Labs.

**Site:** [sourceweave.scottcertain.com](https://sourceweave.scottcertain.com) — published with `noIndex` until output quality meets the thresholds in [PRD §10](PRD.md#10-success-metrics). There is no generated documentation on it yet; the first section arrives at M2.

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
  targets/<name>/upstream/               pinned upstream source (read-only)
             │
             │   pipeline/ — drafts, grounded in that source
             ▼
  targets/<name>/docs/                   THE CORPUS — the only place
      page.md + provenance                documentation is written.
      reviewed_by: <human>                Committed. Reviewed here.
             │
             ▼
     ┌───────────────────────┐
     │  shared corpus loader │  excludes reviewed_by: null  (FR-26)
     │  one review gate      │  enforced once, for every channel
     └──────────┬────────────┘
                │
   ┌────────────┼─────────────┬──────────────────┐
   ▼            ▼             ▼                  ▼
channels/    channels/     channels/         channels/
 site/       llms-txt/      mcp/             workspace/
   │            │             │                  │
   ▼            ▼             ▼                  ▼
site/docs/   llms.txt     MCP server        document bundle
docusaurus   raw .md      + provenance             │
   │            │         + verification           │
   ▼            ▼             ▼                    ▼
Netlify     crawlers &   coding agents      the reader's own
 humans     assistants    (integrators)      AnythingLLM
```

`eval/` also reads the corpus — and `official-docs/` from M6 — to score it. It is not a channel because it publishes nothing.

1. **Pin** — upstream repos are Git submodules pinned to a release tag.
2. **Generate** — `pipeline/` assembles grounded context from the pinned source and drafts pages. Grounded in the pinned inputs, not model memory: generation is denied network access, so it cannot describe anything else.
3. **Evaluate** — `eval/` scores drafts for style-guide adherence and factual accuracy against source.
4. **Review** — a human edits the output and records themselves in `reviewed_by`. Those edits feed back into `style-guide/`.
5. **Publish** — each channel renders the reviewed corpus. No channel holds its own copy of documentation, and none can publish a page the gate excluded.

**Documentation is written in exactly one place.** Everything below the corpus is a rendering of it, which is why the review gate sits in the shared loader rather than in any one channel — four surfaces, one check. See [ADR 0006](docs/decisions/0006-one-corpus-many-channels.md).

| Channel | Serves | Arrives |
|---|---|---|
| `site/` | Humans; portfolio reviewers | M2 |
| `llms-txt/` | Crawlers and general assistants | M5 |
| `mcp/` | Integrating developers, through their coding agent | M5 |
| `workspace/` | End users, inside their own AnythingLLM | M7 |

The MCP channel is the differentiated one: a general documentation index can serve prose about AnythingLLM, but it cannot say which version a claim was verified against or whether the example runs. That metadata already exists for internal reasons, so exposing it is packaging rather than new capability.

**None of `channels/` exists yet.** Today `site/` is a plain Docusaurus project rendering a placeholder; the corpus is empty until M2.

## Repository layout

| Path | Contents | License |
|---|---|---|
| [pipeline/](pipeline/) | Generation scripts, prompts, CI glue (Python) | MIT |
| [eval/](eval/) | Style-adherence and accuracy scoring (Python) | MIT |
| `channels/` | Corpus renderers — site, `llms.txt`, MCP, workspace. *Not yet created; M2 onward.* | MIT |
| [style-guide/](style-guide/) | Human-authored style guide | CC BY 4.0 |
| [targets/anythingllm/](targets/anythingllm/) | Target-specific submodules and the corpus | CC BY 4.0 (docs) |
| [site/](site/) | Docusaurus project, Netlify base directory. Built by `channels/site/` — one channel among several | MIT |
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
git clone https://github.com/ScottCertain/sourceweave.git
cd sourceweave

# Upstream source, ~93 MB. Needed for generation; not for working on the site.
git submodule update --init targets/anythingllm/upstream

# Python side
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"

# Verify model access (should print the CLI version, not an auth error)
claude --version
```

**Do not clone with `--recurse-submodules`.** It is an alias of `--recursive` and is equivalent to `git submodule update --init --recursive`, so it pulls AnythingLLM's *own* submodules — the embed widget and browser extension — which are out of scope and expensive ([ADR 0003](docs/decisions/0003-upstream-integration.md)). Use the explicit init above.

A correct checkout leaves those uninitialized:

```
$ git -C targets/anythingllm/upstream submodule status
-385d36c0...  browser-extension
-7e5c6afc...  embed
```

The leading `-` means not cloned. That is the desired state.

Working only on `site/`? Skip the submodule entirely — the site is a channel and never reads upstream ([ADR 0006](docs/decisions/0006-one-corpus-many-channels.md)).

Copy `.env.example` to `.env` for local configuration. `.env` is gitignored and must never hold secrets that belong in CI.

## Status

Milestone **M1: Upstream wiring**. See [PRD §11](PRD.md#11-milestones) for scope and exit criteria, and [the milestones page](https://github.com/ScottCertain/sourceweave/milestones) for live progress.

| Milestone | Status |
|---|---|
| M0 Foundation | ✅ Complete |
| M1 Upstream wiring | 🟡 In progress |
| M2 First generation slice | ⬜ Not started |
| M3 Style guide v1 | ⬜ Not started |
| M4 Evaluation v1 | ⬜ Not started |
| M5 AI-mediated delivery | ⬜ Not started |
| M6 Comparison | ⬜ Not started |
| M7 Expansion | ⬜ Not started |

Milestones are scope-boxed: each closes when its exit criteria are met, not on a date.

## Acknowledgments

Gap and drift analysis compares SourceWeave output against the official [AnythingLLM documentation](https://github.com/Mintplex-Labs/anythingllm-docs) (MIT). Official docs are read-only input for comparison and are never copied or republished here.

AnythingLLM and the Mintplex Labs name are the property of their respective owners. SourceWeave uses no Mintplex branding.

## License

- **Code** — pipeline, evaluation, CI, and site configuration: [MIT](LICENSE)
- **Prose** — style guide, generated documentation, decision records, and write-ups: [CC BY 4.0](LICENSE-docs)
