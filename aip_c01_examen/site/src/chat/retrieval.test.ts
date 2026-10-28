import {describe, expect, it} from 'vitest';
import {
  buildGroundingContext, formatSection, MAX_PRIMARY_CHARS, pageRoute, parseChatIndex,
  RELATED_CHAR_BUDGET, retrieveRelated,
} from './retrieval';
import type {ChatDocument, ChatIndex} from './retrieval';

function doc(route: string, title: string, bodies: string[]): ChatDocument {
  return {
    route, title,
    headings: bodies.map((_body, i) => ({title: `Section ${i}`, id: `section-${i}`})),
    sections: bodies.map((body, i) => ({route, docTitle: title, heading: `Section ${i}`, headingId: `section-${i}`, body})),
  };
}

const index: ChatIndex = {
  version: 1,
  documents: [
    doc('/current', 'Current page', ['Only the current page is primary. RAG Northwind.']),
    doc('/retrieval', 'RAG and vectors', ['RAG retrieves current Northwind policies. '.repeat(200), 'Chunking RAG documents. '.repeat(200)]),
    doc('/security', 'Guardrails', ['Northwind Guardrails block PII. '.repeat(200)]),
    doc('/cost', 'Inference costs', ['Batch processing reduces inference cost.']),
  ],
};

describe('page-first grounding', () => {
  it('uses the exact matching page and keeps source routes intact', () => {
    const context = buildGroundingContext(index, '/current/', 'RAG policies');
    expect(context.title).toBe('Current page');
    expect(context.primary).toBe(index.documents[0].sections[0].body);
    expect(context.map).toContain('RAG and vectors (/retrieval)');
    expect(context.map).toContain('/security#section-0');
    expect(context.related[0].route).toBe('/retrieval');
    expect(context.related.every((section) => section.route !== '/current')).toBe(true);
    expect(context.related.every((section) => index.documents.some((item) =>
      item.route === section.route && item.title === section.docTitle))).toBe(true);
  });

  it('enforces top-k and the complete formatted excerpt character budget', () => {
    const related = retrieveRelated(index, '/current', 'Northwind RAG Guardrails');
    expect(related).toHaveLength(3);
    expect(related.map(formatSection).join('\n\n').length).toBeLessThanOrEqual(RELATED_CHAR_BUDGET);
    expect(related.every((section) => section.body.length <= 2400)).toBe(true);
    const smaller = retrieveRelated(index, '/current', 'RAG', {budget: 500, topK: 1});
    expect(smaller).toHaveLength(1);
    expect(smaller.map(formatSection).join('\n\n').length).toBeLessThanOrEqual(500);
    expect(retrieveRelated(index, '/current', 'RAG', {budget: 10})).toEqual([]);
  });

  it('does not retrieve unrelated sections or the current page', () => {
    expect(retrieveRelated(index, '/retrieval/', 'RAG chunking').some((section) => section.route === '/retrieval')).toBe(false);
    expect(retrieveRelated(index, '/current', 'unknownword')).toEqual([]);
    expect(retrieveRelated(index, '/current', 'the this and de la')).toEqual([]);
  });

  it('caps oversized primary context with an explicit omission marker', () => {
    const large: ChatIndex = {version: 1, documents: [doc('/', 'Long page', ['x'.repeat(80_000)])]};
    const context = buildGroundingContext(large, '/', 'Explain');
    expect(context.primary).toHaveLength(MAX_PRIMARY_CHARS);
    expect(context.primary).toContain('Remaining page text omitted');
  });

  it('fails explicitly instead of substituting context from another page', () => {
    expect(() => buildGroundingContext(index, '/missing', 'RAG')).toThrow('No course context');
  });
});

describe('index and route validation', () => {
  it('handles the Pages baseUrl, root route, route prefix and trailing slashes', () => {
    const base = '/aws-bedrock-agentcore-course/aip_c01_examen/';
    expect(pageRoute(base, base)).toBe('/');
    expect(pageRoute(`${base}blueprint/topic/?q=1#heading`, base)).toBe('/blueprint/topic');
    expect(pageRoute('/topic/', '/')).toBe('/topic');
    expect(pageRoute('/aws-bedrock-agentcore-course/aip_c01_examen-other/topic', base)).toBeUndefined();
  });

  it('rejects mismatched section routes, missing anchors and duplicate documents', () => {
    expect(parseChatIndex(index)).toEqual(index);
    const mismatched = structuredClone(index);
    mismatched.documents[0].sections[0].route = '/security';
    expect(() => parseChatIndex(mismatched)).toThrow('invalid');
    const missingHeading = structuredClone(index);
    missingHeading.documents[0].sections[0].headingId = 'missing';
    expect(() => parseChatIndex(missingHeading)).toThrow('invalid');
    expect(() => parseChatIndex({version: 1, documents: [index.documents[0], index.documents[0]]})).toThrow('invalid');
    expect(() => parseChatIndex({version: 2, documents: []})).toThrow('invalid');
  });
});
