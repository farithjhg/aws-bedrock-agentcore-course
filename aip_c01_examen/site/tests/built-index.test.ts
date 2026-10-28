import {readFileSync, readdirSync} from 'node:fs';
import path from 'node:path';
import {describe, expect, it} from 'vitest';
import {parseChatIndex} from '../src/chat/retrieval';

const baseUrl = '/aws-bedrock-agentcore-course/aip_c01_examen/';
const build = path.resolve('build');
const index = parseChatIndex(JSON.parse(readFileSync(path.join(build, 'chat-index.json'), 'utf8')));

function decodeAttribute(value: string): string {
  return value.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'");
}

describe('production index and SSR output', () => {
  it('indexes every course Markdown document, with a matching built route and every actual h2/h3 ID', () => {
    const docs = readdirSync('docs', {recursive: true}).filter((file) => String(file).endsWith('.md'));
    expect(index.documents).toHaveLength(docs.length);
    for (const doc of index.documents) {
      const file = doc.route === '/' ? 'index.html' : `${doc.route.slice(1)}.html`;
      const html = readFileSync(path.join(build, ...file.split('/')), 'utf8');
      const actualIds = [...html.matchAll(/<h[23]\b[^>]*\bid="([^"]+)"/g)].map((match) => decodeAttribute(match[1]));
      expect(doc.headings.map(({id}) => id), doc.route).toEqual(actualIds);
      expect(html).toContain(`${baseUrl}assets/`);
      expect(html).not.toContain('id="page-chat-panel"');
      expect(doc.sections.every((section) => section.docTitle === doc.title && section.route === doc.route)).toBe(true);
    }
  });

  it('ships only public index fields and never the synthetic test credential or machine paths', () => {
    for (const doc of index.documents) {
      expect(Object.keys(doc).sort()).toEqual(['headings', 'route', 'sections', 'title']);
    }
    const json = readFileSync(path.join(build, 'chat-index.json'), 'utf8');
    expect(json).not.toContain('@site/');
    expect(json).not.toContain(process.cwd());
    for (const file of readdirSync(build, {recursive: true})) {
      if (/\.(js|json|html)$/.test(String(file))) {
        expect(readFileSync(path.join(build, String(file)), 'utf8'), String(file))
          .not.toContain('test-key-not-a-real-credential');
      }
    }
  });
});
