import {DEFAULT_PARSE_FRONT_MATTER} from '@docusaurus/utils';
import docusaurusHeadings from '@docusaurus/mdx-loader/lib/remark/headings/index.js';
import type {Nodes, Root} from 'mdast';
import type {ChatDocument, ChatSection} from '../../src/chat/retrieval';
import {pageRoute} from '../../src/chat/retrieval';

function textContent(node: Nodes): string {
  if (node.type === 'html' || node.type === 'definition') return '';
  if ('value' in node) return node.value;
  if (!('children' in node)) return '';
  const inline = ['paragraph', 'heading', 'strong', 'emphasis', 'delete', 'link'];
  const separator = node.type === 'tableRow' ? ' | ' : inline.includes(node.type) ? '' : '\n';
  return node.children.map(textContent).join(separator);
}

export function routeFromPermalink(permalink: string, baseUrl: string): string {
  const route = pageRoute(permalink, baseUrl);
  if (route === undefined) {
    throw new Error(`Chat index: documentation permalink is outside baseUrl: ${permalink}`);
  }
  return route;
}

export async function buildDocument(
  markdown: string,
  metadata: {title: string; permalink: string},
  baseUrl: string,
  maintainCase = false,
): Promise<ChatDocument> {
  const [{unified}, {default: remarkParse}, {default: remarkGfm}, {default: remarkDirective}] = await Promise.all([
    import('unified'), import('remark-parse'), import('remark-gfm'), import('remark-directive'),
  ]);
  const {content} = await DEFAULT_PARSE_FRONT_MATTER({filePath: metadata.permalink, fileContent: markdown});
  // Use the installed Docusaurus heading transform, including explicit IDs and duplicate suffixes.
  const processor = unified().use(remarkParse).use(remarkGfm).use(remarkDirective)
    .use(docusaurusHeadings, {anchorsMaintainCase: maintainCase});
  const tree: Root = await processor.run(processor.parse(content));
  const route = routeFromPermalink(metadata.permalink, baseUrl);
  const document: ChatDocument = {title: metadata.title, route, headings: [], sections: []};
  let section: ChatSection = {
    docTitle: metadata.title, route, heading: metadata.title, headingId: '', body: '',
  };
  for (const node of tree.children) {
    if (node.type === 'heading' && (node.depth === 2 || node.depth === 3)) {
      if (section.body.trim()) document.sections.push({...section, body: section.body.trim()});
      const id = node.data?.hProperties?.id;
      if (typeof id !== 'string') throw new Error(`Chat index: missing heading ID in ${route}`);
      const heading = textContent(node);
      document.headings.push({title: heading, id});
      section = {docTitle: metadata.title, route, heading, headingId: id, body: ''};
    }
    const text = textContent(node).trim();
    if (text) section.body += `${text}\n\n`;
  }
  if (section.body.trim()) document.sections.push({...section, body: section.body.trim()});
  return document;
}
