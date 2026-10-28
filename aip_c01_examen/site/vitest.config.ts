import {defineConfig} from 'vitest/config';

export default defineConfig({
  esbuild: {jsx: 'automatic'},
  test: {
    maxWorkers: 2,
    alias: {
      '@docusaurus/useBaseUrl': '@docusaurus/core/lib/client/exports/useBaseUrl.js',
      '@docusaurus/useGlobalData': '@docusaurus/core/lib/client/exports/useGlobalData.js',
      '@docusaurus/router': 'react-router-dom',
    },
  },
});
