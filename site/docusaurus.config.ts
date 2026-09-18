import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This is a channel, not the product. It renders the corpus; it does not own
// it. See docs/decisions/0006-one-corpus-many-channels.md.

const config: Config = {
  title: 'SourceWeave',
  tagline: 'Independent documentation for AnythingLLM, generated from pinned source',

  // FR-22. Stays true until the quality metrics in PRD section 10 reach their
  // thresholds. Removing it is a deliberate, recorded decision -- not a tidy-up.
  noIndex: true,

  future: {
    v4: true,
  },

  // Provisional until the Netlify site exists (issue #8).
  url: 'https://sourceweave.netlify.app',
  baseUrl: '/',

  organizationName: 'ScottCertain',
  projectName: 'sourceweave',

  // A broken link is a build failure, not a warning. Generated content makes
  // link rot easy to introduce and easy to miss (FR-13).
  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // No editUrl. Pages here are generated from pinned source and
          // regenerated when that source changes -- editing the rendered page
          // would be overwritten on the next run. Corrections belong in the
          // pipeline, the prompts, or the review step.
        },
        // Blog deferred to M2, deliberately -- see issue #13.
        //
        // It is not unnecessary: FR-38 requires retrieval-fitness changes to be
        // recorded experiments with a dated hypothesis and a result, and no
        // other artifact fits. ADRs are immutable so they cannot accumulate
        // findings, the PRD holds requirements, and the citation page shows the
        // number rather than what it meant. FR-24 wants release notes for the
        // same reason.
        //
        // It waits because an empty blog on a site with no content reads as
        // abandoned, which is worse than not having one. Re-enabling is this
        // one line plus a directory.
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'SourceWeave',
      // No logo. The template's branding assets were removed rather than
      // shipped -- this project uses no borrowed branding, upstream or
      // otherwise. Site identity is a later, deliberate choice.
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/ScottCertain/sourceweave',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'This project',
          items: [
            {
              label: 'Source and decisions',
              href: 'https://github.com/ScottCertain/sourceweave',
            },
            {
              label: 'How it works',
              href: 'https://github.com/ScottCertain/sourceweave#how-it-works',
            },
          ],
        },
        {
          title: 'AnythingLLM',
          items: [
            {
              label: 'Official documentation',
              href: 'https://docs.anythingllm.com',
            },
            {
              label: 'Upstream repository',
              href: 'https://github.com/Mintplex-Labs/anything-llm',
            },
          ],
        },
      ],
      copyright:
        'Documentation CC BY 4.0, code MIT. Independent and unofficial -- not affiliated with or endorsed by Mintplex Labs.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
