import {readFile} from 'node:fs/promises';
import path from 'node:path';
import CopyPlugin from 'copy-webpack-plugin';
import {aliasedSitePathToRelativePath} from '@docusaurus/utils';
import type {LoadContext, Plugin} from '@docusaurus/types';
import {parseChatIndex} from '../../src/chat/retrieval';
import type {ChatSiteData} from '../../src/chat/retrieval';
import {buildDocument} from './buildIndex';

interface DocSource {
  title: string;
  permalink: string;
  source: string;
}

function docSources(content: unknown): DocSource[] {
  if (!content || typeof content !== 'object' || !('loadedVersions' in content) ||
      !Array.isArray(content.loadedVersions)) {
    throw new Error('Chat index requires the default Docusaurus docs plugin.');
  }
  return content.loadedVersions.flatMap((version: unknown) => {
    if (!version || typeof version !== 'object' || !('docs' in version) || !Array.isArray(version.docs)) {
      throw new Error('Chat index: invalid documentation version metadata.');
    }
    return version.docs.map((doc: unknown): DocSource => {
      if (!doc || typeof doc !== 'object' ||
          !('title' in doc) || typeof doc.title !== 'string' ||
          !('permalink' in doc) || typeof doc.permalink !== 'string' ||
          !('source' in doc) || typeof doc.source !== 'string') {
        throw new Error('Chat index: missing resolved documentation metadata.');
      }
      return {title: doc.title, permalink: doc.permalink, source: doc.source};
    }).filter((doc) => doc.source.endsWith('.md'));
  });
}

export default function chatIndexPlugin(context: LoadContext): Plugin {
  let indexPath: string | undefined;
  return {
    name: 'chat-index',
    async allContentLoaded({allContent, actions}) {
      const sources = docSources(allContent['docusaurus-plugin-content-docs']?.default);
      const documents = await Promise.all(sources.map(async (doc) => {
        const source = path.resolve(context.siteDir, aliasedSitePathToRelativePath(doc.source));
        return buildDocument(
          await readFile(source, 'utf8'), doc, context.baseUrl,
          context.siteConfig.markdown.anchors.maintainCase,
        );
      }));
      const index = parseChatIndex({version: 1, documents});
      indexPath = await actions.createData('chat-index.json', JSON.stringify(index));
      actions.setGlobalData({
        pages: documents.map(({title, route}) => ({title, route})),
      } satisfies ChatSiteData);
    },
    configureWebpack(_config, isServer) {
      if (isServer) return {};
      if (!indexPath) throw new Error('Chat index was not generated before bundling.');
      // CopyPlugin watches the generated data file, so dev rebuilds update the same public asset.
      return {plugins: [new CopyPlugin({patterns: [{from: indexPath, to: 'chat-index.json'}]})]};
    },
  };
}
