import React, {useEffect, useRef, useState} from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {useLocation} from '@docusaurus/router';
import {usePluginData} from '@docusaurus/useGlobalData';
import {ChatError, composePrompt, MAX_HISTORY_TURNS, streamAnswer} from '../../chat/agent';
import type {HistoryTurn} from '../../chat/agent';
import {buildGroundingContext, normalizeRoute, pageRoute, parseChatIndex} from '../../chat/retrieval';
import type {ChatIndex, ChatPage, ChatSiteData} from '../../chat/retrieval';
import ChatMarkdown from '../../chat/ChatMarkdown';
import styles from './styles.module.css';

const KEY_STORAGE = 'aip-c01.gemini-api-key';
const suggestions = [
  {
    label: 'Explain this page',
    question: 'Explain the key concepts on this page in plain language, then show the exam discriminators and decisive constraint keywords.',
  },
  {
    label: 'Northwind example',
    question: 'Give me a concrete Northwind Support Assistant example grounded in this page, including the constraint that decides the AWS choice.',
  },
  {
    label: 'Quiz me',
    question: 'Quiz me on this page with one original scenario question. Wait for my answer before explaining the discriminator.',
  },
];

interface Message extends HistoryTurn {
  id: number;
  state: 'complete' | 'streaming' | 'stopped' | 'failed';
}

