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

  // The live deploy target. Changes to https://sourceweave.scottcertain.com
  // once that domain is configured (issue #19) -- this value feeds canonical
  // links and the sitemap, so it has to name a host that actually answers.
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
    // FR-23, first half: the unofficial statement and the AI-generation
    // disclosure, site-wide.
    //
    // isCloseable: false is the load-bearing setting. A dismissible banner is
    // dismissed once, per browser, and then never seen again -- which is fine
    // for a promotion and wrong for a disclosure. PRD section 12 lists "users
    // mistake SourceWeave for official docs" as a risk to mitigate on every
    // page, not once per visitor.
    announcementBar: {
      id: 'unofficial-ai-generated',
      content:
        'Independent and unofficial. These pages are drafted by an automated pipeline and may contain errors. Official documentation: <a target="_blank" rel="noopener" href="https://docs.anythingllm.com">docs.anythingllm.com</a>',
      backgroundColor: '#563d0e',
      textColor: '#fdf3d8',
      isCloseable: false,
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
      // FR-23, second half. The banner is prominent; this is permanent and
      // sits at the end of every page, so the statement survives a reader who
      // scrolls past the top of the page without registering it.
      copyright:
        'Independent and unofficial -- not affiliated with, endorsed by, or supported by Mintplex Labs. ' +
        'Documentation on this site is drafted by an automated pipeline and reviewed by a human before publication; ' +
        'every page records the source it was generated from. ' +
        'Documentation CC BY 4.0, code MIT.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
