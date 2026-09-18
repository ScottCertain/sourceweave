# targets/anythingllm/

Target-specific material for [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) by Mintplex Labs.

Everything specific to this target lives here, so `pipeline/` and `eval/` stay reusable across targets (PRD NFR-5, G6).

> **Independent and unofficial.** Not affiliated with, endorsed by, or supported by Mintplex Labs.

## Upstream facts

Confirmed by inspection on 2026-09-16, closing PRD §13 Q8 and Q9:

| | |
|---|---|
| Code repo | `Mintplex-Labs/anything-llm` — **MIT**, default branch `master` |
| Docs repo | `Mintplex-Labs/anythingllm-docs` — **MIT**, default branch `main` |
| Latest release | `v1.16.1`, published 2026-08-27 |
| OpenAPI spec | **`server/swagger/openapi.json`** — committed in the repo |

The OpenAPI spec being a committed file rather than server-emitted output is the reason API reference is the first generation slice: it gives M2 a structured source of truth and needs no running instance. See [ADR 0003](../../docs/decisions/0003-upstream-integration.md).

## Layout

| Path | Contents | Status |
|---|---|---|
| `upstream/` | Submodule: `anything-llm`, pinned to `v1.16.1` | **Added** (M1) |
| `official-docs/` | Submodule: `anythingllm-docs`, comparison baseline only | Deferred to M6 — see below |
| `docs/` | Generated and reviewed output (CC BY 4.0) | Empty until M2 |

## Working with the submodule

```bash
# after cloning, if you did not use --recurse-submodules
git submodule update --init targets/anythingllm/upstream
```

**Do not initialize recursively.** `anything-llm` carries its own submodules — `embed` and `browser-extension` — that are out of scope and expensive to clone. Use `git submodule update --init`, never `--init --recursive`. A correct checkout shows those two as uninitialized:

```
$ git -C targets/anythingllm/upstream submodule status
-385d36c0...  browser-extension
-7e5c6afc...  embed
```

The leading `-` means not cloned. That is the desired state.

**Do not shallow-clone this submodule.** `provenance.pinned_version()` reads the version with `git describe --tags --exact-match`. A shallow clone typically lacks tags, so it would not fail — it would silently fall back to a `master@sha` version string, and every generated page would record a weaker pin. The failure would only surface when reading provenance much later.

## Why `official-docs/` is not here yet

[ADR 0003](../../docs/decisions/0003-upstream-integration.md) decides both repos are pinned submodules, and that still holds. What changed is *when* the second one gets added.

`anythingllm-docs` is roughly 306 MB — about three times the size of `anything-llm` — and nothing reads it until the comparison work at M6 (FR-16, FR-17). Netlify cannot be told to skip submodule checkout, so anything in the repository is cloned by every build whether the build wants it or not.

Carrying 306 MB through five milestones to hold a baseline nothing reads is a poor trade, so it is added at M6. This is sequencing rather than a change of decision, so no superseding record is needed.

## Read-only rules

Both submodules are inputs. Two rules, and the second is a legal one:

1. Nothing in this repository writes to `upstream/` or `official-docs/`.
2. **No content is ever copied out of `official-docs/` into `docs/`.** The official docs are a comparison baseline for gap and drift analysis (PRD FR-16, FR-17), never a source to draw from. Copying would violate a stated non-goal and would make the "independent" claim false.

Generated prose is grounded in `upstream/` — the code — because that is the source of truth for behavior.
