# SourceWeave — working notes for Claude Code

SourceWeave generates documentation for an open-source target from its pinned source, evaluates the output, and publishes it. See [PRD.md](PRD.md) for requirements and [docs/decisions/](docs/decisions/) for decisions already made and closed.

## Hard rules

**Never add `--bare` to a `claude` invocation in this repository.** Bare mode does not read subscription credentials and falls back to `ANTHROPIC_API_KEY`. It does not error when you add it — the run simply executes against a different credential path, silently. This project is designed around a fixed subscription capacity ceiling, deliberately; see [ADR 0002](docs/decisions/0002-model-access-via-claude-subscription.md).

**Never add an Anthropic SDK dependency.** All model access goes through `pipeline/sourceweave_pipeline/claude_client.py`. If a second call site appears, that is a bug.

**Never copy content out of `targets/*/official-docs/`.** It is a comparison baseline, not a source. Copying breaks a stated non-goal and makes the project's independence claim false.

**Never write to `targets/*/upstream/` or `targets/*/official-docs/`.** They are read-only submodules.

**No secrets in the repo.** Not in `.env`, not in committed configs, not in prompt files. CI uses a `CLAUDE_CODE_OAUTH_TOKEN` repository secret; Netlify uses environment variables.

**Do not publish unreviewed generated content.** A page whose provenance has `reviewed_by: null` has not been through human review. Fully autonomous publishing is a stated non-goal.

## Layout

| Path | Contents | License |
|---|---|---|
| `pipeline/` | Generation (Python) | MIT |
| `eval/` | Scoring (Python) | MIT |
| `style-guide/` | Style guide, written from real edits | CC BY 4.0 |
| `targets/<name>/` | Target-specific: submodules + generated docs | CC BY 4.0 (docs) |
| `site/` | Docusaurus, Netlify base directory | MIT |
| `docs/decisions/` | ADRs | CC BY 4.0 |

Target-specific material stays under `targets/<name>/`. If something target-specific is about to be written into `pipeline/` or `eval/`, that is the wrong location — the pipeline must stay reusable (PRD NFR-5, G6).

## Commands

```bash
# Python
pip install -e ".[dev]"
ruff check .
ruff format .
pytest

# Site (once scaffolded)
cd site && npm run build
```

## Conventions

- **Prompts are files**, versioned in Git, referenced by version in each page's provenance. Never inline a prompt in Python — it breaks reproducibility (PRD NFR-2).
- **`pipeline/claude-settings.json` is pinned config, not a scratch file.** Changing it changes generated output and every subsequent page's fingerprint. Permissions for working in the repo by hand go in `.claude/settings.json` instead.
- **Every generated page carries provenance front matter**: source files with digests, upstream version, model, prompt version.
- **Push style rules into Vale** wherever they can be expressed mechanically. A linter rule is deterministic and spends no capacity; a model-scored rule spends some on every run.
- **Summarized scores are committed; raw run logs are not.** Logs go to `.runs/`, which is gitignored (PRD FR-15).
- **Regeneration is incremental.** Regenerate a page only when its recorded source digests have changed. The capacity ceiling makes this a requirement, not an optimization — a full-corpus run exhausts the window before it finishes.
- **A run that hits the ceiling checkpoints and stops.** Catch `RateLimited`, save progress, exit cleanly. Never retry into a wall.

## Decision records

Decisions go in `docs/decisions/` as numbered records, not in commit messages or scattered comments. Records are immutable once merged; to change one, add a record that supersedes it.

When closing a PRD §13 open question, say so in the record's `Closes:` line.

## Tone for generated documentation

Until `style-guide/STYLE.md` exists, these hold:

- Describe what the pinned source actually shows. A claim the source does not support is a defect, not a stylistic choice.
- No marketing language, and no Mintplex branding.
- Label the version being described.
- Prefer short sentences and concrete examples over hedged generalities.

Once the style guide exists, it supersedes this section.
