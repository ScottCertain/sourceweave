# 0004. MIT for code, CC BY 4.0 for prose

**Status:** Accepted
**Date:** 2026-09-16
**Closes:** PRD §14 (moves the licensing rows from Proposed to Decided)

## Context

The repository holds two kinds of work with different reuse expectations. The pipeline and evaluation harness are software, and are most useful to others under a permissive software license. The style guide and generated documentation are prose, where a license built for text and carrying an attribution requirement fits better than one written for code.

A single top-level `LICENSE` cannot express this, and a repository that ships prose under an unqualified MIT license sends the wrong signal about attribution.

There is also a third category: the upstream submodules, which are third-party MIT work included as read-only input and not relicensed by anything here.

## Decision

| Scope | License | File |
|---|---|---|
| `pipeline/`, `eval/`, `site/`, `.github/` | MIT | `LICENSE` |
| `style-guide/`, `targets/*/docs/`, `docs/`, `PRD.md`, `README.md` | CC BY 4.0 | `LICENSE-docs` |
| `targets/*/upstream/`, `targets/*/official-docs/` | Upstream's own (MIT) | Not ours to set |

`LICENSE-docs` states its scope explicitly, names what it does not cover, and links the canonical CC legal code. The README carries the split in its License section.

Published pages carry the AI-generation disclosure and the unofficial-project statement (FR-22, FR-23). The disclosure is also restated in `LICENSE-docs`, so it travels with the text if the prose is reused downstream.

## Consequences

- Anyone reusing generated prose must attribute. Anyone reusing the pipeline need not, beyond the MIT notice.
- Two license files means the scope statements must stay accurate as directories are added. A new top-level directory requires a decision about which license covers it, and an update to `LICENSE-docs` and the README table.
- GitHub reports a single repository license (MIT, from `LICENSE`). The prose license is discoverable only by reading. Accepted; the README table is the mitigation.
- The copyright status of AI-generated prose is unsettled (PRD §12). Applying CC BY 4.0 asserts rights that may be thinner than they appear for machine-generated passages. The PRD's position stands: disclose AI generation, rely on human editing, selection, and arrangement, and revisit if legal guidance changes. This record does not resolve that question and should not be read as claiming it is resolved.
