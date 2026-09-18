# site/

The Docusaurus project, and Netlify's base directory. Licensed MIT; the generated content it renders is CC BY 4.0.

This is a **channel**, not the product — it renders the corpus and does not own it ([ADR 0006](../docs/decisions/0006-one-corpus-many-channels.md)). "Hand-maintained" applies to the shell here (theme, config, landing page), not to the content, which is synced in and fully automated.

```bash
npm install
npm start          # dev server
npm run build      # production build; CI runs this
npm run typecheck  # tsc, not run by build -- wire into CI with issue #7
npm run serve      # serve the built output locally
```

Scaffolded with `create-docusaurus` classic, **TypeScript**. Note that `npm run build` does not type-check; `tsc` is a separate script, so CI has to run it explicitly or type errors ship silently.

## What was removed from the template

| Removed | Why |
|---|---|
| Tutorial sample docs | Replaced by a single placeholder until M2. |
| `HomepageFeatures` component | Template marketing furniture. |
| All template images | Docusaurus branding. This project ships no borrowed branding, upstream or otherwise — hence no favicon or logo yet. Site identity is a later, deliberate choice. |
| `editUrl` | Pages are generated, and regenerated when their source changes. An "edit this page" link would invite edits the next run overwrites. Corrections belong in the pipeline, the prompts, or the review step. |

## The blog is deferred, not rejected

`blog: false` until M2 — issue #13.

It is not unnecessary. FR-38 requires retrieval-fitness changes to be recorded experiments with a dated hypothesis and a result, and no other artifact fits: ADRs are immutable so they cannot accumulate findings, the PRD holds requirements, and the citation page shows the number rather than what it meant. FR-24 wants release notes for the same reason.

It waits because an empty blog on a site with no content reads as abandoned, which is worse than not having one. Re-enabling is one config line and a directory.

## Configuration that maps to a requirement

These are not niceties. Each one implements something stated.

| Setting | Requirement | Status |
|---|---|---|
| `noIndex: true` | FR-22 | **Set.** Verified in built HTML as `<meta name=robots content="noindex, nofollow">` on every page. Stays until the metrics in PRD §10 reach threshold; removing it is a deliberate, recorded decision. |
| `onBrokenLinks: 'throw'` | FR-13 | **Set.** A broken link fails the build. Generated content makes link rot easy to introduce and easy to miss. |
| Unofficial statement, site-wide | FR-23 | **Not yet** — issue #6. Present on the landing page only. |
| AI-generation disclosure, site-wide | FR-23 | **Not yet** — issue #6. Present on the landing page only. |
| Version label on every page | FR-19 | **Not yet** — needs the provenance front matter that arrives with M2. |
| `url` | — | **Provisional** (`sourceweave.netlify.app`) until the Netlify site exists, issue #8. |

## Where the content comes from

At M0 there is none: `docs/` holds one placeholder page.

From M2, `docs/` stops being hand-written. `channels/site/` loads the reviewed corpus, applies the review gate so no page with `reviewed_by: null` can render, and writes Markdown here. At that point `site/docs/` becomes a derived directory and is gitignored.

> **Open question.** [ADR 0001](../docs/decisions/0001-pipeline-language.md) says Docusaurus reads `targets/<name>/docs/` directly; [ADR 0006](../docs/decisions/0006-one-corpus-many-channels.md) says it must not, because that bypasses the review gate and pushes Docusaurus-shaped front matter into the corpus. Both are merged and immutable. Tracked in issue #12, to be resolved before M2 when it first matters.

Either way, one constraint holds: **generated pages are plain Markdown with YAML front matter, not Docusaurus-specific MDX.** Where a component is genuinely needed, the component lives here and the page references it by name.

## Provenance display

Each generated page will carry a `sourceweave:` front matter block — upstream version, source files with digests, model, prompt version, reviewer. Surfacing that on the rendered page is what makes the AI-generation disclosure specific rather than a generic banner.

## Netlify

| Setting | Value |
|---|---|
| Base directory | `site` |
| Build command | `npm run build` |
| Publish directory | `site/build` |

Secrets live in Netlify environment variables, never in the repo (NFR-1). Once the corpus lives outside `site/`, the build needs whatever step puts it in place — decided alongside issue #12.
