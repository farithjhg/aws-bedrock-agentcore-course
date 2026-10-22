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

  // Build output goes to the default aip_c01_examen/site/build. The Pages
  // workflow copies that compiled output into aip_c01_examen/ so it is served
  // at baseUrl. (outDir is a Docusaurus v3 CLI flag, not a config field, and
  // pointing it at the parent dir would delete the source during the build.)

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
