import type {
  Account,
  MailError,
  Mailbox,
  MessageSummary,
  Operation,
  Outcome,
} from '../../protocol/typescript/src/contract_generated.js';
import { LIMITS } from '../../protocol/typescript/src/limits_generated.js';
import type { MailApi, MessageHeader, MessageList } from './mail_api.js';
import { createHandleRegistry } from './mail_handles.js';
import { createListRegistry, type ListState } from './mail_lists.js';
import { mailboxRole, mailDate, mailText } from './mail_text.js';

// The envelope, request identifier, and MAC fit in the rest of the frame limit.
export const RESULT_BUDGET_BYTES = LIMITS.maximum_control_bytes - 4096;
export const PAGE_MESSAGES = 50;
export const PAGE_MAILBOXES = 200;
const REMEMBERED_REMOVALS = 20000;
const encoder = new TextEncoder();

function failure(code: MailError): Outcome {
  return { kind: 'error', code };
}

function size(value: unknown): number {
  return encoder.encode(JSON.stringify(value)).byteLength + 1;
}

/** Answers read-only mail operations from Thunderbird, keeping its objects behind transient handles. */
export function createMailAdapter(api: MailApi, now: () => number = Date.now) {
  const handles = createHandleRegistry();
  const lists = createListRegistry(api, now);
  // Messages that moved or were deleted after a list captured them must not reappear.
  const removed = new Set<number>();

  function forgetFolder(folder: { id: string }) {
    handles.forgetFolder(folder.id);
    lists.forgetFolder(folder.id);
  }

  async function forgetMessages(list: MessageList) {
    let page: MessageList | undefined = list;
    while (page) {
      for (const message of page.messages) {
        removed.add(message.id);
        handles.forgetMessage(message.id);
      }
      while (removed.size > REMEMBERED_REMOVALS) {
        const oldest = removed.values().next().value;
        if (oldest === undefined) break;
        removed.delete(oldest);
      }
      page = page.id ? await api.messages.continueList(page.id) : undefined;
    }
  }

  api.folders.onRenamed.addListener(forgetFolder);
  api.folders.onMoved.addListener(forgetFolder);
  api.folders.onDeleted.addListener(forgetFolder);
  api.accounts.onDeleted.addListener((accountId) => {
    handles.forgetAccount(accountId);
    lists.forgetAccount(accountId);
  });
  api.messages.onMoved.addListener((original) => void forgetMessages(original).catch(() => undefined));
  api.messages.onDeleted.addListener((messages) => void forgetMessages(messages).catch(() => undefined));

  async function accounts(): Promise<Outcome> {
    const result: Account[] = (await api.accounts.list(false)).map((account) => ({
      id: handles.issue({ kind: 'account', key: account.id }),
      name: mailText(account.name, 128) || 'Account',
      identities: account.identities
        .filter((identity) => mailText(identity.email, 254) !== '')
        .map((identity) => ({
          id: handles.issue({ kind: 'identity', key: identity.id, folder: `${account.id}:/` }),
          name: mailText(identity.name, 128),
          email: mailText(identity.email, 254),
        })),
    }));
    const outcome: Outcome = { kind: 'accounts', accounts: result };
    return size(outcome) > RESULT_BUDGET_BYTES ? failure('too_large') : outcome;
  }

  async function mailboxes(accountHandle: string): Promise<Outcome> {
    const account = handles.resolve(accountHandle, 'account');
    if (!account) return failure('stale_handle');
    const accountId = String(account.key);
    const folders = await api.folders.query({
      accountId,
      isRoot: false,
      isUnified: false,
      isTag: false,
      isVirtual: false,
    });
    folders.sort((left, right) => (left.path < right.path ? -1 : left.path > right.path ? 1 : 0));
    const byPath = new Map(folders.map((folder) => [folder.path, folder.id]));
    const pending: Mailbox[] = folders.map((folder) => {
      const parentPath = folder.path.slice(0, folder.path.lastIndexOf('/'));
      const parent = byPath.get(parentPath);
      const role = mailboxRole(folder.specialUse);
      return {
        id: handles.issue({ kind: 'mailbox', key: folder.id, folder: folder.id }),
        name: mailText(folder.name, 255) || mailText(folder.path, 255) || 'Folder',
        ...(parent === undefined ? {} : { parent: handles.issue({ kind: 'mailbox', key: parent, folder: parent }) }),
        ...(role === undefined ? {} : { role }),
      };
    });
    return mailboxPage({ kind: 'mailboxes', account: accountId, pending });
  }

  function mailboxPage(state: Extract<ListState, { kind: 'mailboxes' }>, cursor?: string): Outcome {
    const page: Mailbox[] = [];
    let used = 0;
    while (state.pending.length > 0 && page.length < PAGE_MAILBOXES) {
      const next = state.pending[0];
      if (next === undefined || (page.length > 0 && used + size(next) > RESULT_BUDGET_BYTES)) break;
      used += size(next);
      page.push(next);
      state.pending.shift();
    }
    return { kind: 'mailboxes', mailboxes: page, ...continuation(state, cursor) };
  }

  function continuation(state: ListState, cursor: string | undefined): { cursor?: string } {
    const more = state.pending.length > 0 || (state.kind === 'messages' && state.thunderbird !== null);
    if (!more) {
      if (cursor !== undefined) lists.close(cursor);
      return {};
    }
    return { cursor: cursor ?? lists.open(state) };
  }

  function summary(folder: string, header: MessageHeader): MessageSummary {
    return {
      id: handles.issue({ kind: 'message', key: header.id, folder }),
      subject: mailText(header.subject, 300),
      author: mailText(header.author, 300),
      recipients: mailText(header.recipients.join(', '), 300),
      date: mailDate(header.date),
      read: header.read === true,
      flagged: header.flagged === true,
    };
  }

  async function messagePage(state: Extract<ListState, { kind: 'messages' }>, cursor?: string): Promise<Outcome> {
    const page: MessageSummary[] = [];
    let used = 0;
    while (page.length < PAGE_MESSAGES) {
      if (state.pending.length === 0 && state.thunderbird !== null) {
        const next = await api.messages.continueList(state.thunderbird);
        state.thunderbird = next.id;
        state.pending.push(...next.messages);
      }
      const header = state.pending[0];
      if (header === undefined) break;
      if (removed.has(header.id)) {
        state.pending.shift();
        continue;
      }
      const item = summary(state.folder, header);
      if (page.length > 0 && used + size(item) > RESULT_BUDGET_BYTES) break;
      used += size(item);
      page.push(item);
      state.pending.shift();
    }
    return { kind: 'messages', messages: page, ...continuation(state, cursor) };
  }

  async function messages(mailboxHandle: string): Promise<Outcome> {
    const mailbox = handles.resolve(mailboxHandle, 'mailbox');
    if (!mailbox) return failure('stale_handle');
    const folder = String(mailbox.key);
    let list: MessageList;
    try {
      list = await api.messages.list(folder, { sortType: 'date', sortOrder: 'descending' });
    } catch {
      return failure('stale_handle');
    }
    return messagePage({ kind: 'messages', folder, pending: [...list.messages], thunderbird: list.id });
  }

  async function next(cursor: string): Promise<Outcome> {
    const state = lists.take(cursor);
    if (!state) return failure('stale_cursor');
    return state.kind === 'mailboxes' ? mailboxPage(state, cursor) : messagePage(state, cursor);
  }

  return {
    async execute(operation: Operation): Promise<Outcome> {
      try {
        switch (operation.name) {
          case 'list_accounts':
            return await accounts();
          case 'list_mailboxes':
            return await mailboxes(operation.account);
          case 'list_messages':
            return await messages(operation.mailbox);
          case 'continue_list':
            return await next(operation.cursor);
          case 'close_list':
            lists.close(operation.cursor);
            return { kind: 'closed' };
        }
      } catch {
        return failure('failed');
      }
    },
    // Handles and cursors belong to one connector session.
    reset() {
      handles.clear();
      lists.clear();
    },
  };
}

export type MailAdapter = ReturnType<typeof createMailAdapter>;
