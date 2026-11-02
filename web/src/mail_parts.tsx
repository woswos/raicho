import type { Account, Mailbox, MailboxesDocument, MessageSummary } from './api_generated.js';
import type { Failure } from './api.js';
import { failureMessage } from './failures.js';
import { mailboxTree } from './mailbox_tree.js';
import { longDate, shortDate } from './summaries.js';

export type Load<Value> =
  { status: 'loading' } | { status: 'ready'; value: Value } | { status: 'failed'; failure: Failure };

export function Notice({ failure, action, onAction }: { failure: Failure; action?: string; onAction?: () => void }) {
  return (
    <div class="notice" role="alert">
      <p>{failureMessage(failure)}</p>
      {action && onAction && (
        <button type="button" class="secondary" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}

interface MailboxListProps {
  account: Account;
  mailboxes: Load<MailboxesDocument> | undefined;
  selected: string | undefined;
  onSelect: (mailbox: Mailbox) => void;
  onReload: () => void;
}

export function MailboxList({ account, mailboxes, selected, onSelect, onReload }: MailboxListProps) {
  return (
    <section class="account" aria-label={account.name}>
      <h2>{account.name}</h2>
      {account.identities[0] && <p class="muted identity">{account.identities[0].email}</p>}
      {(!mailboxes || mailboxes.status === 'loading') && <p class="muted">Loading mailboxes…</p>}
      {mailboxes?.status === 'failed' && (
        <Notice failure={mailboxes.failure} action="Reload mailboxes" onAction={onReload} />
      )}
      {mailboxes?.status === 'ready' && (
        <ul class="mailboxes">
          {mailboxTree(mailboxes.value.mailboxes).map(({ mailbox, depth }) => (
            <li key={mailbox.id} style={{ paddingInlineStart: `${String(depth * 14)}px` }}>
              <button
                type="button"
                aria-current={mailbox.id === selected ? 'true' : undefined}
                onClick={() => onSelect(mailbox)}
              >
                {mailbox.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      {mailboxes?.status === 'ready' && mailboxes.value.truncated && (
        <p class="muted">Thunderbird has more folders than Raicho lists.</p>
      )}
    </section>
  );
}

const SENDING_ROLES = new Set(['sent', 'drafts', 'outbox', 'templates']);

export function SummaryRow({ summary, mailbox, now }: { summary: MessageSummary; mailbox: Mailbox; now: Date }) {
  const correspondent = SENDING_ROLES.has(mailbox.role ?? '') ? summary.recipients : summary.author;
  return (
    <li class="summary" data-read={summary.read ? 'true' : 'false'}>
      <span class="correspondent">{correspondent || '(no address)'}</span>
      <span class="subject">{summary.subject || '(no subject)'}</span>
      <time dateTime={summary.date} title={longDate(summary.date)}>
        {shortDate(summary.date, now)}
      </time>
      {summary.flagged && (
        <span class="flag" aria-label="Flagged" title="Flagged">
          ★
        </span>
      )}
      {!summary.read && <span class="visually-hidden">Unread</span>}
    </li>
  );
}
