// @vitest-environment jsdom
import React from 'react';
import {act, cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {ChatError, streamAnswer} from '../../chat/agent';
import type {ChatIndex} from '../../chat/retrieval';
import ChatWidget from './index';

const location = vi.hoisted(() => ({pathname: '/aws-bedrock-agentcore-course/aip_c01_examen/one'}));
vi.mock('@docusaurus/router', () => ({useLocation: () => location}));
vi.mock('@docusaurus/useBaseUrl', () => ({
  default: (route: string) => `/aws-bedrock-agentcore-course/aip_c01_examen/${route.replace(/^\//, '')}`,
}));
vi.mock('@docusaurus/useGlobalData', () => ({
  usePluginData: () => ({pages: [{title: 'Page One', route: '/one'}, {title: 'Page Two', route: '/two'}]}),
}));
vi.mock('../../chat/agent', async (original) => ({
  ...await original<typeof import('../../chat/agent')>(),
  streamAnswer: vi.fn(),
}));

const base = '/aws-bedrock-agentcore-course/aip_c01_examen/';
const storageKey = 'aip-c01.gemini-api-key';
const fakeKey = 'test-key-not-a-real-credential';
const index: ChatIndex = {
  version: 1,
  documents: ['One', 'Two'].map((name) => ({
    title: `Page ${name}`, route: `/${name.toLowerCase()}`, headings: [],
    sections: [{
      docTitle: `Page ${name}`, route: `/${name.toLowerCase()}`, heading: '', headingId: '',
      body: `Primary material for Page ${name}.`,
    }],
  })),
};

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  location.pathname = `${base}one`;
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callback(0); return 1; });
  vi.stubGlobal('cancelAnimationFrame', vi.fn());
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(index))));
  vi.mocked(streamAnswer).mockReset().mockImplementation(async function* () {
    yield 'A **mocked** answer.';
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function openWithKey() {
  window.localStorage.setItem(storageKey, fakeKey);
  const result = render(<ChatWidget />);
  fireEvent.click(screen.getByRole('button', {name: 'Ask this page'}));
  await waitFor(() => expect(screen.getByRole('button', {name: 'Explain this page'})).toHaveProperty('disabled', false));
  return result;
}

function submit(question = 'Explain the decision') {
  fireEvent.change(screen.getByRole('textbox', {name: 'Question about this page'}), {target: {value: question}});
  fireEvent.click(screen.getByRole('button', {name: 'Send'}));
}

describe('visitor key and privacy controls', () => {
  it('discloses the transfer, saves only the visitor key, and forgets it without a model request', async () => {
    render(<ChatWidget />);
    fireEvent.click(screen.getByRole('button', {name: 'Ask this page'}));
    expect(screen.getByText(/Sending shares this page's text/).textContent).toContain('with Google');
    expect(screen.getByRole('link', {name: /Get a Gemini API key/}).getAttribute('href')).toBe('https://aistudio.google.com/apikey');
    fireEvent.change(screen.getByLabelText('Gemini API key'), {target: {value: ` ${fakeKey} `}});
    fireEvent.click(screen.getByRole('button', {name: 'Save key'}));
    await screen.findByRole('button', {name: 'Forget key'});
    expect(window.localStorage.getItem(storageKey)).toBe(fakeKey);
    expect(window.localStorage.length).toBe(1);
    expect(window.sessionStorage.length).toBe(0);
    expect(document.body.innerHTML).not.toContain(fakeKey);
    expect(streamAnswer).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', {name: 'Forget key'}));
    expect(window.localStorage.getItem(storageKey)).toBeNull();
    expect(screen.getByLabelText('Gemini API key')).toHaveProperty('value', '');
  });

  it('surfaces localStorage failures instead of pretending the key was saved or forgotten', async () => {
    await openWithKey();
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new DOMException('Denied'); });
    fireEvent.click(screen.getByRole('button', {name: 'Forget key'}));
    expect(screen.getByRole('alert').textContent).toContain('could not be removed');
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new DOMException('Denied'); });
    fireEvent.change(screen.getByLabelText('Gemini API key'), {target: {value: fakeKey}});
    fireEvent.click(screen.getByRole('button', {name: 'Save key'}));
    expect(screen.getByRole('alert').textContent).toContain('could not be saved');
    expect(streamAnswer).not.toHaveBeenCalled();
  });

  it('fetches the index under the real baseUrl and exposes a retry on failure', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error('Offline'));
    window.localStorage.setItem(storageKey, fakeKey);
    render(<ChatWidget />);
    expect(fetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', {name: 'Ask this page'}));
    expect((await screen.findByRole('alert')).textContent).toContain('Could not load the course context');
    expect(fetch).toHaveBeenCalledWith(`${base}chat-index.json`, expect.objectContaining({signal: expect.any(AbortSignal)}));
    expect(screen.getByRole('button', {name: 'Explain this page'})).toHaveProperty('disabled', true);
    fireEvent.click(screen.getByRole('button', {name: 'Retry context'}));
    await waitFor(() => expect(screen.getByRole('button', {name: 'Explain this page'})).toHaveProperty('disabled', false));
  });
});

