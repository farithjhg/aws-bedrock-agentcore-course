export interface ChatPage {
  title: string;
  route: string;
}

export interface ChatSection {
  docTitle: string;
  route: string;
  heading: string;
  headingId: string;
  body: string;
}

export interface ChatDocument extends ChatPage {
  headings: {title: string; id: string}[];
  sections: ChatSection[];
}

export interface ChatIndex {
  version: 1;
  documents: ChatDocument[];
}

export interface ChatSiteData {
  pages: ChatPage[];
}

export interface GroundingContext {
  map: string;
  title: string;
  route: string;
  primary: string;
  related: ChatSection[];
}

export const MAX_PRIMARY_CHARS = 60_000;
export const RELATED_CHAR_BUDGET = 6_000;
export const MAX_RELATED_SECTIONS = 3;
const MAX_EXCERPT_CHARS = 2_400;

export function normalizeRoute(route: string): string {
  return route.split(/[?#]/, 1)[0].replace(/\/+$/, '') || '/';
}

export function pageRoute(pathname: string, baseUrl: string): string | undefined {
  const path = normalizeRoute(pathname);
  const base = normalizeRoute(baseUrl);
  if (base === '/') return path;
  if (path === base) return '/';
  return path.startsWith(`${base}/`) ? path.slice(base.length) : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function parseChatIndex(value: unknown): ChatIndex {
  const invalid = () => new Error('The course context index is invalid. Reload the page or retry.');
  if (!isRecord(value) || value.version !== 1 || !Array.isArray(value.documents)) {
    throw invalid();
  }
  const routes = new Set<string>();
  const documents = value.documents.map((doc: unknown): ChatDocument => {
    if (
      !isRecord(doc) || typeof doc.title !== 'string' ||
      typeof doc.route !== 'string' || !doc.route.startsWith('/') ||
      doc.route.startsWith('//') || /[?#\\]/.test(doc.route) ||
      !Array.isArray(doc.headings) || !Array.isArray(doc.sections)
    ) {
      throw invalid();
    }
    const title = doc.title;
    const route = doc.route;
    if (routes.has(normalizeRoute(route))) throw invalid();
    routes.add(normalizeRoute(route));
    const headings = doc.headings.map((heading: unknown) => {
      if (!isRecord(heading) || typeof heading.title !== 'string' ||
          typeof heading.id !== 'string' || !heading.id) throw invalid();
      return {title: heading.title, id: heading.id};
    });
    const sections = doc.sections.map((section: unknown): ChatSection => {
      if (
        !isRecord(section) || section.docTitle !== title || section.route !== route ||
        typeof section.heading !== 'string' || typeof section.headingId !== 'string' ||
        typeof section.body !== 'string' ||
        (section.headingId !== '' && !headings.some(({id}) => id === section.headingId))
      ) {
        throw invalid();
      }
      return {
        docTitle: title, route, heading: section.heading,
        headingId: section.headingId, body: section.body,
      };
    });
    return {title, route, headings, sections};
  });
  if (!documents.length) throw invalid();
  return {version: 1, documents};
}

export function sectionLink(section: ChatSection): string {
  return `${section.route}${section.headingId ? `#${section.headingId}` : ''}`;
}

export function formatSection(section: ChatSection): string {
  return `${section.docTitle} > ${section.heading}\nSource: ${sectionLink(section)}\n${section.body}`;
}

const stopWords = new Set(
  ('a an and are as at be by can do for from how i in is it me my of on or that the this to what when which why with you your ' +
  'de del el en es la las lo los para por que un una y').split(' '),
);

function tokenize(text: string): string[] {
  return (text.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [])
    .filter((word) => word.length > 1 && !stopWords.has(word));
}

export function retrieveRelated(
  index: ChatIndex,
  currentRoute: string,
  question: string,
  {topK = MAX_RELATED_SECTIONS, budget = RELATED_CHAR_BUDGET}: {topK?: number; budget?: number} = {},
): ChatSection[] {
  const terms = [...new Set(tokenize(question))];
  if (!terms.length || topK <= 0 || budget <= 0) return [];
  const candidates = index.documents
    .filter((doc) => normalizeRoute(doc.route) !== normalizeRoute(currentRoute))
    .flatMap((doc) => doc.sections)
    .filter((section) => section.body.trim())
    .map((section) => {
      const tokens = tokenize(`${section.docTitle} ${section.heading} ${section.heading} ${section.body}`);
      const frequencies = new Map<string, number>();
      for (const token of tokens) frequencies.set(token, (frequencies.get(token) ?? 0) + 1);
      return {section, frequencies, length: tokens.length};
    });
  const averageLength = candidates.reduce((sum, item) => sum + item.length, 0) / (candidates.length || 1);
  const documentFrequency = new Map(terms.map((term) => [
    term, candidates.filter(({frequencies}) => frequencies.has(term)).length,
  ]));
  const ranked = candidates.map((candidate) => {
    const score = terms.reduce((sum, term) => {
      const frequency = candidate.frequencies.get(term) ?? 0;
      const df = documentFrequency.get(term) ?? 0;
      const idf = Math.log(1 + (candidates.length - df + 0.5) / (df + 0.5));
      const denominator = frequency + 1.2 * (0.25 + 0.75 * candidate.length / (averageLength || 1));
      return sum + idf * frequency * 2.2 / denominator;
    }, 0);
    return {...candidate, score};
  }).filter(({score}) => score > 0).sort((a, b) => b.score - a.score);

  const related: ChatSection[] = [];
  let remaining = budget;
  for (const {section} of ranked) {
    if (related.length >= topK) break;
    const separatorLength = related.length ? 2 : 0;
    const headerLength = formatSection({...section, body: ''}).length;
    const bodyBudget = Math.min(MAX_EXCERPT_CHARS, remaining - separatorLength - headerLength);
    if (bodyBudget < 80) continue;
    const excerpt = {...section, body: section.body.slice(0, bodyBudget)};
    remaining -= formatSection(excerpt).length + separatorLength;
    related.push(excerpt);
  }
  return related;
}

export function buildGroundingContext(
  index: ChatIndex,
  route: string,
  question: string,
): GroundingContext {
  const current = index.documents.find((doc) => normalizeRoute(doc.route) === normalizeRoute(route));
  if (!current) throw new Error('No course context was found for this page. Reload before asking again.');
  const text = current.sections.map((section) => section.body).join('\n\n');
  const omitted = '\n[Remaining page text omitted to fit the context budget.]';
  const primary = text.length > MAX_PRIMARY_CHARS
    ? text.slice(0, MAX_PRIMARY_CHARS - omitted.length) + omitted
    : text;
  return {
    title: current.title,
    route: current.route,
    primary,
    map: index.documents.map((doc) => [
      `${doc.title} (${doc.route})`,
      ...doc.headings.map((heading) => `  ${heading.title} (${doc.route}#${heading.id})`),
    ].join('\n')).join('\n\n'),
    related: retrieveRelated(index, current.route, question),
  };
}
