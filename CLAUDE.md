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

## Commit and PR workflow

Standard sequence for any change:

1. Branch off `main` — never commit to `main` directly.
2. Commit with a message that explains *why*, not just what. End with the Claude co-author trailer.
3. Push, open a PR, and wait for CI to pass.
4. **Merge with a merge commit** (`gh pr merge N --merge --delete-branch`), not squash or rebase. The merge commit preserves the link to the PR, and the PR writeup is part of what this project is meant to show (PRD §2).
5. **Delete the branch on merge.** Always — this is standard, not a per-PR decision.

Branch deletion is automated in two places so it does not depend on remembering: the repository has `delete_branch_on_merge` enabled, and `fetch.prune` is set so stale remote-tracking refs clear themselves. The `--delete-branch` flag is still the explicit habit.

The merge method is enforced the same way. `allow_squash_merge` and `allow_rebase_merge` are both disabled on the repository, so the only option the UI offers is a merge commit. Rule 4 above is therefore not something to remember at the moment of merging — which is when it was previously broken, by a dropdown that defaults to whatever was used last.

One commit on `main` predates that setting and is squashed (`52484c2`, PR #16). It was left alone deliberately. Force-pushing `main` to manufacture a merge commit that never happened would misrepresent the history, which costs more than the inconsistency does on a project whose point is a truthful record. Note that `git log --merges` does not list it; anything that needs a complete list of merged work should read the GitHub PR API rather than walk merge commits, which is the better source regardless since it carries the writeups.

## Planning and issue tracking

**A milestone is a sprint.** PRD §11 milestones map one-to-one onto GitHub Milestones — no separate cadence, no second planning structure to keep in sync. The PRD's exit criteria are the sprint goal; do not restate them elsewhere.

**Scope-boxed, not time-boxed.** A milestone closes when its exit criteria are met, not on a date. Under a fixed capacity ceiling throughput is not predictable enough to promise. Record actual start and end dates after the fact — that is where the release-lag metric comes from.

**The board is the plan. There are no implementation-plan documents.** Each milestone gets one tracking issue that decomposes it into child issues. That tracking issue *is* the plan: it lives where the work lives, so it cannot drift from the board the way a Markdown plan would. A design question that surfaces mid-build becomes an ADR, not a plan document.

**WIP limit: three issues in progress.** The failure mode for solo work is six things at 70%, not slow throughput. This matters more than any cadence.

**Keep the traceability chain intact.** It is one line per artifact and it is a large part of what this project demonstrates:

| Artifact | Line |
|---|---|
| Issue | `Implements: FR-NN` |
| PR | `Closes #N` |
| ADR | `Closes: PRD §13 Qn` |

**FR status is decision state, not build state.** `Proposed → Decided` records that a choice was settled. Whether the code exists lives on the board and in PRD §11. Mixing them turns the PRD into a stale tracker.

**Never renumber a milestone without grepping `docs/decisions/` first.** Merged ADRs cite milestone numbers — ADR 0002 pins evaluation calibration to M4, ADR 0003 pins the first generation slice to M2. Records are immutable, so renumbering past a cited milestone silently falsifies a record that cannot be edited. Insert new phases after the last cited number instead. This has already nearly happened once.

## Decision records

Decisions go in `docs/decisions/` as numbered records, not in commit messages or scattered comments. Records are immutable once merged; to change one, add a record that supersedes it.

When closing a PRD §13 open question, say so in the record's `Closes:` line.

**Never put a closing keyword near an issue reference, even negated.** GitHub matches `fix`, `fixes`, `closes`, `resolves` and their variants followed by a `#` reference, and does not parse negation. A phrase of the form *"what this does not fix: #NNN"* closes issue NNN.

Write "issue 32" without the `#`, or phrase so no keyword precedes the reference.

**Write examples of this rule with a placeholder, never a real issue number.** The rule was first added in a commit whose message quoted the original failure verbatim — and the quotation closed the same issue a second time, eighteen hours after the first. A documented example must not be executable. This is also why the rule is stated here rather than trusted to care: it recurred while someone was actively writing it down.

## Working references

`temp/observations/architecture/` holds quick-reference documents describing what the system is and does. They are gitignored on purpose — personal reference material, not repository documentation — and they restate the PRD and ADRs deliberately, which means they drift.

Refresh them at two points:

1. **When an ADR merges.** Add its entry to `04-decisions-index.md`, and check whether `03-constraints-that-shape-everything.md` gained or lost a constraint.
2. **When a milestone closes.** Re-run all of them against the repository, and say in the milestone tracking issue's completion comment that they were refreshed.

Each file carries a *reviewed as of* date. `06-current-state.md` goes stale fastest and should be treated as wrong until re-verified.

The second trigger carries more weight than it looks. These files are not committed, so no CI check and no code review can catch drift in them — the completion comment is the only trace that a refresh happened. This is the same exposure that ADR 0008 records for decision records themselves, and the same reason four separate instructions went stale in a single day when the upstream submodule landed.

## Tone for generated documentation

Until `style-guide/STYLE.md` exists, these hold:

- Describe what the pinned source actually shows. A claim the source does not support is a defect, not a stylistic choice.
- No marketing language, and no Mintplex branding.
- Label the version being described.
- Prefer short sentences and concrete examples over hedged generalities.

Once the style guide exists, it supersedes this section.
