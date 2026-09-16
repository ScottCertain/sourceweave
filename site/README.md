# site/

The Docusaurus project. Netlify's base directory. Licensed MIT (the generated content it renders is CC BY 4.0).

## Not yet scaffolded

This is M0's remaining work. To scaffold:

```bash
npx create-docusaurus@latest site classic --typescript
```

## Required configuration

These are not optional niceties — each maps to a stated requirement:

| Setting | Requirement | Note |
|---|---|---|
| `noIndex: true` | PRD FR-22 | Stays until quality metrics hit their thresholds. Removing it is a deliberate, recorded decision. |
| Version label on every page | PRD FR-19 | Read from the page's `sourceweave.upstream_version` provenance field |
| Unofficial statement | PRD FR-23 | Site-wide, in a banner or footer, visible on every page |
| AI-generation disclosure | PRD FR-23 | Site-wide, alongside the unofficial statement |
| Docs directory | — | Points at `../targets/anythingllm/docs`, outside `site/` |

## The content boundary

Docusaurus reads generated Markdown from `targets/<name>/docs/`. It does not own that content and nothing in `site/` writes to it.

This keeps the site swappable ([ADR 0001](../docs/decisions/0001-pipeline-language.md)). The practical constraint that falls out: **generated pages are plain Markdown with YAML front matter, not Docusaurus-specific MDX.** Where a component is genuinely needed, the component lives here and the page references it by name.

## Provenance display

Each page carries a `sourceweave:` block in its front matter — upstream version, source files, model, prompt version, reviewer. Surfacing it on the rendered page is what makes the AI-generation disclosure specific rather than a generic banner, and it is a good portfolio detail.

## Netlify

| Setting | Value |
|---|---|
| Base directory | `site` |
| Build command | `npm run build` |
| Publish directory | `site/build` |

Submodules must be initialized in the Netlify build for the docs directory to resolve. Secrets live in Netlify environment variables, never in the repo (PRD NFR-1).
