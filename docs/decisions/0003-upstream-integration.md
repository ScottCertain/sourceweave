# 0003. Upstream repos as pinned Git submodules

**Status:** Accepted
**Date:** 2026-09-16
**Closes:** PRD §13 Q8, Q9; confirms PRD §6 "Integration method (Proposed)"

## Context

Generation must be grounded in a known, fixed version of the target (PRD FR-4, NFR-2). Two upstream repositories are involved: the code, which is the source of truth, and the official docs, which are a read-only comparison baseline.

Two PRD open questions and one risk gated this. All three are now resolved by inspection:

| Question | Finding |
|---|---|
| Q8 — license of `anything-llm` | **MIT.** Default branch `master`. Latest release at time of writing: `v1.16.1` (2026-08-27). |
| Q9 — location of the OpenAPI spec | **`server/swagger/openapi.json`**, committed in the repo. |
| §12 risk — "confirm the license before reading code into the pipeline" | Cleared. Both upstream repos are MIT. |

`anythingllm-docs` is also MIT, default branch `main`.

The OpenAPI finding is the significant one. Because the spec is a committed file rather than something emitted only by a running server, API reference generation (FR-5) needs the pinned submodule and nothing else. No Docker instance, no running AnythingLLM, no network at generation time.

## Decision

Both upstream repositories are Git submodules under `targets/anythingllm/`:

| Path | Repo | Pin |
|---|---|---|
| `upstream/` | `Mintplex-Labs/anything-llm` | A release tag, starting at `v1.16.1` |
| `official-docs/` | `Mintplex-Labs/anythingllm-docs` | A commit on `main` |

- Both are **read-only inputs**. Nothing in this repository writes to them, and no content is copied out of `official-docs/` into published pages.
- Version bumps are ordinary reviewable commits (FR-1). The submodule pointer change *is* the version record.
- **Submodules are not initialized recursively.** `anything-llm` contains its own submodules (embed widget, browser extension). Those components are out of scope, and a recursive clone costs significant time and disk for material the pipeline does not read. If a component comes into scope, initialize that one submodule explicitly and record it here.

**API reference is the first generation slice (M2), closing PRD §13 Q4.** The committed OpenAPI spec gives it a structured, machine-readable source of truth, which makes it the section where accuracy scoring (FR-12) is most tractable to build first.

## Consequences

- Generation is fully offline and reproducible from a commit: the submodule pointers pin the inputs, and the prompt version files pin the instructions (NFR-2).
- Contributors must clone with `--recurse-submodules`, or run `git submodule update --init` afterward. Documented in the README.
- A checkout is large. `anything-llm` is a substantial repository even without its nested submodules.
- Upstream release watching (FR-2) reduces to: compare the pinned tag against the latest release tag, and open an issue or draft PR when they differ.
- Drift detection (FR-3) reduces to diffing `server/swagger/openapi.json` between the pinned tag and `master` — a structured diff on a structured file, rather than heuristics over prose.
- Both upstream licenses being MIT means reading code into the pipeline carries no license friction. Attribution obligations attach to any *copied* code; the pipeline reads source to describe behavior and does not vendor it.
