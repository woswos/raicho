import { useEffect, useRef, useState } from 'preact/hooks';

import { apiPath, apiRequest, type Failure } from './api.js';
import type { Account, AccountsDocument, Mailbox, MailboxesDocument, MessagesDocument } from './api_generated.js';
import { failureState } from './failures.js';
import { MailboxList, Notice, SummaryRow, type Load } from './mail_parts.js';
import { appendSummaries } from './summaries.js';

interface Messages {
  mailbox: Mailbox;
  load: Load<MessagesDocument>;
  more?: Load<null>;
}

// Connection is undefined until the first status check answers.
export function MailView({ connected, onSignedOut }: { connected: boolean | undefined; onSignedOut: () => void }) {
  const [accounts, setAccounts] = useState<Load<Account[]>>({ status: 'loading' });
  const [mailboxes, setMailboxes] = useState<Record<string, Load<MailboxesDocument>>>({});
  const [messages, setMessages] = useState<Messages | undefined>();
  const [reconnected, setReconnected] = useState(false);
  // Responses for an earlier selection must not replace the current one.
  const selection = useRef(0);
  const wasConnected = useRef(connected);

  function failed(failure: Failure) {
    if (failureState(failure) === 'unauthenticated') onSignedOut();
    return { status: 'failed', failure } as const;
  }

  async function loadMailboxes(account: Account): Promise<Mailbox | undefined> {
    setMailboxes((current) => ({ ...current, [account.id]: { status: 'loading' } }));
    const result = await apiRequest<MailboxesDocument>(apiPath('/api/mail/accounts', account.id, '/mailboxes'));
    const load: Load<MailboxesDocument> =
      result.ok && result.document
        ? { status: 'ready', value: result.document }
        : failed(result.ok ? { kind: 'invalid' } : result.failure);
    setMailboxes((current) => ({ ...current, [account.id]: load }));
    return load.status === 'ready'
      ? (load.value.mailboxes.find((mailbox) => mailbox.role === 'inbox') ?? load.value.mailboxes[0])
      : undefined;
  }

  async function select(mailbox: Mailbox) {
    const request = ++selection.current;
    setMessages({ mailbox, load: { status: 'loading' } });
    const result = await apiRequest<MessagesDocument>(apiPath('/api/mail/mailboxes', mailbox.id, '/messages'));
    if (request !== selection.current) return;
    setMessages({
      mailbox,
      load:
        result.ok && result.document
          ? { status: 'ready', value: result.document }
          : failed(result.ok ? { kind: 'invalid' } : result.failure),
    });
  }

  async function loadMore(current: Messages, document: MessagesDocument) {
    if (!document.cursor) return;
    const request = selection.current;
    setMessages({ ...current, more: { status: 'loading' } });
    const result = await apiRequest<MessagesDocument>(apiPath('/api/mail/cursors', document.cursor));
    if (request !== selection.current) return;
    if (!result.ok || !result.document) {
      setMessages({ ...current, more: failed(result.ok ? { kind: 'invalid' } : result.failure) });
      return;
    }
    const next: MessagesDocument = {
      messages: appendSummaries(document.messages, result.document.messages),
      ...(result.document.cursor ? { cursor: result.document.cursor } : {}),
    };
    setMessages({ mailbox: current.mailbox, load: { status: 'ready', value: next } });
  }

  async function loadAccounts() {
    const request = ++selection.current;
    setAccounts({ status: 'loading' });
    setMailboxes({});
    setMessages(undefined);
    const result = await apiRequest<AccountsDocument>('/api/mail/accounts');
    if (!result.ok || !result.document) {
      setAccounts(failed(result.ok ? { kind: 'invalid' } : result.failure));
      return;
    }
    const loaded = result.document.accounts;
    setAccounts({ status: 'ready', value: loaded });
    const first = await Promise.all(loaded.map(loadMailboxes));
    const inbox = first.find((mailbox) => mailbox !== undefined);
    if (inbox && request === selection.current) void select(inbox);
  }

  useEffect(() => {
    void loadAccounts();
  }, []);

  // A reconnect issues new handles, so the views reload instead of reusing stale ones.
  useEffect(() => {
    if (connected === true && wasConnected.current === false) {
      setReconnected(true);
      void loadAccounts();
    }
    wasConnected.current = connected;
  }, [connected]);

  const page = messages?.load.status === 'ready' ? messages.load.value : undefined;
  const pageFailure = messages?.load.status === 'failed' ? messages.load.failure : undefined;
  const stale = pageFailure !== undefined && failureState(pageFailure) === 'stale';
  return (
    <main id="main" class="mail">
      {connected === false && (
        <p class="banner" role="status">
          Thunderbird is not connected. Mail shown here may be out of date, and new mail is unavailable.
        </p>
      )}
      {connected && reconnected && (
        <p class="banner" role="status">
          Thunderbird reconnected, so the mailboxes were reloaded.
        </p>
      )}
      <nav class="sidebar" aria-label="Accounts and mailboxes">
        {accounts.status === 'loading' && <p class="muted">Loading accounts…</p>}
        {accounts.status === 'failed' && (
          <Notice failure={accounts.failure} action="Reload accounts" onAction={() => void loadAccounts()} />
        )}
        {accounts.status === 'ready' && accounts.value.length === 0 && (
          <p class="muted">Thunderbird has no accounts. Add one in the Thunderbird desktop.</p>
        )}
        {accounts.status === 'ready' &&
          accounts.value.map((account) => (
            <MailboxList
              key={account.id}
              account={account}
              mailboxes={mailboxes[account.id]}
              selected={messages?.mailbox.id}
              onSelect={(mailbox) => {
                setReconnected(false);
                void select(mailbox);
              }}
              onReload={() => void loadAccounts()}
            />
          ))}
      </nav>
      <section class="messages" aria-live="polite" aria-label={messages ? messages.mailbox.name : 'Messages'}>
        {!messages && accounts.status === 'ready' && <p class="muted">Choose a mailbox.</p>}
        {messages && <h1>{messages.mailbox.name}</h1>}
        {messages?.load.status === 'loading' && <p class="muted">Loading messages…</p>}
        {messages && pageFailure && (
          <Notice
            failure={pageFailure}
            action={stale ? 'Reload mailboxes' : 'Try again'}
            onAction={() => void (stale ? loadAccounts() : select(messages.mailbox))}
          />
        )}
        {page && page.messages.length === 0 && <p class="muted">No messages in this mailbox.</p>}
        {messages && page && page.messages.length > 0 && (
          <ul class="summaries" data-stale={connected === false ? 'true' : 'false'}>
            {page.messages.map((summary) => (
              <SummaryRow key={summary.id} summary={summary} mailbox={messages.mailbox} now={new Date()} />
            ))}
          </ul>
        )}
        {messages?.more?.status === 'failed' && (
          <Notice
            failure={messages.more.failure}
            action="Reload mailbox"
            onAction={() => void select(messages.mailbox)}
          />
        )}
        {page?.cursor && messages && (
          <button
            type="button"
            class="secondary load-more"
            disabled={messages.more?.status === 'loading' || connected === false}
            onClick={() => void loadMore(messages, page)}
          >
            {messages.more?.status === 'loading' ? 'Loading…' : 'Load older messages'}
          </button>
        )}
      </section>
    </main>
  );
}
