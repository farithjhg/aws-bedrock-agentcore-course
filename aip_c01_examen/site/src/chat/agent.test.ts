import {afterEach, describe, expect, it, vi} from 'vitest';
import {ChatError, composePrompt, GEMINI_ENDPOINT, MAX_HISTORY_TURNS, streamAnswer} from './agent';
import type {HistoryTurn} from './agent';

const fakeKey = 'test-key-not-a-real-credential';
const options = () => ({
  apiKey: fakeKey, history: [] as HistoryTurn[], prompt: 'Current page prompt',
  signal: new AbortController().signal,
});
const event = (text: string, finishReason?: string) => `data: ${JSON.stringify({
  candidates: [{content: {parts: [{text}]}, ...(finishReason ? {finishReason} : {})}],
})}`;

function response(text: string, chunkSize = 4096): Response {
  const bytes = new TextEncoder().encode(text);
  return new Response(new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += chunkSize) controller.enqueue(bytes.slice(i, i + chunkSize));
      controller.close();
    },
  }), {headers: {'Content-Type': 'text/event-stream'}});
}

async function collect(input = options()): Promise<string> {
  let answer = '';
  for await (const token of streamAnswer(input)) answer += token;
  return answer;
}

afterEach(() => vi.unstubAllGlobals());

describe('Gemini requests and prompt grounding', () => {
  it('keeps eight recent turns, configures the model, and sends the key only in its header', async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => response(`${event('Answer', 'STOP')}\n\n`));
    vi.stubGlobal('fetch', fetchMock);
    const history: HistoryTurn[] = Array.from({length: 12}, (_, i) => ({
      role: i % 2 ? 'model' : 'user', text: `turn-${i}`,
    }));
    await collect({...options(), history});
    const [url, request] = fetchMock.mock.calls[0];
    expect(url).toBe(GEMINI_ENDPOINT);
    expect(url).not.toContain(fakeKey);
    expect(request?.headers).toMatchObject({'x-goog-api-key': fakeKey});
    const body = JSON.parse(String(request?.body));
    expect(String(request?.body)).not.toContain(fakeKey);
    expect(body.contents).toHaveLength(MAX_HISTORY_TURNS + 1);
    expect(body.contents[0]).toEqual({role: 'user', parts: [{text: 'turn-4'}]});
    expect(body.generationConfig).toEqual({temperature: 0.3, maxOutputTokens: 2048});
    expect(body.systemInstruction.parts[0].text).toContain('CURRENT PAGE');
    expect(body.systemInstruction.parts[0].text).toContain('Northwind');
  });

  it('includes the map, primary page, distinct source headings and question', () => {
    const prompt = composePrompt({
      map: 'Security (/security#pii)', title: 'RAG', route: '/rag', primary: 'Page facts',
      related: [{docTitle: 'Security', route: '/security', heading: 'PII', headingId: 'pii', body: 'Mask PII'}],
    }, 'Which constraint matters?');
    for (const text of ['Page facts', 'Title: RAG', 'Route: /rag', 'Source: /security#pii', 'Which constraint matters?']) {
      expect(prompt).toContain(text);
    }
    expect(prompt.indexOf('CURRENT PAGE')).toBeLessThan(prompt.indexOf('RELATED EXCERPTS'));
  });
});

