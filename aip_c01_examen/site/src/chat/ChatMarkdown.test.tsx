import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {describe, expect, it} from 'vitest';
import ChatMarkdown, {safeChatHref} from './ChatMarkdown';

const base = '/aws-bedrock-agentcore-course/aip_c01_examen/';

describe('safe chat Markdown', () => {
  it('renders Markdown, never raw model HTML, scripts or remote images', () => {
    const html = renderToStaticMarkup(<ChatMarkdown baseUrl={base} currentRoute="/blueprint/topic" text={
      '**Plain explanation**\n\n<script>alert("unsafe")</script>\n\n' +
      '<img src="https://tracker.invalid/raw" onerror="alert(1)">\n\n' +
      '![Tracking](https://tracker.invalid/image)\n\n[Bad](javascript:alert%281%29)\n\n`<b>literal code</b>`'
    } />);
    expect(html).toContain('<strong>Plain explanation</strong>');
    expect(html).toContain('&lt;b&gt;literal code&lt;/b&gt;');
    for (const unsafe of ['<script', '<img', 'onerror', 'tracker.invalid', 'href="javascript:']) {
      expect(html).not.toContain(unsafe);
    }
  });

  it('rebases page and heading links once, including relative and current-page links', () => {
    expect(safeChatHref('/blueprint/other#rag', base, '/blueprint/topic')).toBe(`${base}blueprint/other#rag`);
    expect(safeChatHref(`${base}blueprint/other#rag`, base, '/blueprint/topic')).toBe(`${base}blueprint/other#rag`);
    expect(safeChatHref('#rag', base, '/blueprint/topic')).toBe(`${base}blueprint/topic#rag`);
    expect(safeChatHref('../recursos', base, '/blueprint/topic')).toBe(`${base}recursos`);
    expect(safeChatHref('/', base, '/blueprint/topic')).toBe(base);
  });

  it.each(['javascript:alert(1)', 'data:text/html,test', '//evil.invalid', '\\\\evil.invalid', '../../../../outside', '/%2e%2e/outside', 'https://user:password@example.com'])(
    'does not make unsafe or out-of-base links navigable: %s', (href) => {
      expect(safeChatHref(href, base, '/blueprint/topic')).toBeUndefined();
    },
  );

  it('uses safe external links and deployment-prefixed internal hrefs', () => {
    const html = renderToStaticMarkup(<ChatMarkdown baseUrl={base} currentRoute="/" text={
      '[Course](/blueprint/dominio-1-fundacion-datos#rag)\n\n[Google](https://aistudio.google.com/apikey)'
    } />);
    expect(html).toContain(`href="${base}blueprint/dominio-1-fundacion-datos#rag"`);
    expect(html).toContain('rel="noopener noreferrer"');
  });
});
