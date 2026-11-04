import type { Mailbox } from '../../protocol/typescript/src/contract_generated.js';
import { LIMITS } from '../../protocol/typescript/src/limits_generated.js';
import type { MailApi, MessageHeader } from './mail_api.js';
import { folderWithin, randomToken } from './mail_handles.js';

export type ListState =
  | { kind: 'mailboxes'; account: string; pending: Mailbox[] }
  | { kind: 'messages'; folder: string; pending: MessageHeader[]; thunderbird: string | null };

interface Entry {
  state: ListState;
  used: number;
}

/** Open list cursors, bounded in number and idle time, which also abort Thunderbird's lists. */
export function createListRegistry(api: MailApi, now: () => number = Date.now) {
  const entries = new Map<string, Entry>();

  function abort(state: ListState) {
    if (state.kind === 'messages' && state.thunderbird !== null) {
      void api.messages.abortList(state.thunderbird).catch(() => undefined);
    }
  }

  function close(token: string) {
    const entry = entries.get(token);
    if (!entry) return;
    entries.delete(token);
    abort(entry.state);
  }

  function expire() {
    for (const [token, entry] of entries) {
      if (entry.used + LIMITS.list_idle_timeout_ms <= now()) close(token);
    }
  }

  function closeWhere(matches: (state: ListState) => boolean) {
    for (const [token, entry] of entries) {
      if (matches(entry.state)) close(token);
    }
  }

  return {
    open(state: ListState): string {
      expire();
      while (entries.size >= LIMITS.maximum_open_lists) {
        const oldest = entries.keys().next().value;
        if (oldest === undefined) break;
        close(oldest);
      }
      const token = randomToken();
      entries.set(token, { state, used: now() });
      return token;
    },
    take(token: string): ListState | undefined {
      expire();
      const entry = entries.get(token);
      if (!entry) return undefined;
      entries.delete(token);
      entries.set(token, { state: entry.state, used: now() });
      return entry.state;
    },
    close,
    forgetFolder(prefix: string) {
      closeWhere((state) => state.kind === 'messages' && folderWithin(state.folder, prefix));
    },
    forgetAccount(accountId: string) {
      closeWhere((state) =>
        state.kind === 'mailboxes' ? state.account === accountId : state.folder.startsWith(`${accountId}:/`),
      );
    },
    clear() {
      for (const token of [...entries.keys()]) close(token);
    },
    get size() {
      return entries.size;
    },
  };
}

export type ListRegistry = ReturnType<typeof createListRegistry>;