describe('SSE parsing', () => {
  it('handles one-byte chunks, split UTF-8, CRLF, comments, multiple events and final buffered data', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response(
      `: keepalive\r\n\r\n${event('Caf\u00e9 ')}\r\n\r\nid: 2\r\n${event('works', 'STOP')}`, 1,
    )));
    expect(await collect()).toBe('Caf\u00e9 works');
  });

  it('joins multiline data fields and handles a DONE marker without a final newline', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response(
      'event: message\ndata: {"candidates": [\ndata: {"content":{"parts":[{"text":"OK"}]}}\ndata: ]}\n\ndata: [DONE]', 7,
    )));
    expect(await collect()).toBe('OK');
  });

  it('ignores thought parts and accepts final usage-only metadata', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response(
      'data: {"candidates":[{"content":{"parts":[{"thought":true,"text":"hidden"},{"text":"Visible"}]},"finishReason":"STOP"}]}\n\n' +
      'data: {"usageMetadata":{"totalTokenCount":10}}\n\n',
    )));
    expect(await collect()).toBe('Visible');
  });

  it.each([
    ['data: {bad json}\n\n', 'response'],
    [`${event('Partial')}\n\n`, 'interrupted'],
    ['data: {"promptFeedback":{"blockReason":"SAFETY"}}\n\n', 'blocked'],
    ['data: {"candidates":[{"finishReason":"SAFETY"}]}\n\n', 'blocked'],
    [`${event('', 'STOP')}\n\n`, 'empty'],
    [`${event('Partial', 'MAX_TOKENS')}\n\n`, 'limit'],
    ['event: error\ndata: {"message":"not shown"}\n\n', 'service'],
    ['data: {"unknown":true}\n\n', 'response'],
  ])('reports malformed, blocked or incomplete streams (%s)', async (text, code) => {
    vi.stubGlobal('fetch', vi.fn(async () => response(text)));
    await expect(collect()).rejects.toMatchObject({name: 'ChatError', code});
  });

  it.each([[400, 'key'], [401, 'key'], [403, 'key'], [429, 'quota'], [404, 'model'], [503, 'service']])(
    'reports HTTP %s without exposing server error bodies', async (status, code) => {
      vi.stubGlobal('fetch', vi.fn(async () => new Response(`secret ${fakeKey}`, {status: Number(status)})));
      const error = await collect().catch((failure: unknown) => failure);
      expect(error).toBeInstanceOf(ChatError);
      expect(error).toMatchObject({code});
      expect(String(error)).not.toContain(fakeKey);
    },
  );

  it('handles error objects inside SSE without exposing their messages', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response(
      `data: {"error":{"code":429,"message":"${fakeKey}"}}\n\n`,
    )));
    await expect(collect()).rejects.toMatchObject({code: 'quota'});
  });

  it('sanitizes transport errors and missing readable bodies', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error(fakeKey); }));
    const error = await collect().catch((failure: unknown) => failure);
    expect(error).toMatchObject({code: 'network'});
    expect(String(error)).not.toContain(fakeKey);
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null)));
    await expect(collect()).rejects.toMatchObject({code: 'response'});
  });

  it('aborts before fetching and cancels a reader stalled between chunks', async () => {
    const alreadyAborted = new AbortController();
    alreadyAborted.abort();
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    await expect(collect({...options(), signal: alreadyAborted.signal})).rejects.toMatchObject({name: 'AbortError'});
    expect(fetchMock).not.toHaveBeenCalled();

    const cancelled = vi.fn();
    const stream = new ReadableStream<Uint8Array>({cancel: cancelled});
    fetchMock.mockResolvedValue(new Response(stream));
    const controller = new AbortController();
    const pending = collect({...options(), signal: controller.signal});
    await vi.waitFor(() => expect(stream.locked).toBe(true));
    controller.abort();
    await expect(pending).rejects.toMatchObject({name: 'AbortError'});
    expect(cancelled).toHaveBeenCalledOnce();
    expect(stream.locked).toBe(false);
  });

  it('cancels the reader when the consumer stops after the first token', async () => {
    const cancelled = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode(`${event('First')}\n\n`)); },
      cancel: cancelled,
    });
    vi.stubGlobal('fetch', vi.fn(async () => new Response(stream)));
    const answer = streamAnswer(options());
    expect((await answer.next()).value).toBe('First');
    await answer.return(undefined);
    expect(cancelled).toHaveBeenCalledOnce();
    expect(stream.locked).toBe(false);
  });
});
