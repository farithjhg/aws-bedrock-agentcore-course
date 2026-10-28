import React from 'react';
import ReactMarkdown from 'react-markdown';

export function safeChatHref(url: string, baseUrl: string, currentRoute: string): string | undefined {
  const href = url.trim();
  if (!href || /[\u0000-\u0020\\]/.test(href) || href.startsWith('//')) return undefined;
  try {
    if (/^https?:\/\//i.test(href)) {
      const external = new URL(href);
      return external.username || external.password ? undefined : external.href;
    }
    if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return undefined;
    const origin = 'https://course.invalid';
    const base = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
    const current = `${base}${currentRoute.replace(/^\//, '')}`;
    const target = href.startsWith('/')
      ? href.startsWith(base) || href === base.slice(0, -1) ? href : `${base}${href.slice(1)}`
      : href;
    const resolved = new URL(target, `${origin}${current}`);
    if (resolved.origin !== origin ||
        (!resolved.pathname.startsWith(base) && resolved.pathname !== base.slice(0, -1))) {
      return undefined;
    }
    return `${resolved.pathname}${resolved.search}${resolved.hash}`;
  } catch {
    // Invalid model-generated URLs remain plain text, never navigable links.
    return undefined;
  }
}

export default function ChatMarkdown({
  text, baseUrl, currentRoute,
}: {
  text: string;
  baseUrl: string;
  currentRoute: string;
}) {
  return (
    <ReactMarkdown
      skipHtml
      allowedElements={[
        'p', 'a', 'strong', 'em', 'del', 'code', 'pre', 'blockquote',
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'hr', 'br',
      ]}
      urlTransform={(url) => safeChatHref(url, baseUrl, currentRoute)}
      components={{
        a: ({href, children}) => href ? (
          <a
            href={href}
            target={/^https?:/.test(href) ? '_blank' : undefined}
            rel={/^https?:/.test(href) ? 'noopener noreferrer' : undefined}>
            {children}
          </a>
        ) : <span>{children}</span>,
      }}>
      {text}
    </ReactMarkdown>
  );
}