function PageChat({
  page, index, apiKey, baseUrl, open,
}: {
  page: ChatPage;
  index: ChatIndex | undefined;
  apiKey: string;
  baseUrl: string;
  open: boolean;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const active = useRef<AbortController | null>(null);
  const history = useRef<HistoryTurn[]>([]);
  const nextId = useRef(0);
  const log = useRef<HTMLDivElement>(null);

  useEffect(() => () => {
    active.current?.abort();
    active.current = null;
  }, []);

  useEffect(() => {
    if (!open) active.current?.abort();
  }, [open]);

  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages]);

  function clear() {
    active.current?.abort();
    active.current = null;
    history.current = [];
    setMessages([]);
    setQuestion('');
    setBusy(false);
    setError('');
    setStatus('Conversation cleared.');
  }

  async function send(text: string) {
    if (active.current) return;
    const trimmed = text.trim();
    if (!trimmed) {
      setError('Enter a question about this page.');
      return;
    }
    if (!index || !apiKey) {
      setError('Save a key and wait for the course context to load before sending.');
      return;
    }
    const controller = new AbortController();
    active.current = controller;
    const userId = nextId.current++;
    const modelId = nextId.current++;
    setMessages((previous) => [
      ...previous.slice(-(MAX_HISTORY_TURNS - 2)),
      {id: userId, role: 'user', text: trimmed, state: 'complete'},
      {id: modelId, role: 'model', text: '', state: 'streaming'},
    ]);
    setQuestion('');
    setError('');
    setStatus('Gemini is answering.');
    setBusy(true);
    let answer = '';
    const updateAnswer = (state: Message['state']) => {
      setMessages((previous) => previous.map((message) =>
        message.id === modelId ? {...message, text: answer, state} : message));
    };
    try {
      const context = buildGroundingContext(index, page.route, trimmed);
      for await (const token of streamAnswer({
        apiKey, history: history.current, prompt: composePrompt(context, trimmed), signal: controller.signal,
      })) {
        if (active.current !== controller || controller.signal.aborted) return;
        answer += token;
        updateAnswer('streaming');
      }
      if (active.current !== controller || controller.signal.aborted) return;
      const completed: HistoryTurn[] = [
        ...history.current, {role: 'user', text: trimmed}, {role: 'model', text: answer},
      ];
      history.current = completed.slice(-MAX_HISTORY_TURNS);
      updateAnswer('complete');
      setStatus('Answer complete. Verify important details in the course.');
    } catch (failure) {
      if (active.current !== controller) return;
      if (controller.signal.aborted) {
        updateAnswer('stopped');
        setStatus('Answer stopped. Incomplete answers are not used in follow-ups.');
      } else {
        updateAnswer('failed');
        setError(failure instanceof ChatError
          ? failure.message
          : 'Could not prepare the context for this page. Reload the page and retry.');
        setStatus('Answer failed.');
      }
    } finally {
      if (active.current === controller) {
        active.current = null;
        setBusy(false);
      }
    }
  }

  return (
    <div className={styles.session}>
      <div ref={log} className={styles.messages} role="log" aria-label="Page conversation" aria-live="polite" aria-busy={busy}>
        {!messages.length && (
          <div className={styles.empty}>
            <p>Start with this page. Ask for a plain-language explanation, an exam discriminator, or a worked example.</p>
            <div className={styles.suggestions}>
              {suggestions.map((suggestion) => (
                <button key={suggestion.label} type="button" disabled={!index}
                  onClick={() => void send(suggestion.question)}>
                  {suggestion.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((message) => (
          <div key={message.id} className={message.role === 'user' ? styles.userMessage : styles.modelMessage}>
            <strong className={styles.speaker}>{message.role === 'user' ? 'You' : 'Gemini'}</strong>
            {message.role === 'model'
              ? <ChatMarkdown text={message.text} baseUrl={baseUrl} currentRoute={page.route} />
              : <p className={styles.question}>{message.text}</p>}
            {message.state !== 'complete' && (
              <span className={styles.messageState}>
                {message.state === 'streaming' ? 'Answering...' : message.state === 'stopped' ? 'Stopped (incomplete)' : 'Incomplete answer'}
              </span>
            )}
          </div>
        ))}
      </div>
      {error && <p className={styles.error} role="alert">{error}</p>}
      <p className={styles.status} role="status">{status || 'AI answers can be wrong. Check the cited course material.'}</p>
      <form className={styles.composer} onSubmit={(event) => {
        event.preventDefault();
        void send(question);
      }}>
        <label htmlFor="page-chat-question" className={styles.srOnly}>Question about this page</label>
        <textarea
          id="page-chat-question"
          data-chat-autofocus
          rows={2}
          maxLength={2000}
          required
          value={question}
          placeholder="Ask about this page..."
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              if (!busy && index) event.currentTarget.form?.requestSubmit();
            }
          }}
        />
        <div className={styles.actions}>
          <span className={styles.hint}>Enter sends; Shift+Enter adds a line.</span>
          <button type="button" onClick={clear} disabled={!messages.length && !question}>Clear</button>
          {busy
            ? <button type="button" onClick={() => active.current?.abort()}>Stop</button>
            : <button className={styles.primary} type="submit" disabled={!index || !question.trim()}>Send</button>}
        </div>
      </form>
    </div>
  );
}

export default function ChatWidget() {
  const {pathname} = useLocation();
  const baseUrl = useBaseUrl('/');
  const indexUrl = useBaseUrl('/chat-index.json');
  const {pages} = usePluginData('chat-index') as ChatSiteData;
  const route = pageRoute(pathname, baseUrl);
  const page = pages.find((candidate) => normalizeRoute(candidate.route) === route);
  const [open, setOpen] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [draftKey, setDraftKey] = useState('');
  const [keyError, setKeyError] = useState('');
  const [sessionVersion, setSessionVersion] = useState(0);
  const [index, setIndex] = useState<ChatIndex>();
  const [indexError, setIndexError] = useState('');
  const [retry, setRetry] = useState(0);
  const launcher = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLElement>(null);

  useEffect(() => {
    try {
      setApiKey(window.localStorage.getItem(KEY_STORAGE) ?? '');
    } catch {
      setKeyError('Browser storage is unavailable. Allow local storage for this site to save a key.');
    }
  }, []);

  useEffect(() => {
    if (!open || index || !page) return undefined;
    const controller = new AbortController();
    setIndexError('');
    async function load() {
      try {
        const response = await fetch(indexUrl, {signal: controller.signal});
        if (!response.ok) throw new Error('Index request failed');
        const loaded = parseChatIndex(await response.json());
        if (!controller.signal.aborted) setIndex(loaded);
      } catch {
        if (!controller.signal.aborted) {
          setIndexError('Could not load the course context. Check your connection and retry.');
        }
      }
    }
    void load();
    return () => controller.abort();
  }, [open, index, indexUrl, retry, page?.route]);

  useEffect(() => {
    if (!open || !page) return undefined;
    const frame = requestAnimationFrame(() => {
      panel.current?.querySelector<HTMLElement>('[data-chat-autofocus]')?.focus();
    });
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !event.defaultPrevented) {
        event.preventDefault();
        setOpen(false);
        launcher.current?.focus();
      }
    };
    document.addEventListener('keydown', escape);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener('keydown', escape);
    };
  }, [open, page?.route, apiKey]);

  function saveKey(event: React.FormEvent) {
    event.preventDefault();
    const key = draftKey.trim();
    if (!key) {
      setKeyError('Enter your own Gemini API key.');
      return;
    }
    try {
      window.localStorage.setItem(KEY_STORAGE, key);
      setApiKey(key);
      setDraftKey('');
      setKeyError('');
      setSessionVersion((value) => value + 1);
    } catch {
      setKeyError('The key could not be saved. Allow local storage for this site and try again.');
    }
  }

  function forgetKey() {
    setApiKey('');
    setDraftKey('');
    setSessionVersion((value) => value + 1);
    try {
      window.localStorage.removeItem(KEY_STORAGE);
      setKeyError('');
    } catch {
      setKeyError('The saved key could not be removed from browser storage. Clear this site\'s storage in your browser settings.');
    }
  }

  if (!page) return null;
  return (
    <div className={styles.widget}>
      <section ref={panel} id="page-chat-panel" className={styles.panel} hidden={!open}
        role="dialog" aria-modal="false" aria-labelledby="page-chat-title" aria-describedby="page-chat-privacy">
        <header className={styles.header}>
          <div>
            <h2 id="page-chat-title">Ask this page</h2>
            <p className={styles.pageTitle}>{page.title}</p>
          </div>
          <button type="button" aria-label="Close chat" onClick={() => {
            setOpen(false);
            launcher.current?.focus();
          }}>Close</button>
        </header>
        <p id="page-chat-privacy" className={styles.privacy}>
          Sending shares this page&apos;s text, your question, recent conversation and related course excerpts with Google (Gemini 2.5 Flash).
          {' '}Your key is stored only in this browser&apos;s localStorage and sent only to Google for authentication. Do not enter sensitive data.
        </p>
        {keyError && <p className={styles.error} role="alert">{keyError}</p>}
        {!apiKey ? (
          <form className={styles.setup} onSubmit={saveKey}>
            <p>Use your own key. Google&apos;s API quotas and charges apply. No model request is made until you send a question.</p>
            <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">Get a Gemini API key in Google AI Studio</a>
            <label htmlFor="page-chat-key">Gemini API key</label>
            <input id="page-chat-key" data-chat-autofocus type="password" autoComplete="off" spellCheck={false}
              required value={draftKey} onChange={(event) => setDraftKey(event.target.value)} />
            <button type="submit" className={styles.primary}>Save key</button>
          </form>
        ) : (
          <>
            <div className={styles.keyControls}>
              <span>Key saved in this browser</span>
              <button type="button" onClick={forgetKey}>Forget key</button>
            </div>
            {!index && (indexError ? (
              <div className={styles.indexError}>
                <p className={styles.error} role="alert">{indexError}</p>
                <button type="button" onClick={() => setRetry((value) => value + 1)}>Retry context</button>
              </div>
            ) : <p className={styles.loading} role="status">Loading course context...</p>)}
            <PageChat key={`${page.route}:${sessionVersion}`} page={page} index={index} apiKey={apiKey} baseUrl={baseUrl} open={open} />
          </>
        )}
      </section>
      <button ref={launcher} type="button" className={styles.launcher} aria-controls="page-chat-panel"
        aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        Ask this page
      </button>
    </div>
  );
}
