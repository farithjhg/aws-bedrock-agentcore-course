import {describe, expect, it} from 'vitest';
import {buildDocument, routeFromPermalink} from './buildIndex';

const baseUrl = '/aws-bedrock-agentcore-course/aip_c01_examen/';

describe('Docusaurus chat indexing', () => {
  it('uses resolved permalink/title metadata and Docusaurus heading IDs, not filenames', async () => {
    const markdown = `---
id: unrelated-file-id
slug: /custom-slug
title: Frontmatter title
private_note: not-indexed
---
# Visible title

Intro text.

## Repeat

First.

#### Repeat

Subsection still belongs to the first section.

### Repeat

Second.

## RAG & \`vectors\` {#explicit-id}

| Choice | Reason |
|---|---|
| RAG | Fresh facts |

\`\`\`markdown
## Not a heading
\`\`\`

<!-- Do not index this comment. -->
`;
    const document = await buildDocument(markdown, {
      title: 'Resolved title',
      permalink: `${baseUrl}docs/custom-slug`,
    }, baseUrl);
    expect(document.title).toBe('Resolved title');
    expect(document.route).toBe('/docs/custom-slug');
    expect(document.headings).toEqual([
      {title: 'Repeat', id: 'repeat'},
      {title: 'Repeat', id: 'repeat-2'},
      {title: 'RAG & vectors', id: 'explicit-id'},
    ]);
    expect(document.sections).toHaveLength(4);
    expect(document.sections[1].body).toContain('Subsection still belongs');
    expect(document.sections[3].body).toContain('RAG | Fresh facts');
    expect(document.sections[3].body).toContain('## Not a heading');
    const json = JSON.stringify(document);
    expect(json).not.toContain('private_note');
    expect(json).not.toContain('not-indexed');
    expect(json).not.toContain('Do not index this comment');
    expect(document.sections.every((section) =>
      section.route === '/docs/custom-slug' && section.docTitle === document.title)).toBe(true);
  });

  it('honors explicit comment anchors, case settings and the home slug', async () => {
    const document = await buildDocument('## Mixed Case\n\nText.\n\n## Custom <!-- #CaseSensitive -->\n\nOther.', {
      title: 'Home', permalink: baseUrl,
    }, baseUrl, true);
    expect(document.route).toBe('/');
    expect(document.headings.map(({id}) => id)).toEqual(['Mixed-Case', 'CaseSensitive']);
  });

  it('refuses to guess a route outside the configured deployment prefix', () => {
    expect(() => routeFromPermalink('/wrong-prefix/doc', baseUrl)).toThrow('outside baseUrl');
    expect(routeFromPermalink('/docs/custom/', '/')).toBe('/docs/custom');
  });

  it('uses the same directive parsing as rendered headings containing an AWS colon name', async () => {
    const document = await buildDocument('### Network isolation - IAM aws:SourceVpce\n\nPolicy.', {
      title: 'Security', permalink: `${baseUrl}security`,
    }, baseUrl);
    expect(document.headings[0].id).toBe('network-isolation---iam-aws');
  });
});
