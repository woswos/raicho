import type { Mailbox } from './api_generated.js';

export interface TreeEntry {
  mailbox: Mailbox;
  depth: number;
}

const ROLE_ORDER = ['inbox', 'drafts', 'sent', 'archive', 'junk', 'trash', 'templates', 'outbox'];

function rank(mailbox: Mailbox): number {
  const position = mailbox.role === undefined ? -1 : ROLE_ORDER.indexOf(mailbox.role);
  return position === -1 ? ROLE_ORDER.length : position;
}

/** Orders mailboxes with special folders first and children below their parents. */
export function mailboxTree(mailboxes: Mailbox[]): TreeEntry[] {
  const known = new Set(mailboxes.map((mailbox) => mailbox.id));
  const children = new Map<string | undefined, Mailbox[]>();
  for (const mailbox of mailboxes) {
    const parent = mailbox.parent !== undefined && known.has(mailbox.parent) ? mailbox.parent : undefined;
    children.set(parent, [...(children.get(parent) ?? []), mailbox]);
  }
  const ordered: TreeEntry[] = [];
  const visited = new Set<string>();
  const visit = (parent: string | undefined, depth: number) => {
    const siblings = [...(children.get(parent) ?? [])].sort(
      (left, right) => rank(left) - rank(right) || left.name.localeCompare(right.name),
    );
    for (const mailbox of siblings) {
      if (visited.has(mailbox.id)) continue;
      visited.add(mailbox.id);
      ordered.push({ mailbox, depth });
      visit(mailbox.id, depth + 1);
    }
  };
  visit(undefined, 0);
  // A cycle of parents has no root, so its members follow at the top level.
  for (const mailbox of mailboxes) {
    if (!visited.has(mailbox.id)) {
      visited.add(mailbox.id);
      ordered.push({ mailbox, depth: 0 });
      visit(mailbox.id, 1);
    }
  }
  return ordered;
}
