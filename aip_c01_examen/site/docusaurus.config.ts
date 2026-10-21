import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'AIP-C01 Exam Prep',
  tagline:
    'Pass the AWS Certified Generative AI Developer – Professional (AIP-C01) exam',
  favicon: 'img/favicon.svg',

  url: 'https://farithjhg.github.io',
  baseUrl: '/aws-bedrock-agentcore-course/aip_c01_examen/',

  organizationName: 'farithjhg',
  projectName: 'aws-bedrock-agentcore-course',

  trailingSlash: false,
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',

  // Build output lands in aip_c01_examen/ (the published subpath). The Docusaurus
  // source stays in aip_c01_examen/site/ and is never served. See SITE-README.md.
  outDir: '../',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themes: [
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        indexDocs: true,
        docsRouteBasePath: '/',
      },
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'AIP-C01 Exam Prep',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'courseSidebar',
          position: 'left',
          label: 'Course',
        },
        {
          href: 'https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md',
          label: 'AgentCore course',
          position: 'right',
        },
        {
          href: 'https://aws.amazon.com/certification/certified-generative-ai-developer-professional/',
          label: 'AWS exam page',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Related',
          items: [
            {
              label: 'AgentCore course',
              href: 'https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md',
            },
            {
              label: 'AWS AIP-C01 exam page',
              href: 'https://aws.amazon.com/certification/certified-generative-ai-developer-professional/',
            },
            {
              label: 'Official exam guide',
              href: 'https://docs.aws.amazon.com/aws-certification/latest/ai-professional-01/ai-professional-01.html',
            },
          ],
        },
      ],
      copyright:
        'AIP-C01 Exam-Prep Course. Part of the AWS Bedrock AgentCore repository.',
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
