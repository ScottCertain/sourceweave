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
| `upstream/` | Submodule: `anything-llm`, pinned to a release tag | Not yet added (M1) |
| `official-docs/` | Submodule: `anythingllm-docs`, comparison baseline only | Not yet added (M1) |
| `docs/` | Generated and reviewed output (CC BY 4.0) | Empty until M2 |

## Adding the submodules (M1)

```bash
git submodule add https://github.com/Mintplex-Labs/anything-llm.git \
  targets/anythingllm/upstream
git -C targets/anythingllm/upstream checkout v1.16.1

git submodule add https://github.com/Mintplex-Labs/anythingllm-docs.git \
  targets/anythingllm/official-docs

git add .gitmodules targets/anythingllm
git commit -m "Pin AnythingLLM upstream to v1.16.1"
```

**Do not initialize recursively.** `anything-llm` carries its own submodules (embed widget, browser extension) that are out of scope and expensive to clone. Use `git submodule update --init`, not `--init --recursive`.

## Read-only rules

Both submodules are inputs. Two rules, and the second is a legal one:

1. Nothing in this repository writes to `upstream/` or `official-docs/`.
2. **No content is ever copied out of `official-docs/` into `docs/`.** The official docs are a comparison baseline for gap and drift analysis (PRD FR-16, FR-17), never a source to draw from. Copying would violate a stated non-goal and would make the "independent" claim false.

Generated prose is grounded in `upstream/` — the code — because that is the source of truth for behavior.
