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
| Unofficial statement, site-wide | FR-23 | **Set.** Non-closeable announcement bar plus the footer. Verified in CI on every rendered page. |
| AI-generation disclosure, site-wide | FR-23 | **Set.** Same two places, same CI check. |
| Version label on every page | FR-19 | **Not yet** — needs the provenance front matter that arrives with M2. |
| `url` | — | **Live** at [sourceweave.netlify.app](https://sourceweave.netlify.app). Changes to `sourceweave.scottcertain.com` when that domain is configured — issue #19. |

## The FR-23 notice

Two places, deliberately, because they fail differently.

The **announcement bar** is prominent but sits above the fold; a reader who scrolls straight into a page may never register it. The **footer** is easy to overlook but is permanent and terminates every page. Together they cover both reading patterns.

`isCloseable: false` is the load-bearing setting. A dismissible banner is dismissed once, per browser, and then never seen again — acceptable for a promotion, wrong for a disclosure. PRD §12 treats "users mistake SourceWeave for official docs" as a per-page risk, not a per-visitor one.

Both statements are checked in CI against the rendered HTML, so losing either fails the build rather than shipping quietly.

## Where the content comes from

At M0 there is none: `docs/` holds one placeholder page.

From M2, `docs/` stops being hand-written. `channels/site/` loads the reviewed corpus, applies the review gate so no page with `reviewed_by: null` can render, and writes Markdown here. At that point `site/docs/` becomes a derived directory and is gitignored.

> **Open question.** [ADR 0001](../docs/decisions/0001-pipeline-language.md) says Docusaurus reads `targets/<name>/docs/` directly; [ADR 0006](../docs/decisions/0006-one-corpus-many-channels.md) says it must not, because that bypasses the review gate and pushes Docusaurus-shaped front matter into the corpus. Both are merged and immutable. Tracked in issue #12, to be resolved before M2 when it first matters.

Either way, one constraint holds: **generated pages are plain Markdown with YAML front matter, not Docusaurus-specific MDX.** Where a component is genuinely needed, the component lives here and the page references it by name.

## Provenance display

Each generated page will carry a `sourceweave:` front matter block — upstream version, source files with digests, model, prompt version, reviewer. Surfacing that on the rendered page is what makes the AI-generation disclosure specific rather than a generic banner.

## Netlify

Live at **[sourceweave.netlify.app](https://sourceweave.netlify.app)**, deploying from `main`.

Build settings come from [`netlify.toml`](../netlify.toml) at the repository root, not from the Netlify dashboard — settings that live only in a UI are invisible in review and cannot be reproduced from a commit (NFR-2). `netlify.toml` also overrides the dashboard where both define a value, so the file is the source of truth.

| Setting | Value | Source |
|---|---|---|
| Base directory | `site` | `netlify.toml` |
| Build command | `npm run build` | `netlify.toml` |
| Publish directory | `site/build` | `netlify.toml` |
| Node version | 20 | `netlify.toml`, matching CI |
| `X-Robots-Tag` | `noindex, nofollow` on `/*` | `netlify.toml` |

The header is FR-22 one layer below the meta tag. It covers what a `<meta>` cannot: non-HTML assets, crawlers that read headers without parsing the document, and deploy previews, which get a public URL on every pull request. Both come off together when PRD §10 metrics reach threshold, or the site ends up half-indexed.

Secrets live in Netlify environment variables, never in the repo (NFR-1). Once the corpus lives outside `site/`, the build needs whatever step puts it in place — decided alongside issue #12.
