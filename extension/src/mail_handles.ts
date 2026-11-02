export type HandleKind = 'account' | 'identity' | 'mailbox' | 'message';

export interface HandleTarget {
  kind: HandleKind;
  // The Thunderbird identifier: an account, identity, or folder string, or a message number.
  key: string | number;
  // The folder that holds a mailbox or message, so folder events can invalidate it.
  folder?: string;
}

export const MAXIMUM_HANDLES = 20000;

export function randomToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/gu, '-')
    .replace(/\//gu, '_')
    .replace(/=+$/u, '');
}

function within(folder: string | undefined, prefix: string): boolean {
  return folder !== undefined && (folder === prefix || folder.startsWith(`${prefix}/`));
}

/**
 * Transient handles for Thunderbird objects. A handle names one object until an event,
 * eviction, or reset invalidates it, and it never names another object afterwards.
 */
export function createHandleRegistry(limit = MAXIMUM_HANDLES) {
  const targets = new Map<string, HandleTarget>();
  const tokens = new Map<string, string>();
  const identity = (target: HandleTarget) => `${target.kind}:${String(target.key)}`;

  function remove(token: string) {
    const target = targets.get(token);
    if (!target) return;
    targets.delete(token);
    tokens.delete(identity(target));
  }

  return {
    issue(target: HandleTarget): string {
      const existing = tokens.get(identity(target));
      if (existing !== undefined) {
        targets.delete(existing);
        targets.set(existing, target);
        return existing;
      }
      while (targets.size >= limit) {
        const oldest = targets.keys().next().value;
        if (oldest === undefined) break;
        remove(oldest);
      }
      const token = randomToken();
      targets.set(token, target);
      tokens.set(identity(target), token);
      return token;
    },
    resolve(token: string, kind: HandleKind): HandleTarget | undefined {
      const target = targets.get(token);
      return target?.kind === kind ? target : undefined;
    },
    forgetFolder(prefix: string) {
      for (const [token, target] of targets) {
        if (within(target.folder, prefix)) remove(token);
      }
    },
    forgetAccount(accountId: string) {
      for (const [token, target] of targets) {
        if (target.key === accountId || target.folder?.startsWith(`${accountId}:/`)) remove(token);
      }
    },
    forgetMessage(messageId: number) {
      const token = tokens.get(`message:${String(messageId)}`);
      if (token !== undefined) remove(token);
    },
    clear() {
      targets.clear();
      tokens.clear();
    },
  };
}

export type HandleRegistry = ReturnType<typeof createHandleRegistry>;
export { within as folderWithin };
