import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

// Placeholder landing page for M0. The site-wide unofficial and AI-generation
// notice required by FR-23 is issue #6, not this file.

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description="Independent, unofficial documentation for AnythingLLM, generated from pinned source and reviewed before publication.">
      <header className={clsx('hero', styles.heroBanner)}>
        <div className="container">
          <Heading as="h1" className="hero__title">
            {siteConfig.title}
          </Heading>
          <p className="hero__subtitle">{siteConfig.tagline}</p>
          <div className={styles.buttons}>
            <Link className="button button--secondary button--lg" to="/docs/">
              Read the docs
            </Link>
          </div>
        </div>
      </header>
      <main className={styles.main}>
        <div className="container">
          <p>
            SourceWeave reads a pinned version of an open-source project's
            source code, drafts documentation from it with a language model,
            scores that output for style and factual accuracy, and publishes
            the result only after a human has reviewed it.
          </p>
          <p>
            The first target is AnythingLLM. This site is{' '}
            <strong>independent and unofficial</strong>: it is not affiliated
            with, endorsed by, or supported by Mintplex Labs. For official
            documentation see{' '}
            <a href="https://docs.anythingllm.com">docs.anythingllm.com</a>.
          </p>
          <p>
            Documentation here is drafted by an automated pipeline and may
            contain errors. Every page records the source it was generated
            from and the upstream version it describes.
          </p>
        </div>
      </main>
    </Layout>
  );
}