describe('page-scoped conversations', () => {
  it('uses the current page, sends Enter but not Shift+Enter, and clears follow-up history', async () => {
    await openWithKey();
    const input = screen.getByRole('textbox', {name: 'Question about this page'});
    fireEvent.change(input, {target: {value: 'First question\nSecond line'}});
    fireEvent.keyDown(input, {key: 'Enter', shiftKey: true});
    expect(streamAnswer).not.toHaveBeenCalled();
    fireEvent.keyDown(input, {key: 'Enter'});
    await screen.findByText(/Answer complete/);
    expect(vi.mocked(streamAnswer).mock.calls[0][0].prompt).toContain('Primary material for Page One.');
    expect(vi.mocked(streamAnswer).mock.calls[0][0].prompt).toContain('First question\nSecond line');
    submit('Follow up');
    await waitFor(() => expect(streamAnswer).toHaveBeenCalledTimes(2));
    await screen.findByText(/Answer complete/);
    expect(vi.mocked(streamAnswer).mock.calls[1][0].history).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', {name: 'Clear'}));
    expect(screen.queryByText('Follow up')).toBeNull();
    submit('Fresh question');
    await waitFor(() => expect(streamAnswer).toHaveBeenCalledTimes(3));
    expect(vi.mocked(streamAnswer).mock.calls[2][0].history).toEqual([]);
    expect(window.localStorage.length).toBe(1);
  });

  it('aborts on navigation, keeps the panel open, resets history and ignores stale tokens', async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => { release = resolve; });
    vi.mocked(streamAnswer).mockImplementationOnce(async function* () {
      yield 'First page partial';
      await gate;
      yield 'Stale old-page answer';
    });
    const {rerender} = await openWithKey();
    submit();
    await screen.findByText('First page partial');
    const signal = vi.mocked(streamAnswer).mock.calls[0][0].signal;
    location.pathname = `${base}two`;
    rerender(<ChatWidget />);
    expect(signal.aborted).toBe(true);
    expect(screen.getByRole('dialog')).not.toHaveProperty('hidden', true);
    expect(screen.getByText('Page Two')).toBeTruthy();
    expect(screen.queryByText('First page partial')).toBeNull();
    await act(async () => release());
    expect(screen.queryByText('Stale old-page answer')).toBeNull();
    submit('Explain the second page');
    await waitFor(() => expect(streamAnswer).toHaveBeenCalledTimes(2));
    const second = vi.mocked(streamAnswer).mock.calls[1][0];
    expect(second.history).toEqual([]);
    expect(second.prompt.split('CURRENT PAGE')[1].split('RELATED EXCERPTS')[0]).toContain('Primary material for Page Two.');
    expect(second.prompt.split('CURRENT PAGE')[1].split('RELATED EXCERPTS')[0]).not.toContain('Primary material for Page One.');
  });

  it.each(['Clear', 'Forget key', 'unmount'])('aborts and ignores pending tokens after %s', async (action) => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => { release = resolve; });
    vi.mocked(streamAnswer).mockImplementationOnce(async function* () {
      yield 'Partial';
      await gate;
      yield 'Stale';
    });
    const result = await openWithKey();
    submit();
    await screen.findByText('Partial');
    const signal = vi.mocked(streamAnswer).mock.calls[0][0].signal;
    if (action === 'unmount') result.unmount();
    else fireEvent.click(screen.getByRole('button', {name: action}));
    expect(signal.aborted).toBe(true);
    await act(async () => release());
    expect(screen.queryByText('Stale')).toBeNull();
  });

  it('stops partial answers without adding them to history', async () => {
    vi.mocked(streamAnswer).mockImplementationOnce(async function* ({signal}) {
      yield 'Incomplete text';
      await new Promise<void>((_resolve, reject) => {
        signal.addEventListener('abort', () => reject(new DOMException('Stopped', 'AbortError')), {once: true});
      });
    });
    await openWithKey();
    submit();
    await screen.findByText('Incomplete text');
    fireEvent.click(screen.getByRole('button', {name: 'Stop'}));
    await screen.findByText('Stopped (incomplete)');
    submit('Try another question');
    await waitFor(() => expect(streamAnswer).toHaveBeenCalledTimes(2));
    expect(vi.mocked(streamAnswer).mock.calls[1][0].history).toEqual([]);
  });

  it('shows actionable quota errors and closes on Escape with focus restored', async () => {
    vi.mocked(streamAnswer).mockImplementationOnce(async function* () {
      throw new ChatError('quota', 'Gemini quota reached. Wait and retry.');
    });
    await openWithKey();
    submit();
    expect((await screen.findByRole('alert')).textContent).toContain('quota reached');
    fireEvent.keyDown(document, {key: 'Escape'});
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole('button', {name: 'Ask this page'}));
  });

  it('does not render a chatbot on non-documentation routes', () => {
    location.pathname = `${base}not-a-document`;
    render(<ChatWidget />);
    expect(screen.queryByRole('button', {name: 'Ask this page'})).toBeNull();
  });
});
