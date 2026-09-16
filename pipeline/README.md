# pipeline/

Generation. Reads pinned upstream source, drafts documentation grounded in it, and writes Markdown with provenance front matter into `targets/<name>/docs/`.

Licensed MIT.

## Modules

| Module | Responsibility |
|---|---|
| `claude_client.py` | The **only** place this project invokes a model. Wraps `claude -p`. |
| `provenance.py` | Records what produced each page, and detects when a page is stale. |

## The two invariants

Both live in `claude_client.py` and both come from [ADR 0002](../docs/decisions/0002-model-access-via-claude-subscription.md):

1. **`--bare` is never passed.** Bare mode does not read subscription credentials and falls back to `ANTHROPIC_API_KEY`. What makes this worth a hard guard is that it *fails silently* — adding the flag raises no error, and the run just executes against a different credential path with nothing in the output saying so. An inherited `ANTHROPIC_API_KEY` is also stripped from the subprocess environment, so a key set for an unrelated tool cannot quietly redirect a run.
2. **Runs are throttled and resumable.** A fixed capacity ceiling is the binding constraint. A run that reaches it raises `RateLimited`, checkpoints, and stops — it never retries into a wall.

`TestBillingInvariants` fails the build if either protection is removed.

## Designing for the ceiling

The capacity ceiling is the reason several pieces here exist at all. Under an elastic metered budget you could regenerate everything on every run and none of this would be needed:

| Piece | Exists because |
|---|---|
| `Provenance.sources` digests | Staleness must be a fact, not a guess — only changed pages get regenerated |
| `RateLimited` as its own type | Callers need to distinguish "stop and resume later" from "this failed" |
| Throttling between invocations | Spacing work across the window instead of front-loading it |
| `Provenance.ambient_context` | Detecting when the generation environment drifted (see below) |

## Grounding

Generation is grounded in pinned inputs, not model memory (PRD FR-4). In practice that means the prompt carries the actual source text, and the model is instructed to describe only what the supplied source shows. A claim the source does not support is a defect that evaluation should catch.

## Planned structure

Not yet built — these are the M2 pieces:

| Module | Responsibility |
|---|---|
| `cli.py` | Entry point, exposed as the `sourceweave` command |
| `context.py` | Assembles grounded context from the pinned submodule |
| `openapi.py` | Parses `server/swagger/openapi.json` for API reference generation |
| `prompts/` | Versioned prompt files; the version is recorded in provenance |
| `render.py` | Writes Markdown with provenance front matter |

## Prompt versioning

Prompts are files, versioned in Git, and the version identifier goes into every page's provenance. A build is reproducible from a commit only if the prompts are pinned alongside the source (PRD NFR-2), so prompts are never inlined in Python.

## Reproducibility and ambient context

Because `--bare` cannot be used, a `claude -p` run loads ambient context: settings, `CLAUDE.md`, and anything configured in the working directory or `~/.claude`. The machine contributes to the run, which is in tension with NFR-2.

The gap is narrowed rather than closed:

- `claude-settings.json` is pinned and passed with `--settings` instead of inherited. `ClaudeClient` refuses to construct if it is missing, so a run cannot silently fall back to machine config.
- `CLAUDE.md` is version-controlled, so the largest ambient input moves with the commit.
- The pipeline configures no MCP servers and relies on no skills.
- `ambient_fingerprint()` digests both, and the result lands in `Provenance.ambient_context`.

That last one makes environment drift **detectable, not prevented**. A page generated under different ambient context carries a different fingerprint, so you can find it after the fact. A hook in someone's `~/.claude` would still run. ADR 0002 records what to do if this project ever gains contributors.

### `claude-settings.json` is part of the reproducibility surface

Treat a change to it the way you would treat a prompt change — it changes generated output, and it changes every subsequent page's fingerprint.

Its deny list is doing real work. Blocking `Bash`, `WebFetch`, and `WebSearch` makes grounding (PRD FR-4) an **enforced property** rather than a prompt instruction: generation physically cannot reach the network, so it cannot describe anything but the pinned source. A prompt that says "use only the supplied source" is a request; a denied tool is a guarantee.

Permissions for working in the repo by hand belong in `.claude/settings.json`, not here. That file is deliberately excluded from the fingerprint — Claude Code writes to it when you approve a permission, and including it would report drift across the whole corpus for a change that never touched generation.
